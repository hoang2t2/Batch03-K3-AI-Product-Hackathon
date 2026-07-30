from __future__ import annotations

import json
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from track_advisor.application.assessment_service import AssessmentService
from track_advisor.application.chat_service import ScopedChatService
from track_advisor.domain.catalogue import load_catalogue
from track_advisor.infrastructure.gemini_provider import build_provider
from track_advisor.infrastructure.json_repositories import JsonAssessmentRepository, JsonStudentProfileRepository


ROOT = Path(__file__).resolve().parents[3]
STATIC_ROOT = Path(__file__).parent / "static"


def build_services() -> tuple[AssessmentService, ScopedChatService]:
    tracks = load_catalogue(ROOT / "data" / "mock_data" / "tracks_info.json", ROOT / "data" / "mock_data" / "lessons_info.json")
    assessments = JsonAssessmentRepository(ROOT / "runtime" / "assessments.json")
    provider = build_provider()
    profiles = JsonStudentProfileRepository(ROOT / "data" / "mock_data" / "student_scores.json")
    return AssessmentService(profiles, assessments, provider, tracks), ScopedChatService(assessments, provider, tracks)


class AppHandler(SimpleHTTPRequestHandler):
    assessment_service, chat_service = build_services()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_ROOT), **kwargs)

    def _respond_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/health":
            self._respond_json({"status": "ok"})
            return
        if path == "/api/students":
            self._respond_json({"students": self.assessment_service.list_students()})
            return
        if path.startswith("/api/students/") and path.endswith("/profile"):
            student_id = path.split("/")[3]
            try:
                self._respond_json(self.assessment_service.profile_summary(student_id))
            except ValueError as error:
                self._respond_json({"error": str(error)}, HTTPStatus.NOT_FOUND)
            return
        if path == "/":
            self.path = "/index.html"
        super().do_GET()

    def do_POST(self) -> None:
        try:
            size = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(size))
            path = urlparse(self.path).path
            if path == "/api/assessments":
                self._respond_json(self.assessment_service.create(payload["student_id"]))
                return
            if path == "/api/chats":
                self._respond_json(self.chat_service.answer(payload["assessment_id"], payload["question"]))
                return
            self._respond_json({"error": "Endpoint không tồn tại."}, HTTPStatus.NOT_FOUND)
        except (KeyError, ValueError, json.JSONDecodeError) as error:
            self._respond_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)


def run() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 8000), AppHandler)
    print("Track Advisor: http://127.0.0.1:8000")
    server.serve_forever()
