from enum import Enum
from threading import Lock, Thread
from time import sleep

import pytest

from sprats.collections import Variable


class A:
    def __eq__(self, value: object, /) -> bool:
        return isinstance(value, self.__class__)


class B(A):
    pass


class Color(Enum):
    RED = "red"
    GREEN = "green"
    BLUE = "blue"


def test_variable_basic():
    v = Variable(1)
    assert v.value == 1
    assert v.type == int
    v.set_from_str("2")
    assert v.value == 2

    v.value = None
    assert v.value is None

    with pytest.raises(TypeError):
        v.set_value(1.0)

    ab = Variable(B(), name="ab")
    assert ab.name == "ab"
    ab.value = B()
    assert ab.type == B

    with pytest.raises(TypeError):
        ab.set_value(A())

    ab = Variable[A](B(), name="ab", clazz=A, nullable=False)
    assert ab.type == A
    ab.value = A()

    with pytest.raises(ValueError):
        ab.value = None

    with pytest.raises(TypeError):
        ab.set_from_str("B")

    def str_to_clz(s: str) -> A:
        match s:
            case "A":
                return A()
            case "B":
                return B()
            case _:
                raise ValueError()

    ab = Variable[A](B(), name="ab", clazz=A, deserializer=str_to_clz)
    assert ab.value == B()
    ab.set_from_str("A")
    assert ab.type == A
    assert ab.value == A()
    ab.value = None

    with pytest.raises(TypeError):
        ab.value = 7


def test_variable_custom_serializer():
    """Test custom serializer function."""
    v = Variable(42, serializer=lambda v: f"VAL:{v}")
    assert v.str_value() == "VAL:42"
    # __repr__ uses the raw value, not the serializer
    assert repr(v) == "_: Variable[int] = 42"


def test_variable_valid_values():
    """Test valid_values parameter validation."""
    v = Variable(1, valid_values=[1, 2, 3])

    # Valid value
    v.value = 2
    assert v.value == 2

    # Invalid value
    with pytest.raises(ValueError, match="4 is not in a list of valid values"):
        v.value = 4

    # Test valid_values_str
    assert v.valid_values_str() == ["1", "2", "3"]

    # Test with custom serializer
    v2 = Variable(1, valid_values=[1, 2, 3], serializer=lambda v: f"NUM_{v}")
    assert v2.valid_values_str() == ["NUM_1", "NUM_2", "NUM_3"]

    # Test None valid_values
    v3 = Variable(1)
    assert v3.valid_values_str() is None


def test_variable_on_value_change_callback():
    """Test on_value_change callback."""
    callback_values = []

    v = Variable(1, on_value_change=callback_values.append)

    v.value = 2
    assert callback_values == [2]

    v.value = 3
    assert callback_values == [2, 3]

    # Setting same value should not trigger callback
    v.value = 3
    assert callback_values == [2, 3]

    # Setting to None
    v.value = None
    assert callback_values == [2, 3, None]


def test_variable_register_value_change_callback():
    """Test register_value_change_callback method."""
    callback_values = []

    v = Variable(1)
    v.register_value_change_callback(lambda val: callback_values.append(("cb1", val)))
    v.register_value_change_callback(lambda val: callback_values.append(("cb2", val)))

    v.value = 2
    assert callback_values == [("cb1", 2), ("cb2", 2)]


def test_variable_str_value():
    """Test str_value method."""
    v = Variable("hello")
    assert v.str_value() == "hello"

    v2 = Variable(42)
    assert v2.str_value() == "42"

    # With custom serializer
    v3 = Variable(42, serializer=lambda x: f"VAL:{x}")
    assert v3.str_value() == "VAL:42"


def test_variable_name_property():
    """Test name property."""
    v1 = Variable(1, name="my_var")
    assert v1.name == "my_var"

    v2 = Variable(1)
    assert v2.name is None


