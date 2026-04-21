def test_import_app_factory() -> None:
    from app import create_app

    app = create_app()
    assert app is not None
