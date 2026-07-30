from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class CVDescriptions:
    technical_skills: list[str]
    experience: list[str]
    strengths: list[str]
    weaknesses: list[str]
    interests: list[str]

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "CVDescriptions":
        required = {"technical_skills", "experience", "strengths", "weaknesses", "interests"}
        missing = required - raw.keys()
        if missing or not all(isinstance(raw[key], list) for key in required):
            detail = f"thiếu trường: {', '.join(sorted(missing))}" if missing else "các trường phải là list"
            raise ValueError(f"cv_descriptions không hợp lệ ({detail}).")
        return cls(**{key: [str(value) for value in raw[key]] for key in required})


@dataclass(frozen=True)
class StudentProfile:
    student_id: str
    name: str
    learning_scores: dict[str, float]
    cv_descriptions: CVDescriptions

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "StudentProfile":
        required = {"student_id", "name", "scores", "cv_descriptions"}
        missing = required - raw.keys()
        if missing:
            raise ValueError(f"Student profile thiếu trường: {', '.join(sorted(missing))}")
        if not isinstance(raw["scores"], dict):
            raise ValueError("scores phải là object.")
        scores = {name: float(value) for name, value in raw["scores"].items()}
        if any(score < 0 or score > 100 for score in scores.values()):
            raise ValueError("Mọi điểm quá trình phải nằm trong khoảng 0–100.")
        return cls(
            student_id=str(raw["student_id"]), name=str(raw["name"]), learning_scores=scores,
            cv_descriptions=CVDescriptions.from_dict(raw["cv_descriptions"]),
        )

    def public_features(self) -> dict[str, Any]:
        return {"student_id": self.student_id, "name": self.name, "learning_scores": self.learning_scores}


@dataclass(frozen=True)
class Track:
    id: str
    name: str
    summary: str
    lesson_weights: dict[str, float]
    lesson_metadata: dict[str, dict[str, Any]]
    focus: list[str]
    ideal_profile: list[str]
    important_lessons: list[str]
    evaluation_guideline: str


@dataclass(frozen=True)
class TrackResult:
    track_id: str
    suitability_score: float
    reasons: list[str]
    suggestions: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
