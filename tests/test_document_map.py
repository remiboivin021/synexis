from pathlib import Path

from searchctl.document_map import classify_document, infer_scope, map_boost, write_document_map


def test_infer_scope_from_path() -> None:
    assert infer_scope('/x/03_Projects/a.md') == 'projects'
    assert infer_scope('/x/05_Playbooks/a.md') == 'playbooks'
    assert infer_scope('/x/90_Dashboard/index.md') == 'dashboard'


def test_classify_document_active_markers() -> None:
    row = classify_document('/x/03_Projects/a.md', 'Project A', 'Projet en cours avec jalons')
    assert row['scope'] == 'projects'
    assert row['active'] is True


def test_write_document_map(tmp_path: Path) -> None:
    out = tmp_path / 'document_map.json'
    write_document_map([{'scope': 'projects', 'path': '/a', 'title': 'A', 'active': True, 'tags': []}], out)
    assert out.exists()


def test_map_boost_for_active_project_query() -> None:
    payload = {"doc_scope": "projects", "doc_active": True, "path": "/x/03_Projects/a.md"}
    assert map_boost(payload, "projets en cours") >= 0.06
