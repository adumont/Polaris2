from pathlib import Path

import yaml

from polaris2.models import Scenario


def save_scenario(scenario: Scenario, path: str | Path) -> None:
    data = scenario.model_dump()
    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)


def load_scenario(path: str | Path) -> Scenario:
    with open(path) as f:
        data = yaml.safe_load(f)
    return Scenario(**data)
