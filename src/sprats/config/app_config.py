import json
from pathlib import Path
from typing import Any, Type, TypeVar

T = TypeVar("T", bound=Any)


class AppConfig:
    def __init__(self,
                 config_root_dir: Path,
                 init_data: dict[str, Any],
                 override_if_different_version: bool = False,
                 use_cache: bool = True):
        self.app_name_config_dir = config_root_dir
        self.config_file = self.app_name_config_dir / "config.json"
        self.use_cache = use_cache
        self.cached_json = None

        if not self.config_file.exists():
            self.config_file.write_text(json.dumps(init_data, indent=2))

        config_version_in_file = self.get_value("config_version", int)
        config_version_in_init = init_data.get("config_version")
        if (override_if_different_version and
                config_version_in_init is not None and
                config_version_in_file != config_version_in_init):
            self.config_file.write_text(json.dumps(init_data, indent=2))

    def get_json(self):
        if self.use_cache and self.cached_json is not None:
            return self.cached_json
        else:
            self.cached_json = json.loads(self.config_file.read_text())
            return self.cached_json

    def set_value(self, name: str, value: Any) -> None:
        data = self.get_json()
        if (isinstance(value, int) or isinstance(value, bool) or isinstance(value, float) or
                isinstance(value, list) or isinstance(value, dict)):
            data[name] = value
        else:
            data[name] = f"{value}"

        with self.config_file.open("w") as file:
            json.dump(data, file, indent=2)
            file.flush()

        self.cached_json = data

    def get_value(self, name: str, clazz: Type[T] = object) -> T | None:
        data = self.get_json()
        if name in data:
            value = data[name]
            if isinstance(value, clazz):
                return value
            else:
                raise RuntimeError(f"Value for key [{name}] is not an instance of {clazz.__name__}.")
        else:
            return None

    def get_by_xpath[T](self, xpath: str, clazz: Type[T] = object) -> T | None:
        names = [name for name in xpath.split("/") if name.strip() != ""]
        root_name = names[0]
        root_value = self.get_value(root_name)
        len_names = len(names)
        if len_names == 1:
            if isinstance(root_value, clazz):
                return root_value
            else:
                raise RuntimeError(f"Value for key [{xpath}] is not an instance of {clazz.__name__}.")

        if not isinstance(root_value, dict):
            return None
        else:
            value: dict = root_value
            for idx in range(1, len_names):
                value = value.get(names[idx])
                if value is None:
                    return None
                elif idx == len_names - 1:
                    if isinstance(value, clazz):
                        return value
                    elif clazz is float and isinstance(value, int):
                        return value * 1.0
                    else:
                        raise RuntimeError(f"Value for key [{xpath}] is not an instance of {clazz.__name__}.")
                elif not isinstance(value, dict):
                    return None

    def set_by_xpath(self, xpath: str, value: Any, raise_error_on_faile: bool = False) -> None:
        root_data = self.get_json()
        data = root_data

        names = [name for name in xpath.split("/") if name.strip() != ""]
        for name in names[:-1]:
            data = data.get(name)
            if data is None:
                if raise_error_on_faile:
                    raise RuntimeError(f"Xpath {xpath} not found in the data set")
                else:
                    return None
            elif not isinstance(data, dict):
                if raise_error_on_faile:
                    raise RuntimeError(f"Object associated with {xpath} is not a dict")
                else:
                    return None
        data[names[-1]] = value

        with self.config_file.open("w") as file:
            json.dump(root_data, file, indent=2)
            file.flush()

        self.cached_json = root_data
