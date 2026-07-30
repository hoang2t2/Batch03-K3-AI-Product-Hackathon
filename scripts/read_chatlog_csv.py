#!/usr/bin/env python3
"""Đọc và kiểm tra nhanh chatlog CSV của hackathon.

Mặc định script chỉ in thống kê để tránh hiển thị lại nội dung hội thoại thật.
Thêm --preview khi cần kiểm tra một vài dòng đã được rút gọn.
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path


DEFAULT_CSV = Path("data/vlearn-pack/chatlog/chat_history_anonymized_for_hackathon.csv")
REQUIRED_COLUMNS = {"conversation_id", "turn_id", "role", "content"}


def shorten(value: str, max_length: int = 120) -> str:
    """Gộp xuống một dòng và giới hạn độ dài trước khi in ra terminal."""
    compact = " ".join(value.split())
    return compact if len(compact) <= max_length else f"{compact[:max_length - 1]}…"


def read_rows(csv_path: Path) -> tuple[list[str], list[dict[str, str]]]:
    """Đọc CSV có BOM hoặc UTF-8 thường và trả về header cùng các dòng dữ liệu."""
    with csv_path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames is None:
            raise ValueError("CSV không có hàng header.")

        missing = REQUIRED_COLUMNS - set(reader.fieldnames)
        if missing:
            names = ", ".join(sorted(missing))
            raise ValueError(f"CSV thiếu cột bắt buộc: {names}")

        return reader.fieldnames, list(reader)


def print_summary(columns: list[str], rows: list[dict[str, str]]) -> None:
    roles = Counter(row["role"] for row in rows)
    conversations = {row["conversation_id"] for row in rows}
    turns = {row["turn_id"] for row in rows}
    empty_content = sum(not row["content"].strip() for row in rows)

    print(f"Số cột: {len(columns)}")
    print(f"Số dòng: {len(rows)}")
    print(f"Số hội thoại: {len(conversations)}")
    print(f"Số turn: {len(turns)}")
    print(f"Role: {dict(sorted(roles.items()))}")
    print(f"Nội dung rỗng: {empty_content}")


def print_preview(rows: list[dict[str, str]], limit: int) -> None:
    print("\nPreview (content đã rút gọn):")
    for index, row in enumerate(rows[:limit], start=1):
        print(
            f"{index}. {row['conversation_id']} | {row['turn_id']} | "
            f"{row['role']}: {shorten(row['content'])}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Đọc chatlog CSV của hackathon")
    parser.add_argument(
        "csv_path",
        nargs="?",
        type=Path,
        default=DEFAULT_CSV,
        help=f"Đường dẫn CSV (mặc định: {DEFAULT_CSV})",
    )
    parser.add_argument(
        "--preview",
        type=int,
        metavar="N",
        help="In tối đa N dòng đầu, với content được rút gọn",
    )
    args = parser.parse_args()

    if not args.csv_path.is_file():
        parser.error(f"Không tìm thấy file: {args.csv_path}")
    if args.preview is not None and args.preview < 1:
        parser.error("--preview phải là số nguyên dương")

    columns, rows = read_rows(args.csv_path)
    print(f"File: {args.csv_path}")
    print_summary(columns, rows)

    if args.preview:
        print_preview(rows, args.preview)


if __name__ == "__main__":
    main()
