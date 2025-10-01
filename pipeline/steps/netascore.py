import os
import subprocess
from pathlib import Path

import yaml

COMMANDS = {
    "conda": ["conda", "run", "-n", "netascore", "python", "generate_index.py", "data/settings.yml"],
    "docker": ["docker", "compose", "run", "--rm", "netascore", "data/settings.yml"],
}


def update_settings(settings_input_path: Path, settings_output_path: Path, target_srid: int, bbox_str: str) -> None:
    with open(settings_input_path, "r", encoding="utf-8") as f:
        settings = yaml.safe_load(f) or {}

    settings["global"]["target_srid"] = target_srid

    settings["database"]["host"] = os.getenv("DB_HOST")
    settings["database"]["port"] = int(os.getenv("DB_PORT"))
    settings["database"]["dbname"] = os.getenv("DB_NAME")
    settings["database"]["username"] = os.getenv("DB_USERNAME")
    settings["database"]["password"] = os.getenv("DB_PASSWORD")
    if not settings["database"]["password"]:
        del settings["database"]["password"]

    settings["import"]["bbox"] = bbox_str

    settings_output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(settings_output_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(settings, f, sort_keys=False, allow_unicode=True)


def run_netascore(netascore_dir: Path) -> None:
    cmd = COMMANDS[os.getenv("ENVIRONMENT_TYPE")]
    subprocess.run(cmd, cwd=netascore_dir, check=True)
