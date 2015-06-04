class Regex():
    pass


class Empty(Regex):
    def __init__(self):
        pass
    
    def __repr__(self):
        return "<empty>"


class Literal(Regex):
    def __init__(self, char):
        self.char = char

    def __repr__(self):
        return self.char


    def __iter__(self):
        return iter([])


class Concatenation(Regex):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __repr__(self):
        return repr(self.left) + repr(self.right)


    def __iter__(self):
        return iter([self.left, self.right])


class Alternation(Regex):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __repr__(self):
        return "{}|{}".format(self.left, self.right)


    def __iter__(self):
        return iter([self.left, self.right])
        

class Quantifier(Regex):
    def __init__(self, inner, lazy_match):
        self.inner = inner
        self.lazy_match = lazy_match


    def __iter__(self):
        return iter([self.inner])
        

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
        return "<class {}>".format("".join(self.chars))


    def __iter__(self):
        return iter([])


class NegatedCharClass(Regex):
    def __init__(self, chars):
        self.chars = chars

    def __repr__(self):
        return "<negclass {}>".format("".join(self.chars))


    def __iter__(self):
        return iter([])


class AnyChar(Regex):
    def __repr__(self):
        return "."


    def __iter__(self):
        return iter([])


class NoDisplay(Regex):
    def __repr__(self):
        return ","


    def __iter__(self):
        return iter([])


class NoMatch(Regex):
    def __repr__(self):
        return ":"


    def __iter__(self):
        return iter([])


class NoDisplayMatch(Regex):
    def __repr__(self):
        return ";"
    

    def __iter__(self):
        return iter([])
    

class NoDisplayDecrement(Regex):
    def __repr__(self):
        return "<nodispdec>"


    def __iter__(self):
        return iter([])


# class GroupLike(Regex):

class Group(Regex):
    def __init__(self, group_num, inner):
        self.group_num = group_num
        self.inner = inner

    def __repr__(self):
        return "<group {}: {}>".format(self.group_num, self.inner)


    def __iter__(self):
        return iter([self.inner])


class GroupStore(Regex):
    def __init__(self, group_num, prev_match):
        self.group_num = group_num
        self.prev_match = prev_match
        
    def __repr__(self):
        return "<groupstore {}>".format(self.group_num)


    def __iter__(self):
        return iter([])


class StationaryGroup():
    def __init__(self, group_num, inner):
        self.group_num = group_num
        self.inner = inner

    def __repr__(self):
        return "<stationary {} {}>".format(self.group_num, self.inner)


    def __iter__(self):
        return iter([self.inner])


class StationaryReset(Regex):
    def __init__(self, pos, dir_, no_move, no_slip):
        self.pos = pos
        self.dir = dir_
        self.no_move = no_move
        self.no_slip = no_slip

    def __repr__(self):
        return "<stationaryreset>"


    def __iter__(self):
        return iter([])
    

class LengthAssert():
    def __init__(self, group_num, equal_to, inner):
        self.group_num = group_num
        self.equal_to = equal_to
        self.inner = inner

    def __repr__(self):
        return "<lengthassert {} {} {}>".format(self.group_num, self.equal_to,
                                                self.inner)


    def __iter__(self):
        return iter([self.inner])


class LengthCheck():
    def __init__(self, group_num, length):
        self.group_num = group_num
        self.length = length

    def __repr__(self):
        return "<lengthcheck {} {}>".format(self.group_num, self.length)


    def __iter__(self):
        return iter([])


class NoMatchGroup():
    def __init__(self, inner):
        self.inner = inner

    def __repr__(self):
        return "<nomatch {}>".format(self.inner)


    def __iter__(self):
        return iter([self.inner])


class NoDisplayGroup():
    def __init__(self, group_num, inner):
        self.group_num = group_num
        self.inner = inner

    def __repr__(self):
        return "<nodisp {} {}>".format(self.group_num, self.inner)


    def __iter__(self):
        return iter([self.inner])


class NoDisplayMatchGroup():
    def __init__(self, inner):
        self.inner = inner

    def __repr__(self):
        return "<nodispmatch {}>".format(self.inner)


    def __iter__(self):
        return iter([self.inner])


class Recursive():
    def __init__(self, group_num):
        self.group_num = group_num
        
    def __repr__(self):
        if self.group_num is None:
            return "<recursive>"

        else:
            return "<recursive {}>".format(self.group_num)
        

    def __iter__(self):
        return iter([])


class Command(Regex):
    def __init__(self, char):
        self.char = char

    def __repr__(self):
        return self.char


    def __iter__(self):
        return iter([])


class Anchor(Regex):
    def __init__(self, char):
        self.char = char

    def __repr__(self):
        return "$" + self.char
    

    def __iter__(self):
        return iter([])
    

class Directional(Regex):
    def __init__(self, char):
        self.char = char

    def __repr__(self):
        return "^" + self.char


    def __iter__(self):
        return iter([])


class DirectionCheck(Regex):
    def __init__(self, dirs_):
        self.dirs = dirs_

    def __repr__(self):
        return "<dircheck [{}]>".format(" ".join(map(str, self.dirs)))


    def __iter__(self):
        return iter([])
