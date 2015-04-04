class Regex():
    pass


class Literal(Regex):
    def __init__(self, char):
        self.char = char

    def __repr__(self):
        return self.char


class Concatenation(Regex):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __repr__(self):
        return repr(self.left) + repr(self.right)


class Alternation(Regex):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __repr__(self):
        return "{}|{}".format(self.left, self.right)
        

class Quantifier(Regex):
    def __init__(self, inner, lazy_match):
        self.inner = inner
        self.lazy_match = lazy_match
        

class Asterisk(Quantifier):
    def __init__(self, inner, lazy_match):
        super().__init__(inner, lazy_match)

    def __repr__(self):
        return str(self.inner) + "*"


class Plus(Quantifier):
    def __init__(self, inner, lazy_match):
        super().__init__(inner, lazy_match)

    def __repr__(self):
        return str(self.inner) + "+"


class NRepeat(Quantifier):
    def __init__(self, inner, lazy_match, low, high):
        super().__init__(inner, lazy_match)
        self.low = low
        self.high = high

    def __repr__(self):
        if self.low == self.high:
            return "{}{{{}}}".format(self.inner, self.low)

        elif self.low is None:
            return "{}{{,{}}}".format(self.inner, self.high)

        elif self.high is None:
            return "{}{{{},}}".format(self.inner, self.low)

        else:
            return "{}{{{},{}}}".format(self.inner, self.low, self.high)
        
class Optional(Quantifier):
    def __init__(self, inner, lazy_match):
        super().__init__(inner, lazy_match)

    def __repr__(self):
        return str(self.inner) + "?"


class CharClass(Regex):
    def __init__(self, chars):
        self.chars = chars

    def __repr__(self):
        return "<class {}>".format("".join(chars))


class NegatedCharClass(Regex):
    def __init__(self, chars):
        self.chars = chars

    def __repr__(self):
        return "<negclass {}>".format("".join(chars))


class AnyChar(Regex):
    def __repr__(self):
        return "."


class NoDisplay(Regex):
    def __repr__(self):
        return ","


class NoDisplayDecrement(Regex):
    def __repr__(self):
        return "<nodispdec>"


class Group(Regex):
    def __init__(self, group_num, inner):
        self.group_num = group_num
        self.inner = inner

    def __repr__(self):
        return "<group {}: {}>".format(self.group_num, self.inner)


class GroupStore(Regex):
    def __init__(self, group_num, prev_match):
        self.group_num = group_num
        self.prev_match = prev_match
        
    def __repr__(self):
        return "<groupstore {}>".format(self.group_num)


class StationaryGroup():
    def __init__(self, group_num, inner):
        self.group_num = group_num
        self.inner = inner

    def __repr__(self):
        return "<stationary {} {}>".format(self.group_num, self.inner)


class StationaryReset(Regex):
    def __init__(self, pos, dir_, no_move, no_slip):
        self.pos = pos
        self.dir = dir_
        self.no_move = no_move
        self.no_slip = no_slip

    def __repr__(self):
        return "<stationaryreset>"
    

class LengthAssert():
    def __init__(self, group_num, equal_to, inner):
        self.group_num = group_num
        self.equal_to = equal_to
        self.inner = inner

    def __repr__(self):
        return "<lengthassert {} {} {}>".format(self.group_num, self.equal_to,
                                                self.inner)


class LengthCheck():
    def __init__(self, group_num, length):
        self.group_num = group_num
        self.length = length

    def __repr__(self):
        return "<lengthcheck {} {}>".format(self.group_num, self.length)


class Command(Regex):
    def __init__(self, char):
        self.char = char

    def __repr__(self):
        return self.char


class Anchor(Regex):
    def __init__(self, char):
        self.char = char

    def __repr__(self):
        return "$" + self.char


class Directional(Regex):
    def __init__(self, char):
        self.char = char

    def __repr__(self):
        return "^" + self.char


class DirectionCheck(Regex):
    def __init__(self, dirs_):
        self.dirs = dirs_

    def __repr__(self):
        return "<dircheck [{}]>".format(" ".join(map(str, self.dirs)))
