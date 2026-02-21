# STATE — Web UI Interaction

Branch: feature/web-ui  
Worktree: /tmp/wt-web-ui  
Planner: codex  
Executor: codex  

---

# Mission

Add a local web interface that lets users search indexed content, request synthesis answers, browse indexed Markdown/text documents, and read document content from the browser.

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

- [ ] A new CLI command starts a local web server for Synexis interaction.
- [ ] The web UI allows running search queries and displays ranked results with citations.
- [ ] The web UI allows requesting a synthesis using existing summarize logic.
- [ ] The web UI allows listing indexed documents and opening Markdown/text content.
- [ ] Server defaults to localhost binding and rejects remote bind unless explicitly allowed by flag.
- [ ] New tests cover critical web module behavior and pass locally.
- [ ] README documents how to start and use the web UI.

---

# Scope Contract

## Allowed Areas

- src/searchctl/cli.py
- src/searchctl/web.py
- tests/test_web.py
- README.md
- docs/governance/adr/ADR-0002-local-web-ui-surface.md
- STATE.web-ui.md
- TODO.web-ui.md
- DECISIONS.web-ui.md

## Forbidden Areas

- `.agents/` templates and skills
- storage schemas and metadata SQL
- chunking/hash/scoring logic
- connector capabilities and trust model outside local web serving
- unrelated refactors

---

# Blast Radius Assessment

- [ ] localized (single module)  
- [x] multi-module  
- [ ] cross-system  
- [ ] unknown  

---

# Architectural Constraints

- Reuse existing search/summarize behavior; no changes to retrieval formula.
- No new runtime dependencies for web serving.
- Keep network exposure minimal and explicit (localhost by default).
- Keep changes additive and backward-compatible for CLI users.

---

# Parallel Safety Check

- Active sibling worktrees exist, but this feature touches only `feature/web-ui` branch/worktree and does not modify shared schemas/contracts.

---

# Execution Plan (Planner Output)

1. Add web serving module and CLI command with localhost-default safety (done when server starts and endpoints respond).
2. Add tests for web module safety and helper behavior (done when targeted pytest passes).
3. Update documentation and ADR for the new local HTTP interaction surface (done when README + ADR are committed).

---

# Refactor Shield

No opportunistic refactor outside web feature files.

---

# Security Surface Check

Touches network exposure and untrusted HTTP input. Security gate is mandatory.

---

# Definition of Done

All acceptance criteria above are checked and targeted tests pass.
