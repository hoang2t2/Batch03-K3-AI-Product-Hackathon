from __future__ import annotations

import json
from pathlib import Path

from track_advisor.domain.models import StudentProfile


class JsonStudentProfileRepository:
    def __init__(self, path: Path):
        self.path = path

    def get(self, student_id: str) -> StudentProfile | None:
        students = self._load()
        raw = next((student for student in students if student["student_id"] == student_id), None)
        return StudentProfile.from_dict(raw) if raw else None

    def list_students(self) -> list[dict[str, str]]:
        return [{"student_id": student["student_id"], "name": student["name"]} for student in self._load()]

    def _load(self) -> list[dict]:
        return json.loads(self.path.read_text(encoding="utf-8"))


class JsonAssessmentRepository:
    def __init__(self, path: Path):
        self.path = path

    def _load(self) -> dict:
        return json.loads(self.path.read_text(encoding="utf-8")) if self.path.is_file() else {}

    def save(self, snapshot: dict) -> None:
        self.path.parent.mkdir(exist_ok=True)
        values = self._load()
        values[snapshot["assessment_id"]] = snapshot
        self.path.write_text(json.dumps(values, ensure_ascii=False, indent=2), encoding="utf-8")

    def get(self, assessment_id: str) -> dict | None:
        return self._load().get(assessment_id)
