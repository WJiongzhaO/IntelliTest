"""Tests for requirement title parsing."""

from app.engines.input_parser.parser import parse_csv, parse_form


def test_parse_form_preserves_requirement_title() -> None:
    parsed = list(
        parse_form(
            [
                {
                    "title": "Login requirement",
                    "raw_text": "User logs in with valid credentials.",
                }
            ]
        )
    )

    assert parsed == [
        {
            "index": 0,
            "title": "Login requirement",
            "raw_text": "User logs in with valid credentials.",
            "source_row": {
                "title": "Login requirement",
                "raw_text": "User logs in with valid credentials.",
            },
        }
    ]


def test_parse_csv_splits_title_from_requirement_text() -> None:
    content = (
        "title,requirement\n"
        "Login requirement,User logs in with valid credentials.\n"
    ).encode("utf-8")

    parsed = list(parse_csv(content, "requirements.csv"))

    assert len(parsed) == 1
    assert parsed[0]["title"] == "Login requirement"
    assert parsed[0]["raw_text"] == "User logs in with valid credentials."
