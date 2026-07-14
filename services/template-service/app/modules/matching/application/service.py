from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.config import Settings
from app.domain.enums import TemplateMatchingStatus, TemplateStatus, TemplateVersionStatus
from app.errors import BusinessRuleError, NotFoundError
from app.infrastructure.database.models import (
    DocumentProfile,
    Template,
    TemplateMatchingCandidate,
    TemplateMatchingRun,
    TemplateVersion,
)
from app.infrastructure.document_service import DocumentServicePort
from app.infrastructure.events import DomainEvent, EventPublisher
from app.infrastructure.identity_gateway import Principal
from app.modules.matching.domain.document_profile import build_document_profile
from app.modules.matching.domain.score import ScoreResult, score_signals
from app.modules.matching.public.commands import ConfirmTemplateMatchCommand, MatchDocumentCommand
from app.modules.matching.public.events import (
    TEMPLATE_AMBIGUOUS,
    TEMPLATE_MANUALLY_CONFIRMED,
    TEMPLATE_MATCHED,
    TEMPLATE_NOT_FOUND,
)


class TemplateMatchingService:
    def __init__(
        self,
        *,
        session: Session,
        settings: Settings,
        publisher: EventPublisher,
        principal: Principal,
        document_service: DocumentServicePort,
        correlation_id: str,
    ) -> None:
        self.session = session
        self.settings = settings
        self.publisher = publisher
        self.principal = principal
        self.document_service = document_service
        self.correlation_id = correlation_id

    async def match_document(self, command: MatchDocumentCommand) -> TemplateMatchingRun:
        document = await self.document_service.get_document(
            command.document_id,
            authorization=self.principal.authorization,
            correlation_id=self.correlation_id,
        )
        if document is None:
            raise NotFoundError("Document")
        preview = await self.document_service.get_preview(
            command.document_id,
            authorization=self.principal.authorization,
            correlation_id=self.correlation_id,
        )
        if preview is None:
            raise BusinessRuleError("DOCUMENT_PREVIEW_NOT_FOUND", "Document preview is required before template matching", status_code=404)

        profile_json = build_document_profile(
            document,
            preview,
            text_limit=self.settings.template_profile_text_sample_limit,
            keyword_limit=self.settings.template_profile_max_keywords,
        )
        profile = DocumentProfile(
            document_id=command.document_id,
            file_format=profile_json["file_format"],
            profile_json=profile_json,
            profile_version="v1",
        )
        self.session.add(profile)
        self.session.flush()

        max_candidates = min(
            command.max_candidates or self.settings.template_match_max_candidates,
            self.settings.template_match_max_candidates,
        )
        templates = self._find_candidate_templates(
            file_format=profile_json["file_format"],
            category_hint=command.category_hint,
        )
        scored = [
            (template, self._active_version(template), score_signals(list(template.identification_signals), profile_json))
            for template in templates
        ]
        scored.sort(key=lambda item: item[2].score, reverse=True)
        limited = scored[:max_candidates]

        status, reason, winner, confidence = self._decide(limited)
        run = TemplateMatchingRun(
            document_profile_id=profile.id,
            document_id=command.document_id,
            status=status.value,
            matched_template_id=winner[0].id if winner else None,
            matched_template_version_id=winner[1].id if winner and winner[1] else None,
            matched_category_id=winner[0].category_id if winner else None,
            confidence=confidence,
            decision_reason=reason,
            manual_override=False,
            created_by=self.principal.id,
        )
        self.session.add(run)
        self.session.flush()
        self._persist_candidates(run, limited)
        self.session.commit()
        self.session.refresh(run)
        self._load_run(run)
        self._publish_decision_event(run, profile_json)
        return run

    def get_latest_for_document(self, document_id: str) -> TemplateMatchingRun:
        run = self.session.scalar(
            select(TemplateMatchingRun)
            .where(TemplateMatchingRun.document_id == document_id)
            .options(
                selectinload(TemplateMatchingRun.candidates).selectinload(TemplateMatchingCandidate.template),
                selectinload(TemplateMatchingRun.candidates).selectinload(TemplateMatchingCandidate.category),
            )
            .order_by(TemplateMatchingRun.created_at.desc())
        )
        if run is None:
            raise NotFoundError("Template matching run")
        return run

    def list_runs_for_document(self, document_id: str) -> list[TemplateMatchingRun]:
        return list(
            self.session.scalars(
                select(TemplateMatchingRun)
                .where(TemplateMatchingRun.document_id == document_id)
                .options(selectinload(TemplateMatchingRun.candidates))
                .order_by(TemplateMatchingRun.created_at.desc())
            ).all()
        )

    def get_run(self, matching_run_id: str) -> TemplateMatchingRun:
        run = self.session.scalar(
            select(TemplateMatchingRun)
            .where(TemplateMatchingRun.id == matching_run_id)
            .options(
                selectinload(TemplateMatchingRun.candidates).selectinload(TemplateMatchingCandidate.template),
                selectinload(TemplateMatchingRun.candidates).selectinload(TemplateMatchingCandidate.category),
            )
        )
        if run is None:
            raise NotFoundError("Template matching run")
        return run

    def confirm_match(self, command: ConfirmTemplateMatchCommand) -> TemplateMatchingRun:
        template = self.session.scalar(
            select(Template)
            .where(Template.id == command.template_id)
            .options(selectinload(Template.category), selectinload(Template.versions))
        )
        if template is None:
            raise NotFoundError("Template")
        version = next((item for item in template.versions if item.id == command.template_version_id), None)
        if version is None:
            raise NotFoundError("Template version")
        if template.status != TemplateStatus.ACTIVE.value or version.status != TemplateVersionStatus.PUBLISHED.value:
            raise BusinessRuleError("TEMPLATE_VERSION_NOT_PUBLISHED", "Manual confirmation requires an active template and published version")

        latest_profile = self.session.scalar(
            select(DocumentProfile)
            .where(DocumentProfile.document_id == command.document_id)
            .order_by(DocumentProfile.created_at.desc())
        )
        run = TemplateMatchingRun(
            document_profile_id=latest_profile.id if latest_profile else None,
            document_id=command.document_id,
            status=TemplateMatchingStatus.MATCHED.value,
            matched_template_id=template.id,
            matched_template_version_id=version.id,
            matched_category_id=template.category_id,
            confidence=1.0,
            decision_reason=command.reason,
            manual_override=True,
            created_by=self.principal.id,
        )
        self.session.add(run)
        self.session.flush()
        candidate = TemplateMatchingCandidate(
            matching_run_id=run.id,
            template_id=template.id,
            template_version_id=version.id,
            category_id=template.category_id,
            score=1.0,
            rank_position=1,
            matched_signals=["manual_confirmation"],
            missing_required_signals=[],
            negative_matches=[],
            score_details={"reason": command.reason},
        )
        self.session.add(candidate)
        self.session.commit()
        self.session.refresh(run)
        self._load_run(run)
        self._publish(
            TEMPLATE_MANUALLY_CONFIRMED,
            {
                "document_id": command.document_id,
                "template_id": template.id,
                "template_version_id": version.id,
                "category_id": template.category_id,
                "confidence": 1.0,
                "matching_run_id": run.id,
                "reason": command.reason,
            },
        )
        return run

    def _find_candidate_templates(self, *, file_format: str, category_hint: str | None) -> list[Template]:
        statement = (
            select(Template)
            .where(
                Template.status == TemplateStatus.ACTIVE.value,
                Template.file_format == file_format,
                Template.active_version_id.is_not(None),
            )
            .options(
                selectinload(Template.category),
                selectinload(Template.identification_signals),
                selectinload(Template.versions),
            )
        )
        if category_hint:
            statement = statement.where(Template.category_id == category_hint)
        templates = list(self.session.scalars(statement).all())
        return [template for template in templates if self._active_version(template) is not None]

    def _active_version(self, template: Template) -> TemplateVersion | None:
        return next(
            (
                version
                for version in template.versions
                if version.id == template.active_version_id
                and version.status == TemplateVersionStatus.PUBLISHED.value
            ),
            None,
        )

    def _decide(
        self,
        candidates: list[tuple[Template, TemplateVersion | None, ScoreResult]],
    ) -> tuple[TemplateMatchingStatus, str, tuple[Template, TemplateVersion | None, ScoreResult] | None, float]:
        if not candidates:
            return TemplateMatchingStatus.NOT_FOUND, "No active published template candidates for document format", None, 0.0
        top = candidates[0]
        top_score = top[2].score
        if top_score < self.settings.template_match_min_confidence:
            return TemplateMatchingStatus.NOT_FOUND, "No candidate above minimum confidence", None, top_score
        if len(candidates) > 1 and top_score - candidates[1][2].score <= self.settings.template_match_ambiguity_delta:
            return TemplateMatchingStatus.AMBIGUOUS, "Top candidates are too close", None, top_score
        if top_score >= self.settings.template_match_auto_accept_confidence:
            return TemplateMatchingStatus.MATCHED, "Best candidate above auto accept threshold", top, top_score
        return TemplateMatchingStatus.AMBIGUOUS, "Best candidate requires manual confirmation", None, top_score

    def _persist_candidates(
        self,
        run: TemplateMatchingRun,
        candidates: list[tuple[Template, TemplateVersion | None, ScoreResult]],
    ) -> None:
        for index, (template, version, score) in enumerate(candidates, start=1):
            self.session.add(
                TemplateMatchingCandidate(
                    matching_run_id=run.id,
                    template_id=template.id,
                    template_version_id=version.id if version else None,
                    category_id=template.category_id,
                    score=score.score,
                    rank_position=index,
                    matched_signals=score.matched_signals,
                    missing_required_signals=score.missing_required_signals,
                    negative_matches=score.negative_matches,
                    score_details=score.details,
                )
            )

    def _load_run(self, run: TemplateMatchingRun) -> None:
        run.candidates.sort(key=lambda item: item.rank_position)

    def _publish_decision_event(self, run: TemplateMatchingRun, profile: dict[str, Any]) -> None:
        payload: dict[str, Any] = {
            "document_id": run.document_id,
            "client_id": profile.get("client_id"),
            "competence_id": profile.get("competence_id"),
            "matching_run_id": run.id,
        }
        if run.status == TemplateMatchingStatus.MATCHED.value:
            payload.update(
                {
                    "template_id": run.matched_template_id,
                    "template_version_id": run.matched_template_version_id,
                    "category_id": run.matched_category_id,
                    "confidence": run.confidence,
                }
            )
            self._publish(TEMPLATE_MATCHED, payload)
        elif run.status == TemplateMatchingStatus.AMBIGUOUS.value:
            payload.update({"candidate_count": len(run.candidates), "best_candidate_score": run.confidence})
            self._publish(TEMPLATE_AMBIGUOUS, payload)
        elif run.status == TemplateMatchingStatus.NOT_FOUND.value:
            payload.update({"best_candidate_score": run.confidence})
            self._publish(TEMPLATE_NOT_FOUND, payload)

    def _publish(self, event_type: str, payload: dict[str, Any]) -> None:
        self.publisher.publish(
            DomainEvent(
                event_type=event_type,
                payload=payload,
                correlation_id=self.correlation_id,
            )
        )
