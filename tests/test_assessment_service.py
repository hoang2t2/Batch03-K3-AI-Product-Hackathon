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
    def __init__(self): self.searches = []
    def evaluate(self, profile, tracks):
        return [TrackResult(track.id, 8.0, ["Có căn cứ"], ["Đề xuất"]) for track in tracks]
    def answer(self, question, snapshot, tracks):
        if "Thời tiết" in question:
            return {"scope": "out_of_scope", "answer": "Ngoài phạm vi.", "search_query": ""}
        if "làm những gì" in question:
            return {"scope": "needs_reference", "answer": "", "search_query": "công việc AI Product"}
        return {"scope": "in_scope", "answer": "Câu trả lời do provider quyết định scope.", "search_query": ""}
    def search_references(self, question, search_query, snapshot, tracks):
        self.searches.append(search_query)
        return {
            "answer": "Tổng hợp từ nguồn ngoài.", "grounded": True,
            "sources": [{"title": "Bài viết", "url": "https://example.com/a", "source": "example.com", "kind": "article"}],
        }


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
        reply = chat.answer(snapshot["assessment_id"], "Thời tiết hôm nay?")
        self.assertEqual(reply["scope"], "out_of_scope")
        self.assertEqual(reply["sources"], [])

    def test_in_scope_answer_carries_no_sources(self):
        snapshot = self.assessments.create("student-1")
        chat = ScopedChatService(self.store, Provider(), TRACKS)
        reply = chat.answer(snapshot["assessment_id"], "Vì sao track này được gợi ý?")
        self.assertEqual(reply["scope"], "in_scope")
        self.assertEqual(reply["sources"], [])

    def test_topical_question_without_data_triggers_reference_search(self):
        snapshot = self.assessments.create("student-1")
        provider = Provider()
        chat = ScopedChatService(self.store, provider, TRACKS)
        reply = chat.answer(snapshot["assessment_id"], "AI Product sau này sẽ làm những gì?")
        self.assertEqual(reply["scope"], "needs_reference")
        self.assertEqual(provider.searches, ["công việc AI Product"])
        self.assertEqual([source["url"] for source in reply["sources"]], ["https://example.com/a"])
        self.assertTrue(reply["grounded"])
