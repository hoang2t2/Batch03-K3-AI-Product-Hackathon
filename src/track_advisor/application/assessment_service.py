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
        return {
            **profile.public_features(),
            "cv_descriptions": {
                "technical_skills": profile.cv_descriptions.technical_skills,
                "experience": profile.cv_descriptions.experience,
                "strengths": profile.cv_descriptions.strengths,
                "weaknesses": profile.cv_descriptions.weaknesses,
                "interests": profile.cv_descriptions.interests,
            },
            "course_lessons": [
                {
                    "lesson_id": lesson_id,
                    "title": lesson_data["title"],
                    "skills": lesson_data["skills"],
                    "score": profile.learning_scores.get(lesson_id, 0),
                }
                for lesson_id, lesson_data in self._lesson_catalog().items()
            ],
            "lab_completion_score": self._calculate_lab_completion(profile.learning_scores),
            "quiz_score_accumulation": self._calculate_quiz_score(profile.learning_scores),
        }

    def list_students(self) -> list[dict[str, str]]:
        return self.profiles.list_students()

    def create(self, student_id: str) -> dict:
        profile = self.profiles.get(student_id)
        if profile is None:
            raise ValueError("Không tìm thấy hồ sơ học viên.")
        results = self._validate_results(self.provider.evaluate(profile, self.tracks))
        top_score = results[0].suitability_score
        recommendation_ids = [result.track_id for result in results if result.suitability_score == top_score]
        self_assessment_context = self._build_self_assessment_context(profile)
        self_assessment = self._build_self_assessment_text(profile, results, self_assessment_context)
        snapshot = {
            "assessment_id": f"A-{uuid4().hex[:8].upper()}",
            "created_at": datetime.now(UTC).isoformat(),
            "catalogue_version": "v1",
            "student_id": profile.student_id,
            "profile_features_used": profile.public_features(),
            "self_assessment_context": self_assessment_context,
            "self_assessment": self_assessment,
            "track_results": [
                result.to_dict() | {"track_name": next(track.name for track in self.tracks if track.id == result.track_id)}
                for result in results
            ],
            "recommendation_ids": recommendation_ids,
            "notice": "Gợi ý hỗ trợ định hướng sau Giai đoạn 1; hệ thống không tự động ghi danh hoặc thay đổi hồ sơ.",
        }
        self.assessments.save(snapshot)
        return snapshot

    def _calculate_lab_completion(self, scores: dict[str, float]) -> float:
        lab_lessons = ["react_agent", "prompt_engineering", "prototype_demo", "rag_pipeline", "multi_agent", "data_pipeline", "cloud_deployment", "llmops"]
        return round(sum(scores.get(lesson, 0.0) for lesson in lab_lessons) / len(lab_lessons), 1)

    def _calculate_quiz_score(self, scores: dict[str, float]) -> float:
        quiz_lessons = ["ai_foundation", "problem_definition", "product_thinking", "guardrails", "evaluation", "retrospective"]
        return round(sum(scores.get(lesson, 0.0) for lesson in quiz_lessons) / len(quiz_lessons), 1)

    def _build_self_assessment_context(self, profile: object) -> dict:
        scores = profile.learning_scores
        lab_completion_score = self._calculate_lab_completion(scores)
        quiz_score_accumulation = self._calculate_quiz_score(scores)
        top_strength_lessons = [
            {"lesson": lesson, "score": round(score, 1)}
            for lesson, score in sorted(scores.items(), key=lambda item: item[1], reverse=True)[:3]
        ]
        return {
            "student_id": profile.student_id,
            "giai_doan_1_focus": "Tự đánh giá thế mạnh chuyên môn, Lab completion và Quiz score tích lũy",
            "lab_completion_score": lab_completion_score,
            "quiz_score_accumulation": quiz_score_accumulation,
            "top_strength_lessons": top_strength_lessons,
            "cv_strengths": [strength for strength in profile.cv_descriptions.strengths[:3]],
        }

    def _lesson_catalog(self) -> dict[str, dict[str, object]]:
        return {
            "ai_foundation": {"title": "AI & LLM Foundation", "skills": ["LLM", "reasoning", "token"]},
            "problem_definition": {"title": "Xác định bài toán cho AI", "skills": ["problem analysis", "requirements"]},
            "react_agent": {"title": "Design Pattern ReAct", "skills": ["agent", "reasoning", "tool usage"]},
            "prompt_engineering": {"title": "Prompt Engineering", "skills": ["prompt", "tool calling"]},
            "product_thinking": {"title": "AI Product Thinking", "skills": ["product", "requirements"]},
            "prototype_demo": {"title": "Prototype & Demo", "skills": ["prototype", "demo"]},
            "data_foundation": {"title": "Data Foundation", "skills": ["embedding", "vector store"]},
            "rag_pipeline": {"title": "RAG Pipeline", "skills": ["retrieval", "rag"]},
            "multi_agent": {"title": "Multi-Agent", "skills": ["agent", "orchestration"]},
            "data_pipeline": {"title": "Data Pipeline", "skills": ["etl", "observability"]},
            "guardrails": {"title": "Guardrails & Responsible AI", "skills": ["safety", "guardrails"]},
            "cloud_deployment": {"title": "Cloud & Deployment", "skills": ["cloud", "deployment"]},
            "llmops": {"title": "LLMOps", "skills": ["monitoring", "llmops"]},
            "evaluation": {"title": "Evaluation", "skills": ["evaluation", "benchmark"]},
            "retrospective": {"title": "Retrospective & Định hướng", "skills": ["reflection", "career"]},
        }

    def _build_self_assessment_text(self, profile: object, results: list[TrackResult], context: dict) -> str:
        best_track = results[0]
        track_name = next(track.name for track in self.tracks if track.id == best_track.track_id)
        top_lessons = ", ".join(f"{item['lesson']} ({item['score']}/100)" for item in context["top_strength_lessons"])
        return (
            f"Học viên {profile.student_id} có điểm Lab {context['lab_completion_score']}/100 và Quiz tích lũy {context['quiz_score_accumulation']}/100. "
            f"Điểm mạnh nổi bật: {top_lessons}. nhánh phù hợp nhất là {track_name} với mức độ phù hợp {best_track.suitability_score}/10."
        )

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
