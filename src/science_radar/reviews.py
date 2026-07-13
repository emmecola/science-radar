import json
from enum import Enum
from typing import Any, TypeVar

from pydantic import BaseModel, Field, model_validator


ReviewModel = TypeVar("ReviewModel", bound=BaseModel)


class FactStatus(str, Enum):
    VERIFIED = "VERIFIED"
    ACCEPTABLE_UNCERTAINTY = "ACCEPTABLE_UNCERTAINTY"
    REVISE = "REVISE"


class EditorialNote(BaseModel):
    location: str
    issue: str
    required_fix: str


class EditorialReview(BaseModel):
    structure: int = Field(ge=1, le=10)
    clarity: int = Field(ge=1, le=10)
    engagement: int = Field(ge=1, le=10)
    revision_notes: list[EditorialNote]

    @model_validator(mode="after")
    def require_notes_when_revision_is_needed(self):
        if not editorial_approved(self) and not self.revision_notes:
            raise ValueError("Reviews with a score below 7 must include revision_notes")
        return self


class FactCheckClaim(BaseModel):
    claim: str
    status: FactStatus
    note: str
    required_fix: str | None = None

    @model_validator(mode="after")
    def require_fix_for_revision(self):
        if self.status == FactStatus.REVISE and not self.required_fix:
            raise ValueError("REVISE claims must include required_fix")
        return self


class FactCheckReport(BaseModel):
    claims: list[FactCheckClaim] = Field(min_length=1)


def editorial_approved(review: EditorialReview) -> bool:
    return min(
        review.structure,
        review.clarity,
        review.engagement,
    ) >= 7


def fact_check_approved(report: FactCheckReport) -> bool:
    return all(claim.status != FactStatus.REVISE for claim in report.claims)


def parse_review(raw: str, model: type[ReviewModel]) -> ReviewModel:
    try:
        return model.model_validate_json(raw)
    except ValueError as direct_error:
        object_start = raw.find("{")
        if object_start == -1:
            raise ValueError(f"{model.__name__} output contains no JSON object") from direct_error

        try:
            data, _ = json.JSONDecoder().raw_decode(raw[object_start:])
            return model.model_validate(data)
        except (json.JSONDecodeError, ValueError) as extraction_error:
            raise ValueError(f"Invalid {model.__name__} output: {extraction_error}") from direct_error


def editorial_review_guardrail(output: Any) -> tuple[bool, str]:
    try:
        review = parse_review(output.raw, EditorialReview)
    except ValueError as error:
        return (
            False,
            "Invalid editorial review. Return one corrected JSON object matching the "
            f"required schema. Validation error: {error}",
        )
    return True, review.model_dump_json()


def fact_check_guardrail(output: Any) -> tuple[bool, str]:
    try:
        report = parse_review(output.raw, FactCheckReport)
    except ValueError as error:
        return (
            False,
            "Invalid fact-check report. Audit every concrete factual assertion in the "
            "article and return at least one claim in one corrected JSON object matching "
            f"the required schema. Validation error: {error}",
        )
    return True, report.model_dump_json()
