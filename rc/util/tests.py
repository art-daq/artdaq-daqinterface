from datetime import datetime
from rc.util import eq, andn, orn, gt, raises, stringify_times, convert_to_time


def test_andn():
    eq(False, andn(True, False, True))
    eq(True, andn(True, True, True))
    eq(False, andn(True, False))
    eq(False, andn(False, False))
    eq(True, andn(True, True))
    eq(True, andn(*[True for _ in range(1000)]))
    eq(True, andn(True))
    eq(True, andn())


def test_orn():
    eq(True, orn(True, False, True))


def test_gt():
    gt(1, 0)
    raises(AssertionError, gt, 0, 1)


def test_stringify_times():
    st = stringify_times
    # Dicts
    eq({}, st({}))
    eq({"a": 1}, st({"a": 1}))
    eq({"t": "2010-01-01 02:03:04.555555"},
       st({"t": datetime(2010, 1, 1,
                         2, 3, 4, 555555)}))
    eq({"nested": {"t": "2010-01-01 02:03:04.555555"}},
       st({"nested": {"t": datetime(2010, 1, 1,
                                    2, 3, 4, 555555)}}))

    # Tuples
    eq((), st(()))
    eq(("a", 1), st(("a", 1)))
    eq(("t", "2010-01-01 02:03:04.555555"),
       st(("t", datetime(2010, 1, 1,
                         2, 3, 4, 555555))))

def test_convert_to_time():
    time1 = '2015-10-29 19:00:21'
    time2 = '2015-10-30 14:26:32.10'
    dt1 = convert_to_time(time1)
    dt2 = convert_to_time(time2)

