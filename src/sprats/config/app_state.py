import json
from pathlib import Path
from typing import Any, Optional


class AppState:
    def __init__(self, config_root_dir: Path):
        self.app_name_config_dir = config_root_dir
        self.__geometry_dir = self.app_name_config_dir / "geometry"

    def save_geometry(self, name: str, geometry: "QByteArray") -> None:
        from PySide6.QtCore import QByteArray
        self.__geometry_dir.mkdir(parents = True, exist_ok = True)
        geo_file = self.app_name_config_dir / "geometry" / f"{name}.json"
        data = {
            "geometry": geometry.toBase64(QByteArray.Base64Option.Base64Encoding).data().decode("utf-8")
        }
        geo_file.write_text(json.dumps(data, indent = 2))

    def get_geometry(self, name: str) -> Optional["QByteArray"]:
        from PySide6.QtCore import QByteArray
        geo_file = self.app_name_config_dir / "geometry" / f"{name}.json"
        if geo_file.exists():
            data = json.loads(geo_file.read_text())["geometry"].encode("utf-8")
            return QByteArray.fromBase64(data)
        else:
            return None

    def get_value(self, name: str, default_value: str | list[str] | None = None) -> str | list[str] | None:
        state_file = self.app_name_config_dir / "state.json"
        if not state_file.exists():
            state_file.write_text(json.dumps({}))

        data = json.loads(state_file.read_text())
        if name in data:
            return data[name]

        elif default_value is not None:
            # attempt to save default value
            data[name] = default_value
            state_file.write_text(json.dumps(data, indent = 2))

        return default_value

    def set_value(self, name: str, value: Any) -> None:
        state_file = self.app_name_config_dir / "state.json"
        if state_file.exists():
            data = json.loads(state_file.read_text())

            if isinstance(value, list) or isinstance(value, int) or isinstance(value, float) or isinstance(value, bool):
                data[name] = value
            else:
                data[name] = f"{value}"
            state_file.write_text(json.dumps(data, indent = 2))
        else:
            if isinstance(value, list) or isinstance(value, int) or isinstance(value, float) or isinstance(value, bool):
                state_file.write_text(json.dumps({name: value}, indent = 2))
            else:
                state_file.write_text(json.dumps({name: f"{value}"}, indent = 2))
