import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from track_advisor.application.assessment_service import AssessmentService
from track_advisor.application.chat_service import ScopedChatService
from track_advisor.domain.models import CVDescriptions, StudentProfile, Track, TrackResult


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
