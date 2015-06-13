from textwrap import dedent
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


    def test_charclass(self):
        slip = Slip("[abcd]", "n")
        self.assertEqual(slip.match("abacus"), 4)
        self.assertEqual(slip.match("zyzzyva", 1))

        slip = Slip("[^abcd]", "n")
        self.assertEqual(slip.match("abacus"), 2)
        self.assertEqual(slip.match("zyzzyva", 6))

        slip = Slip("[b-z|eiouy]", "n")
        self.assertEqual(slip.match("abacus"), 3)
        self.assertEqual(slip.match("zyzzyva", 4))

        slip = Slip("`y", "n")
        self.assertEqual(slip.match("abacus"), 3)
        self.assertEqual(slip.match("zyzzyva", 4))


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
        slip = Slip("abc<de")
        data = dedent("""\
                      ..e
                      ..d
                      abc""")
        
        print(repr(data))
        
        self.assertEqual(slip.match(data),
                         [((0, 2), {(0, 2), (1, 2), (2, 2), (2, 1), (2, 0)})])

    def test_rotate_left(self):
        slip = Slip("abc>de")
        data = dedent("""\
                      abc
                      ..d
                      ..e""")
        
        self.assertEqual(slip.match(data),
                         [((0, 0), {(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)})])


    def test_slip_right(self):
        slip = Slip("(?|abc)\def", "n")
        self.assertEqual(slip.match("abc\ndef"), 1)


    def test_slip_left(self):
        slip = Slip("(?|abc)/def", "n")        
        self.assertEqual(slip.match("def\nabc"), 1)


    def test_directions(self):
        data = dedent("""\
                      c c c
                       bbb
                        a""")

        self.assertEqual(Slip("^0abc", "no").match(data), 1)
        self.assertEqual(Slip("^1abc", "no").match(data), 1)
        self.assertEqual(Slip("^2abc", "no").match(data), 0)
        self.assertEqual(Slip("^6abc", "no").match(data), 0)
        self.assertEqual(Slip("^7abc", "no").match(data), 1)

        self.assertEqual(Slip("^*abc", "no").match(data), 3)
        self.assertEqual(Slip("^xabc", "no").match(data), 2)
        self.assertEqual(Slip("^+abc", "no").match(data), 1)


    @unittest.skip("Non-capturing bug")
    def test_noncapturing(self):
        slip = Slip("(?:(a)bc)(?_(1).*)")
        self.assertEqual(slip.match("pabce"), [((1, 0), rect((1, 0), (4, 0)))])


    # Todo: Check against Regex101
    @unittest.skip("Recursion capturing bug")
    def test_recursion_groups(self):
        slip = Slip("$6((a+)(?_(2)b+))(?1)(?_(2)c+)$2", "n")
        self.assertEqual(slip.match("aaabbbabc"), 0)
        self.assertEqual(slip.match("aaabbbabccc"), 1)


class TestSlipFlags(unittest.TestCase):
    def test_padding(self):
        slip = Slip("abc>.>ed", "gn")
        self.assertEqual(slip.match("abc\nde"), 1)


    def test_wrapping(self):
        slip = Slip("abc", "w")
        self.assertEqual(slip.match("bca"), [((2, 0), rect((0, 0), (2, 0)))])


    def test_overlapping(self):
        slip = Slip(">?aba", "n")
        slip_overlapping = Slip(">?aba", "on")
        data = dedent("""\
                      aba
                      b..
                      a..""")
        
        self.assertEqual(slip.match(data), 1)
        self.assertEqual(slip_overlapping.match(data), 2)

    
class TestSlipProblems(unittest.TestCase):
    def test_problem_4(self):
        # Word search
        slip = Slip("^*GOLF", "n")
        slip_overlap = Slip("^*GOLF", "on")
        
        data = dedent("""\
                      GOLFREGHO
                      OFORLRGRF
                      LLFORGOLF
                      FEWRGOOTL
                      EFWRGGRLF""")


        self.assertEqual(slip.match(data), 3)
        self.assertEqual(slip_overlap.match(data), 4)


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
