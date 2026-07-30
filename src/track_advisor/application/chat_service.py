from __future__ import annotations

from track_advisor.application.ports import AssessmentRepository, TrackAdvisorProvider
from track_advisor.domain.models import Track


class ScopedChatService:
    def __init__(self, assessments: AssessmentRepository, provider: TrackAdvisorProvider, tracks: list[Track]):
        self.assessments, self.provider, self.tracks = assessments, provider, tracks

    def answer(self, assessment_id: str, question: str) -> dict[str, str]:
        snapshot = self.assessments.get(assessment_id)
        if snapshot is None:
            raise ValueError("Không tìm thấy assessment snapshot.")
        return self.provider.answer(question, snapshot, self.tracks)
