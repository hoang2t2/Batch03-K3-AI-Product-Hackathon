from __future__ import annotations

import json
from pathlib import Path

from track_advisor.domain.models import Track


def load_catalogue(tracks_path: Path, lessons_path: Path) -> list[Track]:
    raw_tracks = json.loads(tracks_path.read_text(encoding="utf-8"))
    lessons = json.loads(lessons_path.read_text(encoding="utf-8"))["lessons"]
    tracks = [Track(
        id=track_id,
        name=track["name"],
        summary=track["description"],
        lesson_weights={lesson_id: lesson["weight"][track_id] for lesson_id, lesson in lessons.items()},
        lesson_metadata={lesson_id: {"title": lesson["title"], "skills": lesson["skills"]} for lesson_id, lesson in lessons.items()},
        focus=track["focus"],
        ideal_profile=track["ideal_profile"],
        important_lessons=track["important_lessons"],
        evaluation_guideline=track["evaluation_guideline"],
    ) for track_id, track in raw_tracks.items()]
    if len(tracks) != 3 or len({track.id for track in tracks}) != 3:
        raise ValueError("Catalogue phải có đúng ba track với ID riêng biệt.")
    lesson_ids = set(lessons)
    for track in tracks:
        if set(track.lesson_weights) != lesson_ids or sum(track.lesson_weights.values()) <= 0:
            raise ValueError(f"Weight của track {track.id} không phủ đúng toàn bộ lesson.")
        if not set(track.important_lessons).issubset(lesson_ids):
            raise ValueError(f"important_lessons của track {track.id} chứa lesson không tồn tại.")
    return tracks
