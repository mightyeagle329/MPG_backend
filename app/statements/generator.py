from pathlib import Path

import yaml

DEFAULT_TEMPLATES_PATH = Path(__file__).parent / "templates.yaml"


class StatementGenerator:
    def __init__(self, templates_path: Path = DEFAULT_TEMPLATES_PATH):
        self._templates_path = templates_path
        self._templates = self._load()

    def _load(self) -> list[str]:
        data = yaml.safe_load(self._templates_path.read_text())
        return list(data.get("statements", []))

    def generate(self, variables: dict) -> list[str]:
        return [template.format(**variables) for template in self._templates]


statement_generator = StatementGenerator()
