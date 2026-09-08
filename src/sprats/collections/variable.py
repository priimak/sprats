from collections.abc import Callable
from enum import Enum
from threading import Lock


class Variable[T]:
    """Container for a variable."""

    def __init__(
        self,
        value: T,
        serializer: Callable[[T], str] = lambda v: f"{v}",
        deserializer: Callable[[str], T] | None = None,
        valid_values: list[T] | None = None,
        on_value_change: Callable[[T | None], None] | None = None,
        name: str | None = None,
        clazz: type[object] | None = None,
        nullable: bool = True,
    ):
        self.__value: T | None = value
        self.__type = value.__class__ if clazz is None else clazz

        if value is None:
            if not nullable:
                raise ValueError("Value cannot be None")
        elif clazz is not None and not isinstance(value, clazz):
            raise TypeError(f"Value [{value}] is not an instance of {clazz}")

        self.__name = name
        self.__nullable = nullable
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

    @property
    def type(self):
        return self.__type

    def valid_values_str(self) -> list[str] | None:
        if self.valid_values is None:
            return None
        else:
            return [self.serializer(v) for v in self.valid_values]

    def __assign_value(self, value: T | None) -> tuple[T | None, bool]:
        if value is None and not self.__nullable:
            raise ValueError("Value cannot be None")

        with self.__lock:
            if not isinstance(value, self.__type) and (not self.__nullable or value is not None):
                raise TypeError()
            elif self.valid_values is not None and value not in self.__valid_values_set:
                raise ValueError(f"{value} is not in a list of valid values")
            elif self.__value != value:
                self.__value = value
                return self.__value, True
            else:
                return None, False

    @value.setter
    def value(self, value: T | None):
        assigned_value, is_changed = self.__assign_value(value)
        if is_changed:
            for callback in self.__on_value_change:
                callback(assigned_value)

    def str_value(self) -> str:
        return self.serializer(self.value)

    def set_value(self, value: T | None) -> None:
        self.value = value

    def set_from_str(self, txt: str) -> None:
        if self.deserializer is not None:
            self.value = self.deserializer(txt)
        else:
            match self.__value:
                case str():
                    self.value = txt
                case Enum():
                    if self.valid_values is None:
                        raise ValueError(
                            f"Please install custom deserialier for [{txt}] for Variable[{self.type.__name__}]"
                        )
                    else:
                        vals = [v for v in self.valid_values if str(v) == txt]
                        if vals != []:
                            self.value = vals[0]
                        else:
                            raise ValueError(f"Value [{txt}] is not in a list of valid values")
                case bool():
                    self.value = txt.strip().lower() == "true"
                case _:
                    self.value = self.__type(txt)
