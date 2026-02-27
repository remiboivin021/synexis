from pathlib import Path

from searchctl.config import load_config


def test_load_config_default_llm(tmp_path: Path) -> None:
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text("roots: []\n", encoding="utf-8")
    cfg = load_config(cfg_file)
    assert cfg.llm.provider == "openrouter"
    assert cfg.llm.base_url.startswith("https://openrouter.ai")
    assert cfg.llm.strict_grounding is True


def test_load_config_custom_llm_model(tmp_path: Path) -> None:
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text(
        "\n".join(
            [
                "roots: []",
                "qdrant:",
                "  url: http://localhost:6333",
                "  collection_name: personal_chunks_v1",
                "  vector_size: 384",
                "  distance: Cosine",
                "llm:",
                "  provider: openrouter",
                "  base_url: https://openrouter.ai/api/v1",
                "  model: openrouter/anthropic/claude-3.5-sonnet",
                "  api_key: test-key",
                "  strict_grounding: false",
            ]
        ),
        encoding="utf-8",
    )
    cfg = load_config(cfg_file)
    assert cfg.llm.model.endswith("claude-3.5-sonnet")
    assert cfg.llm.api_key == "test-key"
    assert cfg.llm.strict_grounding is False
