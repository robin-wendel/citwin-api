import subprocess
from pathlib import Path

import yaml


def update_settings(
        settings_template_input_path: Path,
        settings_output_path: Path,
        case_id: str,
        target_srid: int,
        bbox_str: str
) -> None:
    with open(settings_template_input_path, "r", encoding="utf-8") as f:
        settings = yaml.safe_load(f) or {}

    settings["global"]["case_id"] = case_id
    settings["global"]["target_srid"] = target_srid
    settings["import"]["bbox"] = bbox_str

    settings_output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(settings_output_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(settings, f, sort_keys=False, allow_unicode=True)


def run_netascore(netascore_dir: Path) -> None:
    cmd = ["docker", "compose", "run", "--rm", "netascore", "data/settings.yml"]
    subprocess.run(cmd, cwd=netascore_dir, check=True)
