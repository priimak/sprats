import re
import tempfile
from dataclasses import dataclass
from pathlib import Path

import pytest

from sprats.config import AppConfig


@dataclass
class Z:
    x1: str
    x2: str


@dataclass
class A:
    a: int
    b: bool
    c: str
    d: Z


def test_app_config():
    with tempfile.TemporaryDirectory() as tmpdir:
        config = AppConfig(Path(tmpdir), init_data={"config_version": 1})
        assert config.get_value("foobar") is None
        assert config.get_by_xpath("/foobar") is None
        assert config.get_value("config_version") == 1

        config.set_value("foobar", 1)
        assert config.get_value("foobar") == 1
        assert config.get_value("foobar", int) == 1
        assert isinstance(config.get_value("foobar"), int)
        assert isinstance(config.get_value("foobar", int), int)
        assert isinstance(config.get_value("foobar", float), float)
        assert config.get_by_xpath("/foobar", int) == 1
        with pytest.raises(ValueError, match=re.escape("Value for key [/foobar] is not an instance of str.")):
            config.get_by_xpath("/foobar", str)

        config.set_value("some_val", "my value")
        assert config.get_value("some_val") == "my value"

        with pytest.raises(ValueError, match="Key /db/x/config not found in the dataset"):
            config.set_by_xpath("/db/x/config", A(1, True, "AOne", Z("aaa", "bbb")), create_parents=False)

        config.set_by_xpath(
            "/db/x/config", A(1, True, "AOne", Z("aaa", "bbb")), create_parents=False, raise_error_on_failure=False
        )
        assert config.get_by_xpath("/db/x/config") is None

        config.set_by_xpath(
            "/db/x/config", A(1, True, "AOne", Z("aaa", "bbb")), create_parents=True, raise_error_on_failure=True
        )
        assert config.get_by_xpath("/db/x/config") is not None
        assert config.get_by_xpath("/db/x/config") == {"a": 1, "b": True, "c": "AOne", "d": {"x1": "aaa", "x2": "bbb"}}
        assert config.get_by_xpath("/db/x/config", A) == A(1, True, "AOne", Z("aaa", "bbb"))

        with pytest.raises(ValueError, match=re.escape("Missing key element [y] in /db/y/config")):
            config.get_by_xpath("/db/y/config", raise_error_on_missing_key=True)

        config.set_by_xpath("/db/y", 8)
        with pytest.raises(ValueError, match="Some part of /db/y/config is not a dict"):
            config.get_by_xpath("/db/y/config", raise_error_on_missing_key=True)

        with pytest.raises(ValueError, match="Object associated with /db/y/config is not a dict"):
            config.set_by_xpath("/db/y/config", 1, raise_error_on_failure=True, create_parents=False)

        with pytest.raises(ValueError, match=re.escape("Object associated with [y] in /db/y/config is not a dict")):
            config.set_by_xpath("/db/y/config", 1, raise_error_on_failure=True, create_parents=True)

        config.set_by_xpath("/db/y/config", 1, raise_error_on_failure=False, create_parents=True)

        with pytest.raises(ValueError, match="Some part of /db/y/config is not a dict"):
            config.get_by_xpath("/db/y/config", raise_error_on_missing_key=True)

        config.set_by_xpath("/db", None)
        assert config.get_by_xpath("/db/x/config") == None
        with pytest.raises(ValueError, match="/db is not a dict"):
            config.get_by_xpath("/db/x/config", raise_error_on_missing_key=True)

        config.set_value("A", A(1, True, "AOne", Z("aaa", "bbb")))
        assert config.get_value("A", A) == A(1, True, "AOne", Z("aaa", "bbb"))

        # reopen config
        config = AppConfig(Path(tmpdir), init_data={"config_version": 1})
        assert config.get_value("config_version") == 1
        assert config.get_value("A", A) == A(1, True, "AOne", Z("aaa", "bbb"))

        # reopen config with different version
        config = AppConfig(Path(tmpdir), init_data={"config_version": 2})
        assert config.get_value("config_version") == 1
        assert config.get_value("A", A) == A(1, True, "AOne", Z("aaa", "bbb"))

        # reopen config with different version and override
        config = AppConfig(Path(tmpdir), init_data={"config_version": 2}, override_if_different_version=True)
        assert config.get_value("config_version") == 2
        assert config.get_value("A", A) is None
