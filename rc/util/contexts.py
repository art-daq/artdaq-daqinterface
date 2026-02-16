import contextlib


class ContextObject(object):
    """
    Create an object whose init method can define multiple contexts
    """

    def __init__(self):
        self.contexts = []

    def __enter__(self):
        for vec in self.contexts:
            context = vec[-1]
            names = vec[:-1]
            vals = context.__enter__()
            # Context managers can yield None, a single scalar value,
            # or a tuple of values:
            if vals is None:
                continue
            elif len(names) == 1:
                setattr(self, names[0], vals)
            else:
                assert len(vals) == len(names)
                for val, name in zip(vals, names):
                    setattr(self, name, val)

        return self

    def __exit__(self, *args):
        for vec in reversed(self.contexts):
            vec[-1].__exit__(*args)


@contextlib.contextmanager
def apply_on_exception(func=None):
    try:
        yield
    except:
        func()
