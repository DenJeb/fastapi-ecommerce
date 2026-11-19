import app.db.session
import app.models


def test_auth_tables_are_registered():
    table_names = set(app.db.session.Base.metadata.tables)
    assert {"users", "roles", "user_roles"} <= table_names


def test_user_has_required_columns():
    users = app.db.session.Base.metadata.tables["users"]
    assert "email" in users.columns
    assert "username" in users.columns
    assert "password_hash" in users.columns