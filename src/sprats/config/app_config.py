import json
from pathlib import Path
from typing import Any, Type, TypeVar

T = TypeVar("T", bound = Any)


class AppConfig:
    def __init__(self, config_root_dir: Path, init_data: dict[str, Any]):
        self.app_name_config_dir = config_root_dir
        self.config_file = self.app_name_config_dir / "config.json"

        if not self.config_file.exists():
            self.config_file.write_text(json.dumps(init_data, indent = 2))

    def set_value(self, name: str, value: Any) -> None:
        data = json.loads(self.config_file.read_text())
        if (isinstance(value, int) or isinstance(value, bool) or isinstance(value, float) or
                isinstance(value, list) or isinstance(value, dict)):
            data[name] = value
        else:
            data[name] = f"{value}"
        self.config_file.write_text(json.dumps(data, indent = 2))

    def get_value(self, name: str, clazz: Type[T] = object) -> T | None:
        data = json.loads(self.config_file.read_text())
        if name in data:
            value = data[name]
            if isinstance(value, clazz):
                return value
            else:
                raise RuntimeError(f"Value for key [{name}] is not an instance of {clazz.__name__}.")
        else:
            return None