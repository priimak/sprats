from typing import Callable, Self


class Variable[T]:
    """ Container for a variable. """

    def __init__(
            self,
            value: T,
            serializer: Callable[[T], str] = lambda v: f"{v}",
            deserializer: Callable[[str], T] | None = None,
            valid_values: list[T] | None = None,
            on_value_change: Callable[[T], None] | None = None,
    ):
        self.__value = value
        self.__type = type(value)
        self.serializer = serializer
        self.deserializer = deserializer
        self.valid_values: list[T] | None = None if valid_values is None else valid_values.copy()
        self.__valid_values_set: set[T] | None = None if valid_values is None else set(valid_values)
        self.__on_value_change = [] if on_value_change is None else [on_value_change]
        if self.__valid_values_set is not None and self.__value not in self.__valid_values_set:
            raise ValueError(f"{value} is not in a list of valid values")

    def __repr__(self):
        return f"{self.__value}: Variable[{self.__type}]"

    def register_value_change_callback(self, callback: Callable[[T], None]):
        self.__on_value_change.append(callback)

    @property
    def value(self):
        return self.__value

    def valid_values_str(self) -> list[str] | None:
        if self.valid_values is None:
            return None
        else:
            return [self.serializer(v) for v in self.valid_values]

    @value.setter
    def value(self, value: T):
        if type(value) is not self.__type:
            raise TypeError()
        elif self.valid_values is not None and value not in self.__valid_values_set:
            raise ValueError(f"{value} is not in a list of valid values")
        elif self.__value != value:
            self.__value = value
            for callback in self.__on_value_change:
                callback(self.__value)

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
                    raise TypeError(
                        f"Unable to deserialize text into type {self.__type}"
                    )