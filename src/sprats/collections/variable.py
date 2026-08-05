from typing import Callable


class Variable[T]:
    """ Container for a variable. """

    def __init__(
        self,
        value: T,
        deserializer: Callable[[str], T] | None = None,
        valid_values: list[T] | None = None,
        on_value_change: Callable[[T], None] | None = None,
    ):
        self.__value = value
        self.__type = type(value)
        self.__deserializer = deserializer
        self.valid_values: list[T] | None = None if valid_values is None else valid_values.copy()
        self.__valid_values_set: set[T] | None = None if valid_values is None else set(valid_values)
        self.__on_value_change = on_value_change

    def __repr__(self):
        return f"{self.__value}: Variable[{self.__type}]"

    @property
    def value(self):
        return self.__value

    @value.setter
    def value(self, value: T):
        if type(value) is not self.__type:
            raise TypeError()
        elif self.valid_values is not None and value not in self.__valid_values_set:
            raise ValueError(f"{value} is not in a list of valid values")
        elif self.__value != value:
            self.__value = value
            self.__on_value_change(self.__value)

    def set_value(self, value: T):
        self.value = value

    def set_from_str(self, txt: str):
        if self.__deserializer is not None:
            self.value = self.__deserializer(txt)
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