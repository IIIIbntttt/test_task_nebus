from app import create_app


def test_fastapi_app_has_dishka_container() -> None:
    app = create_app()
    assert hasattr(app.state, "dishka_container")
