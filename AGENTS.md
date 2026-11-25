# Repository instructions

- Read the [task tracker](docs/tasks.md) before making changes. Keep changes scoped to the task and flag decisions it depends on.
- Preserve the original course files, including notebook check cells. Put project code and tests in `src/` and `tests/`.
- Follow the [course AI rule](docs/tasks.md#ai-use).
- Follow the [test instructions](README.md#tests) to run the unit tests.
- Suggest documenting agreed simulator design decisions in project docs and recurring implementation conventions here. Suggest a skill when a multi-step workflow recurs.
- Record agreed simulator design decisions that affect multiple contributors in the project docs. Keep recurring coding and verification conventions in AGENTS.md.

## Style

- Keep docs and replies concise. Include what readers need to act, understand a decision, or verify the work.
- Document each instruction once and link to it where needed.
- Do not write unnecessary code comments. Add a comment only to explain reasoning or constraints that the code does not make clear.
- Start each project Python module with a short docstring describing its role. Give each class a concise description of its responsibility.
- Write gate matrices one row per line and put normalization factors beside the matrix or vector they scale.
- Give each test a short docstring explaining the behavior it verifies.
- In the final reply, summarize what changed, what you verified, and any open decisions or pending checks.
