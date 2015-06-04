import unittest

from slip import Slip
from stack import ImmutableStack


def rect(start, end):
    ax, ay = start
    bx, by = end
    
    rect_set = set()

    for i in range(ax, bx+1):
        for j in range(ay, by+1):
            rect_set.add((i, j))

    return rect_set


class TestSlip(unittest.TestCase):
    def test_literal(self):
        slip = Slip("a", "n")
        self.assertEqual(slip.match("abca"), 2)


    def test_multiple_runs(self):
        slip = Slip("a", "n")
        self.assertEqual(slip.match("abca"), 2)
        self.assertEqual(slip.match("aaaa"), 4)
        self.assertEqual(slip.match("aa"), 2)
        self.assertEqual(slip.match(""), 0)


    def test_asterisk(self):
        slip = Slip("a*")
        self.assertEqual(slip.match("aaab"), [((0, 0), rect((0, 0), (2, 0))),
                                              ((1, 0), rect((1, 0), (2, 0))),
                                              ((2, 0), rect((2, 0), (2, 0))),
                                              ((3, 0), set())])

    def test_plus(self):
        slip = Slip("a+")
        self.assertEqual(slip.match("aaab"), [((0, 0), rect((0, 0), (2, 0))),
                                              ((1, 0), rect((1, 0), (2, 0))),
                                              ((2, 0), rect((2, 0), (2, 0)))])


    def test_backtracking(self):
        slip = Slip("a+ab")
        self.assertEqual(slip.match("aaab"), [((0, 0), rect((0, 0), (3, 0))),
                                              ((1, 0), rect((1, 0), (3, 0)))])


    def test_backtracking_fail(self):
        slip = Slip("a+ab")
        self.assertEqual(slip.match("aaaaaa"), [])


    def test_escape(self):
        slip = Slip("ab`.```/c", "n")
        self.assertEqual(slip.match("ab`.```/c"), 0)
        self.assertEqual(slip.match("ab.`/c"), 1)


    def test_charclass(self):
        slip = Slip("[a-e]", "n")
        self.assertEqual(slip.match("abcdefghijklmnopqrstuvwxyz"), 5)
        self.assertEqual(slip.match("equator"), 2)


    def test_rotate_left(self):
        # ..e
        # ..d
        # abc
        
        slip = Slip("abc<de")
        self.assertEqual(slip.match("..e\n..d\nabc"),
                         [((0, 2), {(0, 2), (1, 2), (2, 2), (2, 1), (2, 0)})])

    def test_rotate_left(self):
        # abc
        # ..d
        # ..e
        
        slip = Slip("abc>de")
        self.assertEqual(slip.match("abc\n..d\n..e"),
                         [((0, 0), {(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)})])


    def test_slip_right(self):
        slip = Slip("(?|abc)\def", "n")
        self.assertEqual(slip.match("abc\ndef"), 1)


    def test_slip_left(self):
        slip = Slip("(?|abc)/def", "n")
        self.assertEqual(slip.match("def\nabc"), 1)


    def test_padding(self):
        slip = Slip("abc>.>ed", "gn")
        self.assertEqual(slip.match("abc\nde"), 1)


    @unittest.skip("Non-capturing bug")
    def test_noncapturing(self):
        slip = Slip("(?:(a)bc)(?_(1).*)")
        self.assertEqual(slip.match("pabce"), [((1, 0), rect((1, 0), (4, 0)))])

    # Similarly for recursion

class TestStack(unittest.TestCase):
    def test_push(self):
        stack = ImmutableStack()
        stack.push(1)
        stack.push(2)
        stack.push(3)

        self.assertEqual(stack.listify(), [1, 2, 3])


    def test_pop(self):
        stack = ImmutableStack()
        stack.push(1)
        stack.push(2)
        self.assertEqual(stack.listify(), [1, 2])

        stack.pop()
        self.assertEqual(stack.listify(), [1])

        stack.push(3)
        stack.push(2)
        self.assertEqual(stack.listify(), [1, 3, 2])
        

if __name__ == "__main__":
    unittest.main()
