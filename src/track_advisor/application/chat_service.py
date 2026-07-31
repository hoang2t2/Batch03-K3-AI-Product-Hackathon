from __future__ import annotations

from typing import Any

from track_advisor.application.ports import AssessmentRepository, TrackAdvisorProvider
from track_advisor.domain.models import Track


class ScopedChatService:
    def __init__(self, assessments: AssessmentRepository, provider: TrackAdvisorProvider, tracks: list[Track]):
        self.assessments, self.provider, self.tracks = assessments, provider, tracks

    def answer(self, assessment_id: str, question: str) -> dict[str, Any]:
        """Trả lời trong phạm vi dashboard; câu đúng chủ đề nhưng thiếu dữ liệu thì tra cứu nguồn ngoài."""
        snapshot = self.assessments.get(assessment_id)
        if snapshot is None:
            raise ValueError("Không tìm thấy assessment snapshot.")
        result = self.provider.answer(question, snapshot, self.tracks)
        if result["scope"] != "needs_reference":
            return {"scope": result["scope"], "answer": result["answer"], "sources": [], "grounded": False}
        found = self.provider.search_references(question, result.get("search_query", ""), snapshot, self.tracks)
        return {
            "scope": "needs_reference", "answer": found["answer"],
            "sources": found.get("sources", []), "grounded": bool(found.get("grounded")),
        }
