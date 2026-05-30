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
    assert parsed[0]["external_id"] is None


def test_parse_csv_preserves_external_id_column() -> None:
    content = (
        "ID,title,requirement\n"
        "LR-001,Valid login,User logs in with valid credentials.\n"
    ).encode("utf-8")

    parsed = list(parse_csv(content, "login_requirements.csv"))

    assert len(parsed) == 1
    assert parsed[0]["external_id"] == "LR-001"
    assert parsed[0]["title"] == "Valid login"
    assert "LR-001" not in parsed[0]["raw_text"]


def test_parse_csv_extracts_module_column() -> None:
    content = (
        "ID,Module,title,requirement\n"
        "AUTH-001,用户登录与会话,Successful login,POST /rest/user/login.\n"
    ).encode("utf-8")

    parsed = list(parse_csv(content, "juice_shop_requirements.csv"))

    assert len(parsed) == 1
    assert parsed[0]["external_id"] == "AUTH-001"
    assert parsed[0]["module"] == "用户登录与会话"
    assert parsed[0]["title"] == "Successful login"
    assert parsed[0]["raw_text"] == "POST /rest/user/login."
    assert "用户登录与会话" not in parsed[0]["raw_text"]
