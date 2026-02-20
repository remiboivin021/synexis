from searchctl.llm_openrouter import build_openrouter_payload
from searchctl.prompts import SUMMARY_SYSTEM_PROMPT, build_summary_user_prompt


def test_summary_prompt_contains_structure_requirements() -> None:
    prompt = build_summary_user_prompt("positionnement freelance", [{"doc_title": "A", "snippet": "B"}])
    assert "Synthese" in prompt
    assert "Points cles" in prompt
    assert "Actions recommandees" in prompt


def test_openrouter_payload_shape() -> None:
    payload = build_openrouter_payload("openrouter/auto", "hello")
    assert payload["model"] == "openrouter/auto"
    assert payload["messages"][0]["role"] == "system"
    assert SUMMARY_SYSTEM_PROMPT in payload["messages"][0]["content"]
    assert payload["messages"][1]["content"] == "hello"
