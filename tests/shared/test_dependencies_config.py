from pathlib import Path


def test_faststream_dependency_contains_cli_extra() -> None:
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")
    assert "faststream[cli,rabbit]" in pyproject
