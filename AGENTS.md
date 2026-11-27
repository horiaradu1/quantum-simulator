# Repository instructions

- Read the [task tracker](docs/tasks.md) before making changes. Keep changes scoped to the task and flag decisions it depends on.
- Preserve the original course files, including notebook check cells. Put project code and tests in `src/` and `tests/`.
- Follow the [course AI rule](docs/tasks.md#ai-use).
- Place each test in the [quantum or application suite](README.md#tests) according to the behavior it verifies. Follow the linked instructions to run the tests.
- Suggest documenting agreed simulator design decisions in project docs and recurring implementation conventions here. Suggest a skill when a multi-step workflow recurs.
- Record agreed simulator design decisions that affect multiple contributors in the project docs. Keep recurring coding and verification conventions in AGENTS.md.

## Style

- Keep docs and replies concise. Include what readers need to act, understand a decision, or verify the work.
- Document each instruction once and link to it where needed.
- Write code that a reader can easily follow. Use descriptive names, keep control flow explicit, and break dense expressions into meaningful steps.
- Do not write unnecessary code comments. Add a comment only to explain reasoning or constraints that the code does not make clear.
- Start each project Python module with a short docstring describing its role. Give each class a concise description of its responsibility.
- Group code into Python modules by responsibility. Keep Qt widgets and event handling in `gui/` so simulation, editor state and file handling can run without Qt.
- Write gate matrices one row per line and put normalization factors beside the matrix or vector they scale.
- Give each test a short docstring explaining the behavior it verifies.
- Focus GUI tests on user workflows and specific regressions. Cover simple button clicks within a workflow when they affect its outcome.
- In the final reply, summarize what changed, what you verified, and any open decisions or pending checks.