def test_variable_type_property():
    """Test type property."""
    v1 = Variable(42)
    assert v1.type == int

    v2 = Variable("hello", clazz=str)
    assert v2.type == str

    class MyClass:
        pass

    v3 = Variable(MyClass(), clazz=MyClass)
    assert v3.type == MyClass


def test_variable_repr():
    """Test __repr__ method."""
    v1 = Variable(42, name="answer")
    assert repr(v1) == "answer: Variable[int] = 42"

    v2 = Variable("hello", name="greeting")
    assert repr(v2) == 'greeting: Variable[str] = "hello"'

    v3 = Variable(None, name="empty")
    assert repr(v3) == "empty: Variable[NoneType] = None"

    v4 = Variable(3.14)
    assert repr(v4) == "_: Variable[float] = 3.14"


def test_variable_set_from_str_enum():
    """Test set_from_str with Enum values."""
    v = Variable(Color.RED, valid_values=list(Color))

    # str(Color.GREEN) returns "Color.GREEN", not "GREEN"
    v.set_from_str("Color.GREEN")
    assert v.value == Color.GREEN

    v.set_from_str("Color.BLUE")
    assert v.value == Color.BLUE

    with pytest.raises(ValueError, match="Value \\[Color.YELLOW\\] is not in a list of valid values"):
        v.set_from_str("Color.YELLOW")

    # Test without valid_values - should raise error
    v2 = Variable(Color.RED)
    with pytest.raises(ValueError, match="Please install custom deserialier"):
        v2.set_from_str("Color.GREEN")


def test_variable_set_from_str_bool():
    """Test set_from_str with boolean values."""
    v = Variable(True)

    v.set_from_str("true")
    assert v.value is True

    v.set_from_str("false")
    assert v.value is False

    v.set_from_str("True")
    assert v.value is True

    v.set_from_str("False")
    assert v.value is False

    v.set_from_str("TRUE")
    assert v.value is True

    v.set_from_str("  true  ")
    assert v.value is True


def test_variable_set_from_str_custom_type():
    """Test set_from_str with custom type construction."""

    class Point:
        def __init__(self, x: int, y: int):
            self.x = x
            self.y = y

        def __eq__(self, other: object, /) -> bool:
            return isinstance(other, Point) and self.x == other.x and self.y == other.y

        def __hash__(self):
            return hash((self.x, self.y))

        def __str__(self):
            return f"({self.x},{self.y})"

    # Point can be constructed from string "(1,2)" using a deserializer
    def point_deserializer(s: str) -> Point:
        # Parse "(1,2)" format
        s = s.strip("()")
        x, y = map(int, s.split(","))
        return Point(x, y)

    v = Variable(Point(0, 0), clazz=Point, deserializer=point_deserializer)
    v.set_from_str("(1,2)")
    assert v.value == Point(1, 2)

    # Test with valid_values
    valid_points = [Point(1, 1), Point(2, 2)]
    v2 = Variable(Point(1, 1), clazz=Point, valid_values=valid_points, deserializer=point_deserializer)
    v2.set_from_str("(2,2)")
    assert v2.value == Point(2, 2)

    with pytest.raises(ValueError, match=r"\(3,3\) is not in a list of valid values"):
        v2.set_from_str("(3,3)")


def test_variable_set_from_str_with_valid_values():
    """Test set_from_str with valid_values for non-enum types."""
    v = Variable(1, valid_values=[1, 2, 3])

    v.set_from_str("2")
    assert v.value == 2

    v.set_from_str("3")
    assert v.value == 3

    with pytest.raises(ValueError, match="4 is not in a list of valid values"):
        v.set_from_str("4")


