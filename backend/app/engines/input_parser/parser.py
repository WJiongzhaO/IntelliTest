"""FR 1.0 input parsing engine.

Supports three input sources:
- CSV file upload (pandas)
- Plain text paste
- Direct form/structured input via API
"""

import io
import re

import pandas as pd

from app.utils.logger import setup_logger

logger = setup_logger(__name__)

TITLE_COLUMN_KEYWORDS = (
    "title",
    "name",
    "requirement_title",
    "requirement_name",
    "需求名",
    "需求名称",
    "标题",
    "名称",
)

TEXT_COLUMN_KEYWORDS = (
    "require",
    "desc",
    "text",
    "description",
    "content",
    "功能",
    "需求",
    "描述",
    "内容",
)


class ParseResult:
    """Normalized parse result. A list of raw requirement strings with metadata."""

    def __init__(self, items: list[dict]):
        self.items = items

    def __len__(self) -> int:
        return len(self.items)

    def __iter__(self):
        return iter(self.items)


def _column_matches(column: object, keywords: tuple[str, ...]) -> bool:
    lowered = str(column).strip().lower()
    return any(keyword in lowered for keyword in keywords)


def parse_csv(file_bytes: bytes, filename: str) -> ParseResult:
    """Parse a CSV file into individual requirement entries.

    Strategy:
      1. Read with pandas, sniffing delimiter and encoding.
      2. Look for title/name columns and requirement/description text columns.
      3. Each row becomes one raw requirement dict.
    """
    logger.info("Parsing CSV file: %s (%d bytes)", filename, len(file_bytes))

    try:
        df = pd.read_csv(io.BytesIO(file_bytes), dtype=str).fillna("")
    except Exception:
        df = pd.read_csv(
            io.BytesIO(file_bytes),
            dtype=str,
            encoding="utf-8-sig",
            sep=None,
            engine="python",
        ).fillna("")

    title_col_candidates = [
        c for c in df.columns if _column_matches(c, TITLE_COLUMN_KEYWORDS)
    ]
    text_col_candidates = [
        c for c in df.columns if _column_matches(c, TEXT_COLUMN_KEYWORDS)
    ]
    text_col_candidates = [c for c in text_col_candidates if c not in title_col_candidates]

    rows: list[dict] = []
    for i, (_, row) in enumerate(df.iterrows()):
        title = ""
        if title_col_candidates:
            title = str(row[title_col_candidates[0]]).strip()

        text = ""
        if text_col_candidates:
            text = " ".join(str(row[c]) for c in text_col_candidates if str(row[c]).strip())
        if not text:
            text = " ".join(str(v) for v in row.values if str(v).strip())
        if text.strip():
            rows.append(
                {
                    "index": i,
                    "title": title or None,
                    "raw_text": text.strip(),
                    "source_row": row.to_dict(),
                }
            )

    logger.info("CSV parsed: %d requirements extracted", len(rows))
    return ParseResult(rows)


def parse_text(text: str) -> ParseResult:
    """Parse freeform text into individual requirements.

    Splits on double-newline, numbered items, or bullet points.
    """
    logger.info("Parsing text input (%d chars)", len(text))

    text = text.strip()
    parts = re.split(r"\n\s*\n|\n(?=\d+[\.\)]\s)|(?<=\n)\s*[-*\u2022]\s", text)

    items: list[dict] = []
    for i, part in enumerate(parts):
        clean = part.strip()
        if clean and len(clean) > 3:
            items.append({"index": i, "raw_text": clean, "source_row": {}})

    if not items:
        items.append({"index": 0, "raw_text": text, "source_row": {}})

    logger.info("Text parsed: %d requirements extracted", len(items))
    return ParseResult(items)


def parse_form(data: list[dict]) -> ParseResult:
    """Accept pre-structured form input. Each dict must have a title and raw text."""
    logger.info("Parsing form input: %d entries", len(data))
    items: list[dict] = []
    for i, entry in enumerate(data):
        items.append(
            {
                "index": i,
                "title": entry.get("title"),
                "raw_text": entry.get("raw_text", entry.get("text", "")),
                "source_row": entry,
            }
        )
    return ParseResult(items)
