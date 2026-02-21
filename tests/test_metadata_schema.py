from searchctl.metadata.db import _load_schema_sql


def test_load_schema_sql_contains_expected_tables() -> None:
    sql = _load_schema_sql()
    assert "CREATE TABLE IF NOT EXISTS meta" in sql
    assert "CREATE TABLE IF NOT EXISTS documents" in sql
