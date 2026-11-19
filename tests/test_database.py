import app.core.config


def test_tests_use_isolated_database():
    """防止 conftest 的环境变量失效后误连开发库"""
    assert app.core.config.settings.environment == "test"
    assert app.core.config.settings.db_name.endswith("_test")
    assert app.core.config.settings.debug is False