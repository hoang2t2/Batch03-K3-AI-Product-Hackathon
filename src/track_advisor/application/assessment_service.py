from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from track_advisor.application.ports import AssessmentRepository, StudentProfileRepository, TrackAdvisorProvider
from track_advisor.domain.models import Track, TrackResult


class AssessmentService:
    def __init__(self, profiles: StudentProfileRepository, assessments: AssessmentRepository, provider: TrackAdvisorProvider, tracks: list[Track]):
        self.profiles, self.assessments, self.provider, self.tracks = profiles, assessments, provider, tracks

    def profile_summary(self, student_id: str) -> dict:
        profile = self.profiles.get(student_id)
        if profile is None:
            raise ValueError("Không tìm thấy hồ sơ học viên.")
        self._validate_score_coverage(profile.learning_scores)
        return profile.public_features()

    def list_students(self) -> list[dict[str, str]]:
        return self.profiles.list_students()

    def create(self, student_id: str) -> dict:
        profile = self.profiles.get(student_id)
        if profile is None:
            raise ValueError("Không tìm thấy hồ sơ học viên.")
        results = self._validate_results(self.provider.evaluate(profile, self.tracks))
        top_score = results[0].suitability_score
        recommendation_ids = [result.track_id for result in results if result.suitability_score == top_score]
        snapshot = {
            "assessment_id": f"A-{uuid4().hex[:8].upper()}",
            "created_at": datetime.now(UTC).isoformat(),
            "catalogue_version": "v1",
            "student_id": profile.student_id,
            "profile_features_used": profile.public_features(),
            "track_results": [
                result.to_dict() | {"track_name": next(track.name for track in self.tracks if track.id == result.track_id)}
                for result in results
            ],
            "recommendation_ids": recommendation_ids,
            "notice": "Gợi ý hỗ trợ định hướng; hệ thống không tự động ghi danh hoặc thay đổi hồ sơ.",
        }
        self.assessments.save(snapshot)
        return snapshot

    def _validate_score_coverage(self, scores: dict[str, float]) -> None:
        expected_lessons = set(self.tracks[0].lesson_weights)
        missing = expected_lessons - set(scores)
        unknown = set(scores) - expected_lessons
        if missing or unknown:
            problems = []
            if missing:
                problems.append(f"thiếu điểm: {', '.join(sorted(missing))}")
            if unknown:
                problems.append(f"lesson không thuộc curriculum: {', '.join(sorted(unknown))}")
            raise ValueError("Input scores không đúng schema (" + "; ".join(problems) + ").")

    def _validate_results(self, results: list[TrackResult]) -> list[TrackResult]:
        ids = {result.track_id for result in results}
        expected = {track.id for track in self.tracks}
        if ids != expected or len(results) != 3:
            raise ValueError("Provider phải đánh giá đầy đủ và duy nhất cả ba track.")
        validated: list[TrackResult] = []
        for result in results:
            validated.append(TrackResult(
                track_id=result.track_id,
                suitability_score=round(max(0, min(10, float(result.suitability_score))), 1),
                reasons=result.reasons[:3], suggestions=result.suggestions[:3],
            ))
        return sorted(validated, key=lambda item: -item.suitability_score)
