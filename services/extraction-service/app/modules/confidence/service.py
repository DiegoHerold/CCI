from app.domain.enums import ExtractedFieldStatus


class ConfidenceService:
    def __init__(self, low_confidence_threshold: float) -> None:
        self.low_confidence_threshold = low_confidence_threshold

    def final_confidence(
        self,
        *,
        worker_confidence: float,
        normalization_success: bool,
        evidence_exists: bool,
        raw_status: str,
    ) -> float:
        confidence = max(0.0, min(float(worker_confidence or 0.0), 1.0))
        if not normalization_success:
            confidence = min(confidence, 0.5)
        if not evidence_exists:
            confidence = min(confidence, 0.6)
        if raw_status in {"ambiguous", "partial"}:
            confidence = min(confidence, 0.7)
        if raw_status in {"not_found", "failed"}:
            confidence = 0.0
        return round(confidence, 4)

    def status(
        self,
        *,
        raw_status: str,
        normalization_success: bool,
        evidence_exists: bool,
        confidence: float,
        is_required: bool,
    ) -> ExtractedFieldStatus:
        if raw_status == "ambiguous":
            return ExtractedFieldStatus.AMBIGUOUS
        if raw_status in {"not_found", "failed"}:
            return ExtractedFieldStatus.REQUIRES_REVIEW if is_required else ExtractedFieldStatus.NOT_FOUND
        if not normalization_success:
            return ExtractedFieldStatus.NORMALIZATION_FAILED
        if not evidence_exists:
            return ExtractedFieldStatus.EVIDENCE_MISSING
        if confidence < self.low_confidence_threshold:
            return ExtractedFieldStatus.LOW_CONFIDENCE
        return ExtractedFieldStatus.NORMALIZED
