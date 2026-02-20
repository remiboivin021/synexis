# STATE — OpenRouter Summary

Branch: feature/openrouter-summary  
Worktree: /home/comeg/workspace/synexis_brain/wt-openrouter-summary  
Planner: codex  
Executor: codex  

---

# Mission

Add OpenRouter as LLM provider and enable a human-readable summary for search results, ending with explicit sources.

---

# Feature Type

- [x] new feature  
- [ ] bug fix  
- [ ] refactor (approved)  
- [ ] performance improvement  
- [ ] infrastructure  
- [ ] security  

---

# Acceptance Criteria

- [ ] Config supports OpenRouter model/base_url/api key (additive).
- [ ] Search command can produce an LLM summary from retrieved results.
- [ ] Summary is human-readable in French.
- [ ] Summary always ends with a Sources section.
- [ ] A dedicated prompt template is used for formatting behavior.
- [ ] Existing JSON result behavior stays backward-compatible unless summary mode is requested.
- [ ] Tests cover prompt/rendering and payload construction.

---

# Scope Contract

## Allowed Areas

- src/searchctl/config.py
- src/searchctl/cli.py
- src/searchctl/* (new llm/prompt modules)
- config.yaml.example
- README.md
- tests/*
- STATE.openrouter-summary.md
- TODO.openrouter-summary.md
- DECISIONS.openrouter-summary.md

## Forbidden Areas

- .agents templates and skills
- governance policy files unrelated to this feature

---

# Blast Radius Assessment

- [ ] localized (single module)
- [x] multi-module
- [ ] cross-system
- [ ] unknown

---

# Architectural Constraints

Keep current CLI + local indexing architecture. No storage schema changes.

---

# Execution Plan (Planner Output)

1. Add OpenRouter provider config and prompt templates.
2. Add summarization path in `search` with explicit sources output.
3. Add tests + docs and verify.

