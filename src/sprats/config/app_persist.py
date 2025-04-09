from pathlib import Path
from typing import Any

from sprats.config.app_config import AppConfig
from sprats.config.app_state import AppState


class AppPersistence:
    def __init__(
            self,
            app_name: str,
            init_config_data: dict[str, Any],
            config_base_dir: Path = Path.home(),
            override_config_if_different_version: bool = False
    ):
        config_root_dir = config_base_dir / f".{app_name}"
        config_root_dir.mkdir(parents=True, exist_ok=True)
        self.state = AppState(config_root_dir)
        self.config = AppConfig(config_root_dir, init_config_data, override_config_if_different_version)
