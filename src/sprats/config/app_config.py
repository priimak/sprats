import json
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, TypeVar

from pydantic import TypeAdapter

T = TypeVar("T", bound=Any)


class AppConfig:
    def __init__(
        self,
        config_root_dir: Path,
        init_data: dict[str, Any],
        override_if_different_version: bool = False,
        use_cache: bool = True,
    ):
        self.app_name_config_dir = config_root_dir
        self.config_file = self.app_name_config_dir / "config.json"
        self.use_cache = use_cache
        self.cached_json = None

        if not self.config_file.exists():
            self.config_file.write_text(json.dumps(init_data, indent=2))

        config_version_in_file = self.get_value("config_version", int)
        config_version_in_init = init_data.get("config_version")
        if (
            override_if_different_version
            and config_version_in_init is not None
            and config_version_in_file != config_version_in_init
        ):
            self.config_file.write_text(json.dumps(init_data, indent=2))
            self.cached_json = None

    def get_json(self):
        if self.use_cache and self.cached_json is not None:
            return self.cached_json
        else:
            self.cached_json = json.loads(self.config_file.read_text())
            return self.cached_json

    def set_value(self, name: str, value: Any) -> None:
        data = self.get_json()
        if (
            isinstance(value, int)
            or isinstance(value, bool)
            or isinstance(value, float)
            or isinstance(value, list)
            or isinstance(value, dict)
        ):
            data[name] = value
        else:
            data[name] = asdict(value) if is_dataclass(value) else f"{value}"

        with self.config_file.open("w") as file:
            json.dump(data, file, indent=2)
            file.flush()

        self.cached_json = data

    def __deserialize_value(self, value: Any, key: str, clazz: type[T] = object) -> T | None:
        if isinstance(value, clazz):
            return value
        elif isinstance(value, int) and clazz is float:
            # upscale to float
            return float(value)
        elif is_dataclass(clazz) and isinstance(value, dict):
            return TypeAdapter(clazz).validate_python(value)
        else:
            raise ValueError(f"Value for key [{key}] is not an instance of {clazz.__name__}.")

    def get_value(self, name: str, clazz: type[T] = object) -> T | None:
        data = self.get_json()
        return self.__deserialize_value(data[name], name, clazz) if name in data else None

    def get_by_xpath[T](
        self, xpath: str, clazz: type[T] = object, raise_error_on_missing_key: bool = False
    ) -> T | None:
        names = [name for name in xpath.split("/") if name.strip() != ""]
        root_name = names[0]
        root_value = self.get_value(root_name)
        len_names = len(names)
        if len_names == 1:
            return self.__deserialize_value(root_value, xpath, clazz)

        elif not isinstance(root_value, dict):
            if raise_error_on_missing_key:
                raise ValueError(f"/{root_name} is not a dict")
            else:
                return None

        else:
            value: dict | None = root_value
            for idx in range(1, len_names):
                if raise_error_on_missing_key and names[idx] not in value:
                    raise ValueError(f"Missing key element [{names[idx]}] in {xpath}")
                value = value.get(names[idx])
                if value is None:
                    return None
                elif idx == len_names - 1:
                    return self.__deserialize_value(value, xpath, clazz)
                elif not isinstance(value, dict):
                    if raise_error_on_missing_key:
                        raise ValueError(f"Some part of {xpath} is not a dict")
                    else:
                        return None
        return None

    def set_by_xpath(
        self, xpath: str, value: Any, raise_error_on_failure: bool = True, create_parents: bool = True
    ) -> None:
        root_data = self.get_json()
        data = root_data

        names = [name for name in xpath.split("/") if name.strip() != ""]
        if create_parents:
            for name in names[:-1]:
                if name not in data:
                    data[name] = {}
                data = data[name]
                if not isinstance(data, dict) and raise_error_on_failure:
                    raise ValueError(f"Object associated with [{name}] in {xpath} is not a dict")

            if (data is None or not isinstance(data, dict)) and not raise_error_on_failure:
                return
            elif names[-1] not in data:
                data[names[-1]] = None
            data = root_data

        for name in names[:-1]:
            if data.get(name) is None or name not in data:
                if raise_error_on_failure:
                    raise ValueError(f"Key {xpath} not found in the dataset")
                else:
                    return

            data = data.get(name)
            if not isinstance(data, dict):
                if raise_error_on_failure:
                    raise ValueError(f"Object associated with {xpath} is not a dict")
                else:
                    return

        data[names[-1]] = asdict(value) if is_dataclass(value) else value
        data_out = json.dumps(root_data, indent=2)
        self.config_file.write_text(data_out)
        self.cached_json = root_data
