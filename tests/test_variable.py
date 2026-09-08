import pytest

from sprats.collections import Variable


class A:
    def __eq__(self, value: object, /) -> bool:
        return isinstance(value, self.__class__)


class B(A):
    pass


def test_variable():
    v = Variable(1)
    assert v.value == 1
    assert v.type == int
    v.set_from_str("2")
    assert v.value == 2

    with pytest.raises(TypeError):
        v.set_value(1.0)

    ab = Variable(B(), name="ab")
    assert ab.name == "ab"
    ab.value = B()
    assert ab.type == B

    with pytest.raises(TypeError):
        ab.set_value(A())

    ab = Variable[A](B(), name="ab", clazz=A)
    assert ab.type == A
    ab.value = A()

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
