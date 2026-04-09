---
version: "0.1.1"
level: copilot
processes:
  design: copilot
  implementation: copilot
  testing: copilot
  documentation: pair
  review: assist
---

## Notes

This repository was developed with significant AI assistance using the pi coding agent.

### AI-Assisted Work

**Design & Architecture:**

- Test modularization architecture and planning
- Infrastructure design for transport-agnostic testing
- CI/CD workflow design

**Implementation:**

- Test infrastructure code (fixtures, abstract clients)
- Documentation updates
- Script improvements (test_stdio.sh, test_local.sh)

**Testing:**

- Test structure and patterns
- Test lifecycle implementations
- Integration test workflows

**Documentation:**

- README.md updates (human-led, AI-assisted)
- tests/README.md restructuring (human-led, AI-assisted)
- CONTRIBUTING.md updates (human-led, AI-assisted)
- AGENTS.md creation (AI-generated with human review)

### Human Contributions

- All architectural decisions and approvals
- Code review and validation
- Testing strategy definition
- Documentation structure and content review
- Final implementation decisions

### Tools Used

- pi coding agent (mariozechner/pi-coding-agent)
  - via OpenWebUI for API access to models
    - llama.cpp server hosting a variety of models from:
      - Qwen3.5 family
- LLM-assisted code generation and documentation

### Verification

AI-generated code has been reviewed and tested by human contributors. All AI assistance was transparent and documented.