def test_variable_deserializer_with_valid_values():
    """Test deserializer interaction with valid_values."""

    def custom_deserializer(s: str) -> int:
        return int(s) * 2

    v = Variable(2, deserializer=custom_deserializer, valid_values=[2, 4, 6])

    v.set_from_str("1")  # deserializer returns 2
    assert v.value == 2

    v.set_from_str("2")  # deserializer returns 4
    assert v.value == 4

    # deserializer returns 8, not in valid_values
    with pytest.raises(ValueError, match="8 is not in a list of valid values"):
        v.set_from_str("4")


def test_variable_nullable_false():
    """Test nullable=False parameter."""
    v = Variable(1, nullable=False)

    with pytest.raises(ValueError, match="Value cannot be None"):
        v.value = None

    with pytest.raises(ValueError, match="Value cannot be None"):
        Variable(None, nullable=False)


def test_variable_clazz_validation():
    """Test clazz parameter validation."""

    class Parent:
        pass

    class Child(Parent):
        pass

    class Unrelated:
        pass

    # Valid: value is instance of clazz
    v1 = Variable(Child(), clazz=Parent)
    assert v1.type == Parent

    # Invalid: value is not instance of clazz
    with pytest.raises(TypeError, match="is not an instance of"):
        Variable(Unrelated(), clazz=Parent)

    # Test with valid_values and clazz - use same instance
    child_instance = Child()
    valid_children = [child_instance]
    v2 = Variable(child_instance, clazz=Parent, valid_values=valid_children)
    assert v2.type == Parent


def test_variable_thread_safety():
    """Test thread safety of value assignment."""
    v = Variable(0)
    errors = []

    def increment():
        try:
            for _ in range(100):
                current = v.value
                sleep(0.0001)  # Small delay to increase chance of race condition
                v.value = current + 1
        except Exception as e:
            errors.append(e)

    threads = [Thread(target=increment) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0
    # Due to race conditions, final value may be less than 1000, but no errors
    assert v.value <= 1000
    assert v.value > 0


def test_variable_callback_thread_safety():
    """Test callback execution thread safety."""
    callback_values = []
    callback_lock = Lock()

    def callback(val):
        with callback_lock:
            callback_values.append(val)

    v = Variable(0, on_value_change=callback)

    def increment():
        for _ in range(50):
            v.value = v.value + 1
            sleep(0.0001)

    threads = [Thread(target=increment) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # All callbacks should have been called
    assert len(callback_values) == 250


def test_variable_edge_cases():
    """Test various edge cases."""
    # Test valid_values that doesn't include initial value
    with pytest.raises(ValueError, match="1 is not in a list of valid values"):
        Variable(1, valid_values=[2, 3])

    # Test valid_values copy behavior
    original_list = [1, 2, 3]
    v = Variable(1, valid_values=original_list)
    original_list.append(4)
    # Internal valid_values should not be affected by external modification
    assert v.valid_values == [1, 2, 3]

    # Test valid_values_str returns copy
    str_list = v.valid_values_str()
    str_list.append("modified")
    assert v.valid_values_str() == ["1", "2", "3"]


def test_variable_init_with_none_and_clazz():
    """Test initialization with None value and clazz specified."""

    class MyClass:
        pass

    v = Variable(None, clazz=MyClass, nullable=True)
    assert v.type == MyClass
    assert v.value is None

    # Should be able to set valid instance
    v.value = MyClass()
    assert isinstance(v.value, MyClass)


def test_variable_set_value_method():
    """Test set_value method."""
    v = Variable(1)
    v.set_value(2)
    assert v.value == 2

    v.set_value(None)
    assert v.value is None


def test_variable_set_from_str_string_type():
    """Test set_from_str when current value is a string."""
    # When value is a string and no deserializer, set_from_str should set the string directly
    v = Variable("hello")
    v.set_from_str("world")
    assert v.value == "world"

    # Test with valid_values
    v2 = Variable("hello", valid_values=["hello", "world", "test"])
    v2.set_from_str("world")
    assert v2.value == "world"

    with pytest.raises(ValueError, match="invalid is not in a list of valid values"):
        v2.set_from_str("invalid")
