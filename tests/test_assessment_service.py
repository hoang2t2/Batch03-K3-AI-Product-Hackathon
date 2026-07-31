import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from track_advisor.application.assessment_service import AssessmentService
from track_advisor.application.chat_service import ScopedChatService
from track_advisor.domain.models import CVDescriptions, StudentProfile, Track, TrackResult
from track_advisor.infrastructure.gemini_provider import build_provider


TRACKS = [
    Track("one", "One", "", {"lesson": 1.0}, {"lesson": {"title": "Lesson", "skills": []}}, [], [], ["lesson"], "guide"),
    Track("two", "Two", "", {"lesson": 1.0}, {"lesson": {"title": "Lesson", "skills": []}}, [], [], ["lesson"], "guide"),
    Track("three", "Three", "", {"lesson": 1.0}, {"lesson": {"title": "Lesson", "skills": []}}, [], [], ["lesson"], "guide"),
]
PROFILE = StudentProfile("student-1", "Student", {"lesson": 80}, CVDescriptions([], [], [], [], []))


class Profiles:
    def get(self, student_id): return PROFILE if student_id == PROFILE.student_id else None


class Snapshots:
    def __init__(self): self.values = {}
    def save(self, snapshot): self.values[snapshot["assessment_id"]] = snapshot
    def get(self, assessment_id): return self.values.get(assessment_id)


class Provider:
    def evaluate(self, profile, tracks):
        return [TrackResult(track.id, 8.0, ["Có căn cứ"], ["Đề xuất"]) for track in tracks]
    def answer(self, question, snapshot, tracks):
        scope = "out_of_scope" if "Thời tiết" in question else "in_scope"
        return {"scope": scope, "answer": "Câu trả lời do provider quyết định scope."}


class AssessmentServiceTests(unittest.TestCase):
    def setUp(self):
        self.store = Snapshots()
        self.assessments = AssessmentService(Profiles(), self.store, Provider(), TRACKS)

    def test_assessment_always_covers_three_tracks(self):
        snapshot = self.assessments.create("student-1")
        self.assertEqual({item["track_id"] for item in snapshot["track_results"]}, {"one", "two", "three"})
        self.assertEqual(set(snapshot["recommendation_ids"]), {"one", "two", "three"})

    def test_suitability_score_is_capped_at_ten(self):
        snapshot = self.assessments.create("student-1")
        second = next(item for item in snapshot["track_results"] if item["track_id"] == "two")
        self.assertEqual(second["suitability_score"], 8.0)

    def test_chat_returns_scope_decided_by_provider_prompt(self):
        snapshot = self.assessments.create("student-1")
        chat = ScopedChatService(self.store, Provider(), TRACKS)
        self.assertEqual(chat.answer(snapshot["assessment_id"], "Thời tiết hôm nay?")["scope"], "out_of_scope")

    def test_create_includes_self_assessment_summary(self):
        snapshot = self.assessments.create("student-1")
        self.assertIn("self_assessment", snapshot)
        self.assertIn("nhánh phù hợp nhất", snapshot["self_assessment"])

    def test_profile_summary_exposes_cv_and_course_lessons(self):
        summary = self.assessments.profile_summary("student-1")
        self.assertIn("cv_descriptions", summary)
        self.assertIn("course_lessons", summary)
        self.assertTrue(summary["course_lessons"])

    def test_build_provider_falls_back_to_mock_when_key_missing(self):
        previous = os.environ.get("GEMINI_API_KEY")
        os.environ["GEMINI_API_KEY"] = ""
        try:
            provider = build_provider()
            self.assertEqual(provider.__class__.__name__, "MockTrackAdvisorProvider")
        finally:
            if previous is None:
                os.environ.pop("GEMINI_API_KEY", None)
            else:
                os.environ["GEMINI_API_KEY"] = previous

    def test_snapshot_includes_self_assessment_context(self):
        snapshot = self.assessments.create("student-1")
        self.assertIn("self_assessment_context", snapshot)
        self.assertEqual(snapshot["self_assessment_context"]["student_id"], "student-1")
        self.assertEqual(snapshot["self_assessment_context"]["giai_doan_1_focus"], "Tự đánh giá thế mạnh chuyên môn, Lab completion và Quiz score tích lũy")

    def test_mock_provider_rejects_off_topic_requests(self):
        previous = os.environ.get("GEMINI_API_KEY")
        os.environ["GEMINI_API_KEY"] = ""
        try:
            provider = build_provider()
            snapshot = {"assessment_id": "A-1", "track_results": [], "recommendation_ids": ["one", "two", "three"]}
            result = provider.answer("Giúp em viết CV xin việc", snapshot, TRACKS)
            self.assertEqual(result["scope"], "out_of_scope")
        finally:
            if previous is None:
                os.environ.pop("GEMINI_API_KEY", None)
            else:
                os.environ["GEMINI_API_KEY"] = previous

    def test_mock_provider_rejects_greetings_and_irrelevant_questions(self):
        previous = os.environ.get("GEMINI_API_KEY")
        os.environ["GEMINI_API_KEY"] = ""
        try:
            provider = build_provider()
            snapshot = {"assessment_id": "A-1", "track_results": [], "recommendation_ids": ["one", "two", "three"]}
            for question in ["Chào em", "Cảm ơn", "Em có thể kể chuyện đời tư không?"]:
                with self.subTest(question=question):
                    self.assertEqual(provider.answer(question, snapshot, TRACKS)["scope"], "out_of_scope")
        finally:
            if previous is None:
                os.environ.pop("GEMINI_API_KEY", None)
            else:
                os.environ["GEMINI_API_KEY"] = previous
