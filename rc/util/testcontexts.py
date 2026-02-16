from contexts import ContextObject, apply_on_exception
from rc.util import eq, raises
from contextlib import contextmanager, nested


@contextmanager
def sixtysix():
    yield 66


@contextmanager
def doubleval():
    yield 1, 2


class Example(ContextObject):
    def __init__(self):
        self.contexts = [("s66", sixtysix())]


class BiggerExample(ContextObject):
    def __init__(self):
        self.contexts = [("s66", sixtysix()), ("one", "two", doubleval())]


def test_context_object():
    with Example() as e:
        eq(e.s66, 66)


def test_context_object_multiple_returns():
    with BiggerExample() as e2:
        eq(e2.s66, 66)
        eq(e2.one, 1)
        eq(e2.two, 2)


def test_exception_in_context_object():
    def zero_divider():
        with ContextObject():
            1 / 0

    raises(ZeroDivisionError, zero_divider)


def test_nested_exception_handled_properly():
    def zero_divider():
        with nested(ContextObject(), ContextObject()) as (a, b):
            1 / 0

    raises(ZeroDivisionError, zero_divider)


def test_exception_handler_context():
    hit = [False]

    class ExampleWithExceptionHandler(ContextObject):
        def __init__(self):
            self.hit = False
            self.contexts = [("exc_handler", apply_on_exception(self.do_hit))]

        def do_hit(self):
            hit[0] = True

    assert not hit[0]

    def diverge():
        with ExampleWithExceptionHandler():
            1 / 0

    raises(ZeroDivisionError, diverge)

    assert hit[0]
