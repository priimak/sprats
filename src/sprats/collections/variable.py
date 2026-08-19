from collections.abc import Callable
from threading import Lock


class Variable[T]:
    """Container for a variable."""

    def __init__(
        self,
        value: T,
        serializer: Callable[[T], str] = lambda v: f"{v}",
        deserializer: Callable[[str], T] | None = None,
        valid_values: list[T] | None = None,
        on_value_change: Callable[[T], None] | None = None,
        name: str | None = None,
    ):
        self.__value = value
        self.__type = type(value)
        self.__name = name
        self.serializer = serializer
        self.deserializer = deserializer
        self.valid_values: list[T] | None = None if valid_values is None else valid_values.copy()
        self.__valid_values_set: set[T] | None = None if valid_values is None else set(valid_values)
        self.__on_value_change = [] if on_value_change is None else [on_value_change]
        if self.__valid_values_set is not None and self.__value not in self.__valid_values_set:
            raise ValueError(f"{value} is not in a list of valid values")
        self.__lock = Lock()
        self.__repr_prefix = ("_" if self.__name is None else self.__name) + f": Variable[{self.__type.__name__}] = "

    def __repr__(self):
        return self.__repr_prefix + (f'"{self.value}"' if isinstance(self.value, str) else f"{self.value}")

    def register_value_change_callback(self, callback: Callable[[T], None]):
        self.__on_value_change.append(callback)

    @property
    def value(self):
        return self.__value

    @property
    def name(self):
        return self.__name

    def valid_values_str(self) -> list[str] | None:
        if self.valid_values is None:
            return None
        else:
            return [self.serializer(v) for v in self.valid_values]

    def __assign_value(self, value: T) -> T | None:
        with self.__lock:
            if type(value) is not self.__type:
                raise TypeError()
            elif self.valid_values is not None and value not in self.__valid_values_set:
                raise ValueError(f"{value} is not in a list of valid values")
            elif self.__value != value:
                self.__value = value
                return self.__value
            else:
                return None

    @value.setter
    def value(self, value: T):
        assigned_value = self.__assign_value(value)
        if assigned_value is not None:
            for callback in self.__on_value_change:
                callback(assigned_value)

    def str_value(self) -> str:
        return self.serializer(self.value)

    def set_value(self, value: T):
        self.value = value

    def set_from_str(self, txt: str):
        if self.deserializer is not None:
            self.value = self.deserializer(txt)
        else:
            match self.__value:
                case str():
                    self.value = txt
                case int():
                    self.value = int(txt)
                case _:
                    raise TypeError(f"Unable to deserialize text into type {self.__type}")
