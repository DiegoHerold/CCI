import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.application.schemas import (
    AnnotationCreate,
    AnnotationUpdate,
    ExtractionRuleCreate,
    ExtractionRuleUpdate,
    FieldCreate,
    FieldUpdate,
    IdentificationSignalCreate,
    IdentificationSignalUpdate,
    TemplateCategoryCreate,
    TemplateCreate,
    TemplateUpdate,
)
from app.config import Settings
from app.domain.enums import TemplateStatus, TemplateVersionStatus
from app.errors import BusinessRuleError, ConflictError, NotFoundError
from app.infrastructure.database.models import (
    ExtractionRule,
    IdentificationSignal,
    Template,
    TemplateAnnotation,
    TemplateCategory,
    TemplateField,
    TemplateVersion,
)
from app.infrastructure.events import DomainEvent, EventPublisher
from app.infrastructure.identity_gateway import Principal


class TemplateService:
    def __init__(
        self,
        session: Session,
        settings: Settings,
        publisher: EventPublisher,
        principal: Principal,
        correlation_id: str,
    ) -> None:
        self.session = session
        self.settings = settings
        self.publisher = publisher
        self.principal = principal
        self.correlation_id = correlation_id

    def create_category(self, payload: TemplateCategoryCreate) -> TemplateCategory:
        category = TemplateCategory(
            name=payload.name,
            slug=payload.slug,
            description=payload.description,
            status=TemplateStatus.ACTIVE.value,
        )
        self.session.add(category)
        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise ConflictError("TEMPLATE_CATEGORY_SLUG_ALREADY_EXISTS", "Category slug already exists") from exc
        self.session.refresh(category)
        self._publish("TemplateCategoryCreated", {"category_id": category.id, "slug": category.slug})
        return category

    def list_categories(self) -> list[TemplateCategory]:
        return list(self.session.scalars(select(TemplateCategory).order_by(TemplateCategory.name)).all())

    def get_category(self, category_id: str) -> TemplateCategory:
        category = self.session.get(TemplateCategory, category_id)
        if not category:
            raise NotFoundError("Template category")
        return category

    def create_template(self, payload: TemplateCreate) -> Template:
        self.get_category(payload.category_id)
        template = Template(
            name=payload.name,
            description=payload.description,
            category_id=payload.category_id,
            file_format=payload.file_format.value,
            structure_type=payload.structure_type.value,
            status=TemplateStatus.DRAFT.value,
            created_by=self.principal.id,
        )
        self.session.add(template)
        self.session.commit()
        self.session.refresh(template)
        self._publish(
            "TemplateCreated",
            {
                "template_id": template.id,
                "category_id": template.category_id,
                "file_format": template.file_format,
                "structure_type": template.structure_type,
            },
        )
        return template

    def list_templates(
        self,
        *,
        category_id: str | None = None,
        file_format: str | None = None,
        status: str | None = None,
        structure_type: str | None = None,
        search: str | None = None,
    ) -> tuple[list[Template], int]:
        stmt = select(Template).options(selectinload(Template.category)).order_by(Template.created_at.desc())
        count_stmt = select(func.count()).select_from(Template)
        filters = []
        if category_id:
            filters.append(Template.category_id == category_id)
        if file_format:
            filters.append(Template.file_format == file_format)
        if status:
            filters.append(Template.status == status)
        if structure_type:
            filters.append(Template.structure_type == structure_type)
        if search:
            like = f"%{search}%"
            filters.append(Template.name.ilike(like))
        for item in filters:
            stmt = stmt.where(item)
            count_stmt = count_stmt.where(item)
        return list(self.session.scalars(stmt).all()), int(self.session.scalar(count_stmt) or 0)

    def get_template(self, template_id: str, *, detail: bool = True) -> Template:
        stmt = select(Template).where(Template.id == template_id)
        if detail:
            stmt = stmt.options(
                selectinload(Template.category),
                selectinload(Template.fields),
                selectinload(Template.identification_signals),
                selectinload(Template.annotations),
                selectinload(Template.extraction_rules),
                selectinload(Template.versions),
            )
        template = self.session.scalar(stmt)
        if not template:
            raise NotFoundError("Template")
        return template

    def update_template(self, template_id: str, payload: TemplateUpdate) -> Template:
        template = self.get_template(template_id, detail=False)
        if payload.category_id is not None:
            self.get_category(payload.category_id)
            template.category_id = payload.category_id
        if payload.name is not None:
            template.name = payload.name
        if "description" in payload.model_fields_set:
            template.description = payload.description
        if payload.file_format is not None:
            template.file_format = payload.file_format.value
        if payload.structure_type is not None:
            template.structure_type = payload.structure_type.value
        self.session.commit()
        self.session.refresh(template)
        self._publish("TemplateUpdated", {"template_id": template.id})
        return template

    def update_template_status(self, template_id: str, status: TemplateStatus) -> Template:
        template = self.get_template(template_id, detail=False)
        template.status = status.value
        self.session.commit()
        self.session.refresh(template)
        self._publish(
            "TemplateArchived" if status == TemplateStatus.ARCHIVED else "TemplateUpdated",
            {"template_id": template.id, "status": template.status},
        )
        return template

    def create_field(self, template_id: str, payload: FieldCreate) -> TemplateField:
        self.get_template(template_id, detail=False)
        if payload.parent_field_id:
            self._get_field(template_id, payload.parent_field_id)
        field = TemplateField(
            template_id=template_id,
            parent_field_id=payload.parent_field_id,
            field_path=payload.field_path,
            label=payload.label,
            description=payload.description,
            field_type=payload.field_type.value,
            is_required=payload.is_required,
            is_repeated=payload.is_repeated,
            is_object=payload.is_object or payload.field_type.value == "object",
            is_array=payload.is_array or payload.field_type.value == "array" or "[]" in payload.field_path,
            order_index=payload.order_index,
        )
        self.session.add(field)
        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise ConflictError("TEMPLATE_FIELD_PATH_ALREADY_EXISTS", "Field path already exists for template") from exc
        self.session.refresh(field)
        self._publish("TemplateFieldCreated", {"template_id": template_id, "field_id": field.id, "field_path": field.field_path})
        return field

    def list_fields(self, template_id: str) -> list[TemplateField]:
        self.get_template(template_id, detail=False)
        return list(
            self.session.scalars(
                select(TemplateField)
                .where(TemplateField.template_id == template_id)
                .order_by(TemplateField.order_index, TemplateField.field_path)
            ).all()
        )

    def update_field(self, template_id: str, field_id: str, payload: FieldUpdate) -> TemplateField:
        field = self._get_field(template_id, field_id)
        if payload.parent_field_id:
            parent = self._get_field(template_id, payload.parent_field_id)
            if parent.id == field.id:
                raise BusinessRuleError("INVALID_PARENT_FIELD", "Field cannot be its own parent")
            field.parent_field_id = parent.id
        if payload.label is not None:
            field.label = payload.label
        if "description" in payload.model_fields_set:
            field.description = payload.description
        for attr in ("is_required", "is_repeated", "is_object", "is_array", "order_index"):
            value = getattr(payload, attr)
            if value is not None:
                setattr(field, attr, value)
        if payload.field_type is not None:
            field.field_type = payload.field_type.value
        self.session.commit()
        self.session.refresh(field)
        return field

    def delete_field(self, template_id: str, field_id: str) -> None:
        field = self._get_field(template_id, field_id)
        field.status = "inactive"
        self.session.commit()

    def create_signal(self, template_id: str, payload: IdentificationSignalCreate) -> IdentificationSignal:
        self.get_template(template_id, detail=False)
        signal = IdentificationSignal(
            template_id=template_id,
            signal_type=payload.signal_type.value,
            value=payload.value,
            weight=payload.weight,
            required=payload.required,
            negative=payload.negative,
        )
        self.session.add(signal)
        self.session.commit()
        self.session.refresh(signal)
        return signal

    def list_signals(self, template_id: str) -> list[IdentificationSignal]:
        self.get_template(template_id, detail=False)
        return list(
            self.session.scalars(
                select(IdentificationSignal)
                .where(IdentificationSignal.template_id == template_id)
                .order_by(IdentificationSignal.created_at)
            ).all()
        )

    def update_signal(self, template_id: str, signal_id: str, payload: IdentificationSignalUpdate) -> IdentificationSignal:
        signal = self._get_signal(template_id, signal_id)
        if payload.signal_type is not None:
            signal.signal_type = payload.signal_type.value
        if payload.value is not None:
            signal.value = payload.value
        for attr in ("weight", "required", "negative"):
            value = getattr(payload, attr)
            if value is not None:
                setattr(signal, attr, value)
        self.session.commit()
        self.session.refresh(signal)
        return signal

    def delete_signal(self, template_id: str, signal_id: str) -> None:
        signal = self._get_signal(template_id, signal_id)
        self.session.delete(signal)
        self.session.commit()

    def create_annotation(self, template_id: str, payload: AnnotationCreate) -> TemplateAnnotation:
        self.get_template(template_id, detail=False)
        self._get_field(template_id, payload.field_id)
        if payload.template_version_id:
            self._get_version(template_id, payload.template_version_id)
        self._validate_json_size(payload.selection_payload, self.settings.max_selection_payload_bytes, "SELECTION_PAYLOAD_TOO_LARGE")
        annotation = TemplateAnnotation(
            template_id=template_id,
            template_version_id=payload.template_version_id,
            field_id=payload.field_id,
            document_id=payload.document_id,
            annotation_type=payload.annotation_type.value,
            source_preview_id=payload.source_preview_id,
            selected_text=payload.selected_text,
            selection_payload=payload.selection_payload,
            created_by=self.principal.id,
        )
        self.session.add(annotation)
        self.session.commit()
        self.session.refresh(annotation)
        self._publish("TemplateAnnotationCreated", {"template_id": template_id, "annotation_id": annotation.id, "field_id": annotation.field_id})
        return annotation

    def list_annotations(
        self,
        template_id: str,
        *,
        field_id: str | None = None,
        document_id: str | None = None,
        annotation_type: str | None = None,
    ) -> list[TemplateAnnotation]:
        self.get_template(template_id, detail=False)
        stmt = select(TemplateAnnotation).where(TemplateAnnotation.template_id == template_id)
        if field_id:
            stmt = stmt.where(TemplateAnnotation.field_id == field_id)
        if document_id:
            stmt = stmt.where(TemplateAnnotation.document_id == document_id)
        if annotation_type:
            stmt = stmt.where(TemplateAnnotation.annotation_type == annotation_type)
        return list(self.session.scalars(stmt.order_by(TemplateAnnotation.created_at)).all())

    def get_annotation(self, template_id: str, annotation_id: str) -> TemplateAnnotation:
        annotation = self.session.get(TemplateAnnotation, annotation_id)
        if not annotation or annotation.template_id != template_id:
            raise NotFoundError("Template annotation")
        return annotation

    def delete_annotation(self, template_id: str, annotation_id: str) -> None:
        annotation = self.get_annotation(template_id, annotation_id)
        self.session.delete(annotation)
        self.session.commit()

    def create_rule(self, template_id: str, payload: ExtractionRuleCreate) -> ExtractionRule:
        self.get_template(template_id, detail=False)
        self._get_field(template_id, payload.field_id)
        if payload.template_version_id:
            self._get_version(template_id, payload.template_version_id)
        if payload.created_from_annotation_id:
            self.get_annotation(template_id, payload.created_from_annotation_id)
        self._validate_json_size(payload.config, self.settings.max_rule_config_bytes, "RULE_CONFIG_TOO_LARGE")
        rule = ExtractionRule(
            template_id=template_id,
            template_version_id=payload.template_version_id,
            field_id=payload.field_id,
            rule_type=payload.rule_type,
            strategy=payload.strategy.value,
            config=payload.config,
            confidence_hint=payload.confidence_hint,
            created_from_annotation_id=payload.created_from_annotation_id,
        )
        self.session.add(rule)
        self.session.commit()
        self.session.refresh(rule)
        self._publish("TemplateExtractionRuleCreated", {"template_id": template_id, "rule_id": rule.id, "field_id": rule.field_id, "strategy": rule.strategy})
        return rule

    def list_rules(self, template_id: str) -> list[ExtractionRule]:
        self.get_template(template_id, detail=False)
        return list(
            self.session.scalars(
                select(ExtractionRule)
                .where(ExtractionRule.template_id == template_id)
                .order_by(ExtractionRule.created_at)
            ).all()
        )

    def update_rule(self, template_id: str, rule_id: str, payload: ExtractionRuleUpdate) -> ExtractionRule:
        rule = self._get_rule(template_id, rule_id)
        if payload.template_version_id:
            self._get_version(template_id, payload.template_version_id)
            rule.template_version_id = payload.template_version_id
        if payload.created_from_annotation_id:
            self.get_annotation(template_id, payload.created_from_annotation_id)
            rule.created_from_annotation_id = payload.created_from_annotation_id
        if payload.rule_type is not None:
            rule.rule_type = payload.rule_type
        if payload.strategy is not None:
            rule.strategy = payload.strategy.value
        if payload.config is not None:
            self._validate_json_size(payload.config, self.settings.max_rule_config_bytes, "RULE_CONFIG_TOO_LARGE")
            rule.config = payload.config
        if "confidence_hint" in payload.model_fields_set:
            rule.confidence_hint = payload.confidence_hint
        self.session.commit()
        self.session.refresh(rule)
        return rule

    def delete_rule(self, template_id: str, rule_id: str) -> None:
        rule = self._get_rule(template_id, rule_id)
        self.session.delete(rule)
        self.session.commit()

    def create_version(self, template_id: str, base_version_id: str | None = None) -> TemplateVersion:
        self.get_template(template_id, detail=False)
        if base_version_id:
            base = self._get_version(template_id, base_version_id)
            snapshot = dict(base.snapshot)
        else:
            snapshot = self._build_snapshot(template_id)
        max_version = self.session.scalar(
            select(func.max(TemplateVersion.version_number)).where(TemplateVersion.template_id == template_id)
        ) or 0
        version = TemplateVersion(
            template_id=template_id,
            version_number=max_version + 1,
            status=TemplateVersionStatus.DRAFT.value,
            snapshot=snapshot,
            created_by=self.principal.id,
        )
        self.session.add(version)
        self.session.commit()
        self.session.refresh(version)
        self._publish("TemplateVersionCreated", {"template_id": template_id, "version_id": version.id, "version_number": version.version_number})
        return version

    def list_versions(self, template_id: str) -> list[TemplateVersion]:
        self.get_template(template_id, detail=False)
        return list(
            self.session.scalars(
                select(TemplateVersion)
                .where(TemplateVersion.template_id == template_id)
                .order_by(TemplateVersion.version_number)
            ).all()
        )

    def get_version(self, template_id: str, version_id: str) -> TemplateVersion:
        return self._get_version(template_id, version_id)

    def publish_version(self, template_id: str, version_id: str) -> TemplateVersion:
        template = self.get_template(template_id, detail=False)
        version = self._get_version(template_id, version_id)
        if version.status == TemplateVersionStatus.ARCHIVED.value:
            raise BusinessRuleError("ARCHIVED_VERSION_CANNOT_BE_PUBLISHED", "Archived version cannot be published")
        snapshot = self._build_snapshot(template_id)
        if not snapshot["fields"]:
            raise BusinessRuleError("EMPTY_TEMPLATE_VERSION", "Template version requires at least one field")
        version.snapshot = snapshot
        version.status = TemplateVersionStatus.PUBLISHED.value
        version.published_by = self.principal.id
        version.published_at = datetime.now(timezone.utc)
        template.active_version_id = version.id
        template.status = TemplateStatus.ACTIVE.value
        self.session.commit()
        self.session.refresh(version)
        self._publish(
            "TemplateVersionPublished",
            {
                "template_id": template.id,
                "version_id": version.id,
                "version_number": version.version_number,
                "category_id": template.category_id,
                "file_format": template.file_format,
                "structure_type": template.structure_type,
            },
        )
        return version

    def archive_version(self, template_id: str, version_id: str) -> TemplateVersion:
        template = self.get_template(template_id, detail=False)
        version = self._get_version(template_id, version_id)
        version.status = TemplateVersionStatus.ARCHIVED.value
        if template.active_version_id == version.id:
            template.active_version_id = None
        self.session.commit()
        self.session.refresh(version)
        return version

    def _get_field(self, template_id: str, field_id: str) -> TemplateField:
        field = self.session.get(TemplateField, field_id)
        if not field or field.template_id != template_id:
            raise NotFoundError("Template field")
        return field

    def _get_signal(self, template_id: str, signal_id: str) -> IdentificationSignal:
        signal = self.session.get(IdentificationSignal, signal_id)
        if not signal or signal.template_id != template_id:
            raise NotFoundError("Identification signal")
        return signal

    def _get_rule(self, template_id: str, rule_id: str) -> ExtractionRule:
        rule = self.session.get(ExtractionRule, rule_id)
        if not rule or rule.template_id != template_id:
            raise NotFoundError("Extraction rule")
        return rule

    def _get_version(self, template_id: str, version_id: str) -> TemplateVersion:
        version = self.session.get(TemplateVersion, version_id)
        if not version or version.template_id != template_id:
            raise NotFoundError("Template version")
        return version

    def _build_snapshot(self, template_id: str) -> dict[str, Any]:
        template = self.get_template(template_id, detail=True)
        return {
            "template": {
                "template_id": template.id,
                "name": template.name,
                "description": template.description,
                "category_id": template.category_id,
                "file_format": template.file_format,
                "structure_type": template.structure_type,
                "status": template.status,
            },
            "fields": [
                {
                    "field_id": item.id,
                    "parent_field_id": item.parent_field_id,
                    "field_path": item.field_path,
                    "label": item.label,
                    "description": item.description,
                    "field_type": item.field_type,
                    "is_required": item.is_required,
                    "is_repeated": item.is_repeated,
                    "is_object": item.is_object,
                    "is_array": item.is_array,
                    "order_index": item.order_index,
                    "status": item.status,
                }
                for item in sorted(template.fields, key=lambda field: (field.order_index, field.field_path))
                if item.status == "active"
            ],
            "identification_signals": [
                {
                    "signal_id": item.id,
                    "signal_type": item.signal_type,
                    "value": item.value,
                    "weight": item.weight,
                    "required": item.required,
                    "negative": item.negative,
                }
                for item in template.identification_signals
            ],
            "annotations": [
                {
                    "annotation_id": item.id,
                    "field_id": item.field_id,
                    "document_id": item.document_id,
                    "annotation_type": item.annotation_type,
                    "source_preview_id": item.source_preview_id,
                    "selected_text": item.selected_text,
                    "selection_payload": item.selection_payload,
                }
                for item in template.annotations
            ],
            "extraction_rules": [
                {
                    "rule_id": item.id,
                    "field_id": item.field_id,
                    "rule_type": item.rule_type,
                    "strategy": item.strategy,
                    "config": item.config,
                    "confidence_hint": item.confidence_hint,
                    "created_from_annotation_id": item.created_from_annotation_id,
                }
                for item in template.extraction_rules
            ],
        }

    def _validate_json_size(self, payload: dict[str, Any], max_bytes: int, code: str) -> None:
        size = len(json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
        if size > max_bytes:
            raise BusinessRuleError(code, "JSON payload exceeds configured size limit")

    def _publish(self, event_type: str, payload: dict[str, Any]) -> None:
        self.publisher.publish(DomainEvent(event_type=event_type, payload=payload, correlation_id=self.correlation_id))
import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.application.schemas import (
    AnnotationCreate,
    ExtractionRuleCreate,
    ExtractionRuleUpdate,
    FieldCreate,
    FieldUpdate,
    IdentificationSignalCreate,
    IdentificationSignalUpdate,
    TemplateCategoryCreate,
    TemplateCreate,
    TemplateUpdate,
)
from app.config import Settings
from app.domain.enums import TemplateStatus, TemplateVersionStatus
from app.errors import BusinessRuleError, ConflictError, NotFoundError
from app.infrastructure.database.models import (
    ExtractionRule,
    IdentificationSignal,
    Template,
    TemplateAnnotation,
    TemplateCategory,
    TemplateField,
    TemplateVersion,
)
from app.infrastructure.events import DomainEvent, EventPublisher
from app.infrastructure.identity_gateway import Principal


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TemplateService:
    def __init__(
        self,
        *,
        session: Session,
        settings: Settings,
        publisher: EventPublisher,
        principal: Principal,
        correlation_id: str,
    ) -> None:
        self.session = session
        self.settings = settings
        self.publisher = publisher
        self.principal = principal
        self.correlation_id = correlation_id

    def create_category(self, payload: TemplateCategoryCreate) -> TemplateCategory:
        category = TemplateCategory(
            name=payload.name.strip(),
            slug=payload.slug.strip().lower(),
            description=payload.description,
            status="active",
        )
        try:
            self.session.add(category)
            self.session.flush()
            self._publish(
                "TemplateCategoryCreated",
                {"category_id": category.id, "slug": category.slug, "status": category.status},
            )
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise ConflictError("TEMPLATE_CATEGORY_SLUG_EXISTS", "Template category slug already exists") from exc
        return category

    def list_categories(self) -> list[TemplateCategory]:
        return list(
            self.session.scalars(
                select(TemplateCategory).order_by(TemplateCategory.name.asc(), TemplateCategory.id.asc())
            ).all()
        )

    def get_category(self, category_id: str) -> TemplateCategory:
        category = self.session.get(TemplateCategory, category_id)
        if category is None:
            raise NotFoundError("Template category")
        return category

    def create_template(self, payload: TemplateCreate) -> Template:
        category = self.get_category(payload.category_id)
        if category.status != "active":
            raise BusinessRuleError("TEMPLATE_CATEGORY_INACTIVE", "Template category must be active")
        template = Template(
            name=payload.name.strip(),
            description=payload.description,
            category_id=category.id,
            file_format=payload.file_format.value,
            structure_type=payload.structure_type.value,
            status=TemplateStatus.DRAFT.value,
            created_by=self.principal.id,
        )
        self.session.add(template)
        self.session.flush()
        self._publish(
            "TemplateCreated",
            {
                "template_id": template.id,
                "category_id": template.category_id,
                "file_format": template.file_format,
                "structure_type": template.structure_type,
                "status": template.status,
            },
        )
        self.session.commit()
        return template

    def list_templates(
        self,
        *,
        category_id: str | None,
        file_format: str | None,
        status: str | None,
        structure_type: str | None,
        search: str | None,
    ) -> tuple[list[Template], int]:
        statement = select(Template)
        if category_id:
            statement = statement.where(Template.category_id == category_id)
        if file_format:
            statement = statement.where(Template.file_format == file_format.upper())
        if status:
            statement = statement.where(Template.status == status)
        if structure_type:
            statement = statement.where(Template.structure_type == structure_type)
        if search:
            statement = statement.where(Template.name.ilike(f"%{search}%"))
        total = self.session.scalar(select(func.count()).select_from(statement.order_by(None).subquery())) or 0
        items = list(
            self.session.scalars(
                statement.order_by(Template.created_at.desc(), Template.id.asc())
            ).all()
        )
        return items, int(total)

    def get_template(self, template_id: str) -> Template:
        template = self.session.scalar(
            select(Template)
            .options(
                selectinload(Template.category),
                selectinload(Template.fields),
                selectinload(Template.identification_signals),
                selectinload(Template.annotations),
                selectinload(Template.extraction_rules),
                selectinload(Template.versions),
            )
            .where(Template.id == template_id)
        )
        if template is None:
            raise NotFoundError("Template")
        return template

    def update_template(self, template_id: str, payload: TemplateUpdate) -> Template:
        template = self.get_template(template_id)
        changes = payload.model_dump(exclude_unset=True)
        if "category_id" in changes and changes["category_id"] is not None:
            category = self.get_category(changes["category_id"])
            if category.status != "active":
                raise BusinessRuleError("TEMPLATE_CATEGORY_INACTIVE", "Template category must be active")
        for field, value in changes.items():
            if hasattr(value, "value"):
                value = value.value
            setattr(template, field, value)
        self._publish("TemplateUpdated", {"template_id": template.id, "fields": sorted(changes)})
        self.session.commit()
        return template

    def update_template_status(self, template_id: str, status: TemplateStatus) -> Template:
        template = self.get_template(template_id)
        template.status = status.value
        self._publish("TemplateUpdated", {"template_id": template.id, "status": template.status})
        self.session.commit()
        return template

    def create_field(self, template_id: str, payload: FieldCreate) -> TemplateField:
        self._ensure_template_exists(template_id)
        self._validate_parent_field(template_id, payload.parent_field_id)
        field = TemplateField(
            template_id=template_id,
            parent_field_id=payload.parent_field_id,
            field_path=payload.field_path,
            label=payload.label,
            description=payload.description,
            field_type=payload.field_type.value,
            is_required=payload.is_required,
            is_repeated=payload.is_repeated,
            is_object=payload.is_object,
            is_array=payload.is_array,
            order_index=payload.order_index,
            status="active",
        )
        try:
            self.session.add(field)
            self.session.flush()
            self._publish(
                "TemplateFieldCreated",
                {"template_id": template_id, "field_id": field.id, "field_path": field.field_path},
            )
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise ConflictError("TEMPLATE_FIELD_PATH_EXISTS", "Field path already exists for this template") from exc
        return field

    def list_fields(self, template_id: str) -> list[TemplateField]:
        self._ensure_template_exists(template_id)
        return list(
            self.session.scalars(
                select(TemplateField)
                .where(TemplateField.template_id == template_id, TemplateField.status == "active")
                .order_by(TemplateField.order_index.asc(), TemplateField.field_path.asc())
            ).all()
        )

    def update_field(self, template_id: str, field_id: str, payload: FieldUpdate) -> TemplateField:
        field = self._get_field(template_id, field_id)
        changes = payload.model_dump(exclude_unset=True)
        if "parent_field_id" in changes:
            self._validate_parent_field(template_id, changes["parent_field_id"], field_id=field_id)
        for key, value in changes.items():
            if hasattr(value, "value"):
                value = value.value
            setattr(field, key, value)
        self.session.commit()
        return field

    def delete_field(self, template_id: str, field_id: str) -> None:
        field = self._get_field(template_id, field_id)
        field.status = "inactive"
        self.session.commit()

    def create_signal(self, template_id: str, payload: IdentificationSignalCreate) -> IdentificationSignal:
        self._ensure_template_exists(template_id)
        signal = IdentificationSignal(
            template_id=template_id,
            signal_type=payload.signal_type.value,
            weight=payload.weight,
            value=payload.value,
            required=payload.required,
            negative=payload.negative,
        )
        self.session.add(signal)
        self.session.flush()
        self._publish(
            "TemplateIdentificationSignalCreated",
            {"template_id": template_id, "signal_id": signal.id, "signal_type": signal.signal_type},
        )
        self.session.commit()
        return signal

    def list_signals(self, template_id: str) -> list[IdentificationSignal]:
        self._ensure_template_exists(template_id)
        return list(
            self.session.scalars(
                select(IdentificationSignal)
                .where(IdentificationSignal.template_id == template_id)
                .order_by(IdentificationSignal.required.desc(), IdentificationSignal.weight.desc())
            ).all()
        )

    def update_signal(
        self,
        template_id: str,
        signal_id: str,
        payload: IdentificationSignalUpdate,
    ) -> IdentificationSignal:
        signal = self._get_signal(template_id, signal_id)
        for key, value in payload.model_dump(exclude_unset=True).items():
            if hasattr(value, "value"):
                value = value.value
            setattr(signal, key, value)
        self.session.commit()
        return signal

    def delete_signal(self, template_id: str, signal_id: str) -> None:
        signal = self._get_signal(template_id, signal_id)
        self.session.delete(signal)
        self.session.commit()

    def create_annotation(self, template_id: str, payload: AnnotationCreate) -> TemplateAnnotation:
        self._ensure_template_exists(template_id)
        self._get_field(template_id, payload.field_id)
        self._validate_mutable_version(template_id, payload.template_version_id)
        self._ensure_json_size(payload.selection_payload, self.settings.max_selection_payload_bytes, "ANNOTATION_PAYLOAD_TOO_LARGE")
        annotation = TemplateAnnotation(
            template_id=template_id,
            template_version_id=payload.template_version_id,
            field_id=payload.field_id,
            document_id=payload.document_id,
            annotation_type=payload.annotation_type.value,
            source_preview_id=payload.source_preview_id,
            selected_text=payload.selected_text,
            selection_payload=payload.selection_payload,
            created_by=self.principal.id,
        )
        self.session.add(annotation)
        self.session.flush()
        self._publish(
            "TemplateAnnotationCreated",
            {
                "template_id": template_id,
                "annotation_id": annotation.id,
                "field_id": annotation.field_id,
                "document_id": annotation.document_id,
                "annotation_type": annotation.annotation_type,
            },
        )
        self.session.commit()
        return annotation

    def list_annotations(
        self,
        template_id: str,
        *,
        field_id: str | None,
        document_id: str | None,
        annotation_type: str | None,
    ) -> list[TemplateAnnotation]:
        self._ensure_template_exists(template_id)
        statement = select(TemplateAnnotation).where(TemplateAnnotation.template_id == template_id)
        if field_id:
            statement = statement.where(TemplateAnnotation.field_id == field_id)
        if document_id:
            statement = statement.where(TemplateAnnotation.document_id == document_id)
        if annotation_type:
            statement = statement.where(TemplateAnnotation.annotation_type == annotation_type)
        return list(self.session.scalars(statement.order_by(TemplateAnnotation.created_at.desc())).all())

    def get_annotation(self, template_id: str, annotation_id: str) -> TemplateAnnotation:
        annotation = self.session.get(TemplateAnnotation, annotation_id)
        if annotation is None or annotation.template_id != template_id:
            raise NotFoundError("Template annotation")
        return annotation

    def update_annotation(self, template_id: str, annotation_id: str, payload: AnnotationUpdate) -> TemplateAnnotation:
        annotation = self.get_annotation(template_id, annotation_id)
        changes = payload.model_dump(exclude_unset=True)
        if "field_id" in changes and changes["field_id"]:
            self._get_field(template_id, changes["field_id"])
        if "template_version_id" in changes:
            self._validate_mutable_version(template_id, changes["template_version_id"])
        if "selection_payload" in changes and changes["selection_payload"] is not None:
            self._ensure_json_size(changes["selection_payload"], self.settings.max_selection_payload_bytes, "ANNOTATION_PAYLOAD_TOO_LARGE")
        for key, value in changes.items():
            setattr(annotation, key, value)
        self._publish("TemplateAnnotationUpdated", {"template_id": template_id, "annotation_id": annotation.id})
        self.session.commit()
        return annotation

    def delete_annotation(self, template_id: str, annotation_id: str) -> None:
        annotation = self.get_annotation(template_id, annotation_id)
        self.session.delete(annotation)
        self.session.commit()

    def create_rule(self, template_id: str, payload: ExtractionRuleCreate) -> ExtractionRule:
        self._ensure_template_exists(template_id)
        self._get_field(template_id, payload.field_id)
        self._validate_mutable_version(template_id, payload.template_version_id)
        if payload.created_from_annotation_id:
            self.get_annotation(template_id, payload.created_from_annotation_id)
        self._ensure_json_size(payload.config, self.settings.max_rule_config_bytes, "EXTRACTION_RULE_CONFIG_TOO_LARGE")
        rule = ExtractionRule(
            template_id=template_id,
            template_version_id=payload.template_version_id,
            field_id=payload.field_id,
            rule_type=payload.rule_type,
            strategy=payload.strategy.value,
            config=payload.config,
            confidence_hint=payload.confidence_hint,
            created_from_annotation_id=payload.created_from_annotation_id,
        )
        self.session.add(rule)
        self.session.flush()
        self._publish(
            "TemplateExtractionRuleCreated",
            {
                "template_id": template_id,
                "extraction_rule_id": rule.id,
                "field_id": rule.field_id,
                "strategy": rule.strategy,
            },
        )
        self.session.commit()
        return rule

    def list_rules(self, template_id: str) -> list[ExtractionRule]:
        self._ensure_template_exists(template_id)
        return list(
            self.session.scalars(
                select(ExtractionRule)
                .where(ExtractionRule.template_id == template_id)
                .order_by(ExtractionRule.created_at.desc())
            ).all()
        )

    def update_rule(self, template_id: str, rule_id: str, payload: ExtractionRuleUpdate) -> ExtractionRule:
        rule = self._get_rule(template_id, rule_id)
        changes = payload.model_dump(exclude_unset=True)
        if "template_version_id" in changes:
            self._validate_mutable_version(template_id, changes["template_version_id"])
        if "created_from_annotation_id" in changes and changes["created_from_annotation_id"]:
            self.get_annotation(template_id, changes["created_from_annotation_id"])
        if "config" in changes and changes["config"] is not None:
            self._ensure_json_size(changes["config"], self.settings.max_rule_config_bytes, "EXTRACTION_RULE_CONFIG_TOO_LARGE")
        for key, value in changes.items():
            if hasattr(value, "value"):
                value = value.value
            setattr(rule, key, value)
        self.session.commit()
        return rule

    def delete_rule(self, template_id: str, rule_id: str) -> None:
        rule = self._get_rule(template_id, rule_id)
        self.session.delete(rule)
        self.session.commit()

    def create_version(self, template_id: str, base_version_id: str | None) -> TemplateVersion:
        self._ensure_template_exists(template_id)
        base_snapshot: dict[str, Any] = {}
        if base_version_id:
            base = self.get_version(template_id, base_version_id)
            base_snapshot = base.snapshot
        next_number = (self.session.scalar(
            select(func.max(TemplateVersion.version_number)).where(TemplateVersion.template_id == template_id)
        ) or 0) + 1
        version = TemplateVersion(
            template_id=template_id,
            version_number=next_number,
            status=TemplateVersionStatus.DRAFT.value,
            snapshot=base_snapshot or self._build_snapshot(template_id),
            created_by=self.principal.id,
        )
        self.session.add(version)
        self.session.flush()
        self._publish(
            "TemplateVersionCreated",
            {"template_id": template_id, "version_id": version.id, "version_number": version.version_number},
        )
        self.session.commit()
        return version

    def list_versions(self, template_id: str) -> list[TemplateVersion]:
        self._ensure_template_exists(template_id)
        return list(
            self.session.scalars(
                select(TemplateVersion)
                .where(TemplateVersion.template_id == template_id)
                .order_by(TemplateVersion.version_number.desc())
            ).all()
        )

    def get_version(self, template_id: str, version_id: str) -> TemplateVersion:
        version = self.session.get(TemplateVersion, version_id)
        if version is None or version.template_id != template_id:
            raise NotFoundError("Template version")
        return version

    def publish_version(self, template_id: str, version_id: str) -> TemplateVersion:
        template = self.get_template(template_id)
        version = self.get_version(template_id, version_id)
        if version.status == TemplateVersionStatus.ARCHIVED.value:
            raise BusinessRuleError("TEMPLATE_VERSION_ARCHIVED", "Archived template version cannot be published")
        fields = [field for field in template.fields if field.status == "active"]
        if not fields:
            raise BusinessRuleError("TEMPLATE_VERSION_EMPTY", "Template version must include at least one active field")
        version.snapshot = self._build_snapshot(template_id)
        version.status = TemplateVersionStatus.PUBLISHED.value
        version.published_by = self.principal.id
        version.published_at = utc_now()
        template.active_version_id = version.id
        template.status = TemplateStatus.ACTIVE.value
        self._publish(
            "TemplateVersionPublished",
            {
                "template_id": template.id,
                "version_id": version.id,
                "version_number": version.version_number,
                "category_id": template.category_id,
                "file_format": template.file_format,
                "structure_type": template.structure_type,
            },
        )
        self.session.commit()
        return version

    def archive_version(self, template_id: str, version_id: str) -> TemplateVersion:
        template = self.get_template(template_id)
        version = self.get_version(template_id, version_id)
        version.status = TemplateVersionStatus.ARCHIVED.value
        if template.active_version_id == version.id:
            template.active_version_id = None
            template.status = TemplateStatus.INACTIVE.value
        self._publish(
            "TemplateArchived",
            {"template_id": template_id, "version_id": version.id, "version_number": version.version_number},
        )
        self.session.commit()
        return version

    def _ensure_template_exists(self, template_id: str) -> None:
        if self.session.get(Template, template_id) is None:
            raise NotFoundError("Template")

    def _get_field(self, template_id: str, field_id: str) -> TemplateField:
        field = self.session.get(TemplateField, field_id)
        if field is None or field.template_id != template_id:
            raise NotFoundError("Template field")
        return field

    def _validate_parent_field(
        self,
        template_id: str,
        parent_field_id: str | None,
        *,
        field_id: str | None = None,
    ) -> None:
        if parent_field_id is None:
            return
        if parent_field_id == field_id:
            raise BusinessRuleError("TEMPLATE_FIELD_PARENT_SELF", "Field cannot be its own parent")
        parent = self._get_field(template_id, parent_field_id)
        if parent.status != "active":
            raise BusinessRuleError("TEMPLATE_FIELD_PARENT_INACTIVE", "Parent field must be active")

    def _get_signal(self, template_id: str, signal_id: str) -> IdentificationSignal:
        signal = self.session.get(IdentificationSignal, signal_id)
        if signal is None or signal.template_id != template_id:
            raise NotFoundError("Identification signal")
        return signal

    def _get_rule(self, template_id: str, rule_id: str) -> ExtractionRule:
        rule = self.session.get(ExtractionRule, rule_id)
        if rule is None or rule.template_id != template_id:
            raise NotFoundError("Extraction rule")
        return rule

    def _validate_mutable_version(self, template_id: str, version_id: str | None) -> None:
        if version_id is None:
            return
        version = self.get_version(template_id, version_id)
        if version.status == TemplateVersionStatus.PUBLISHED.value:
            raise BusinessRuleError(
                "TEMPLATE_VERSION_PUBLISHED_IMMUTABLE",
                "Published template versions cannot be edited directly",
            )

    def _ensure_json_size(self, payload: dict[str, Any], limit_bytes: int, code: str) -> None:
        size = len(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
        if size > limit_bytes:
            raise BusinessRuleError(code, "JSON payload exceeds configured size limit")

    def _build_snapshot(self, template_id: str) -> dict[str, Any]:
        template = self.get_template(template_id)
        return {
            "template": {
                "template_id": template.id,
                "name": template.name,
                "description": template.description,
                "category_id": template.category_id,
                "file_format": template.file_format,
                "structure_type": template.structure_type,
                "status": template.status,
            },
            "fields": [
                {
                    "id": field.id,
                    "parent_field_id": field.parent_field_id,
                    "field_path": field.field_path,
                    "label": field.label,
                    "description": field.description,
                    "field_type": field.field_type,
                    "is_required": field.is_required,
                    "is_repeated": field.is_repeated,
                    "is_object": field.is_object,
                    "is_array": field.is_array,
                    "order_index": field.order_index,
                }
                for field in sorted(template.fields, key=lambda item: (item.order_index, item.field_path))
                if field.status == "active"
            ],
            "identification_signals": [
                {
                    "id": signal.id,
                    "signal_type": signal.signal_type,
                    "weight": signal.weight,
                    "value": signal.value,
                    "required": signal.required,
                    "negative": signal.negative,
                }
                for signal in template.identification_signals
            ],
            "annotations": [
                {
                    "id": annotation.id,
                    "field_id": annotation.field_id,
                    "document_id": annotation.document_id,
                    "annotation_type": annotation.annotation_type,
                    "source_preview_id": annotation.source_preview_id,
                    "selected_text": annotation.selected_text,
                    "selection_payload": annotation.selection_payload,
                }
                for annotation in template.annotations
            ],
            "extraction_rules": [
                {
                    "id": rule.id,
                    "field_id": rule.field_id,
                    "rule_type": rule.rule_type,
                    "strategy": rule.strategy,
                    "config": rule.config,
                    "confidence_hint": rule.confidence_hint,
                    "created_from_annotation_id": rule.created_from_annotation_id,
                }
                for rule in template.extraction_rules
            ],
        }

    def _publish(self, event_type: str, payload: dict[str, Any]) -> None:
        self.publisher.publish(
            DomainEvent(
                event_type=event_type,
                payload=payload,
                correlation_id=self.correlation_id,
            )
        )
