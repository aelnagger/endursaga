# Agent Guidance

- Read [README.md](README.md) for the project goal and hardware overview.
- This is a Python `src/`-layout package. Keep package code under `src/endursaga/` and tests under `tests/`.
- Use `uv sync --group dev` to install the declared development dependencies, `uv run pytest` to run tests, and `uv build` to build the package. The project requires Python 3.15 or newer.
- Follow the existing `unittest.TestCase` test style; pytest discovers and runs these tests. Use fakes or mocks for camera and GPIO interactions so ordinary tests do not require Raspberry Pi hardware.
- Keep hardware-facing behavior injectable, following `CameraProtocol` and `MosfetPulseController` patterns. Avoid adding hardware setup to imports or tests that do not explicitly exercise it.
- `picamzero` is imported lazily for real camera captures and is not declared in `pyproject.toml`; do not assume it is available in the development environment.