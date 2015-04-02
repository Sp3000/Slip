class Regex():
    pass


class Literal(Regex):
    def __init__(self, char):
        self.char = char

    def __str__(self):
        return self.char


class Concatenation(Regex):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __str__(self):
        return str(self.left) + str(self.right)
        

class Quantifier(Regex):
    def __init__(self):
        self.lazy_match = False
        

class Asterisk(Quantifier):
    def __init__(self, inner):
        self.inner = inner

    def __str__(self):
        return str(self.inner) + "*"


class Plus(Quantifier):
    def __init__(self, inner):
        self.inner = inner

    def __str__(self):
        return str(self.inner) + "+"


class NRepeat(Quantifier):
    def __init__(self, inner, low, high):
        self.inner = inner
        self.low = low
        self.high = high

    def __str__(self):
        if self.low == self.high:
            return "{}{{{}}}".format(self.inner, self.low)

        elif self.low is None:
            return "{}{{,{}}}".format(self.inner, self.high)

        elif self.high is None:
            return "{}{{{},}}".format(self.inner, self.low)

        else:
            return "{}{{{},{}}}".format(self.inner, self.low, self.high)
        
class Optional(Quantifier):
    def __init__(self, inner):
        self.inner = inner

    def __str__(self):
        return str(self.inner) + "?"


class CharClass(Regex):
    def __init__(self, chars):
        self.chars = chars

    def __str__(self):
        return "<class {}>".format("".join(chars))


class NegatedCharClass(Regex):
    def __init__(self, chars):
        self.chars = chars

    def __str__(self):
        return "<negclass {}>".format("".join(chars))


class AnyChar(Regex):
    def __str__(self):
        return "."


class Group(Regex):
    def __init__(self, groupnum, inner):
        self.groupnum = groupnum
        self.inner = inner

    def __str__(self):
        return "<group {}: {}>".format(self.groupnum, self.inner)


class GroupStore(Regex):
    def __init__(self, group_num, match):
        self.group_num = group_num
        self.match = match

    def __str__(self):
        return "<groupstore {}: length {}>".format(self.group_num, len(self.match))


class Command(Regex):
    def __init__(self, char):
        self.char = char

    def __str__(self):
        return self.char


class Directional(Regex):
    def __init__(self, char):
        self.char = char

    def __str__(self):
        return "^" + self.char


class DirectionCheck(Regex):
    def __init__(self, dirs_):
        self.dirs = dirs_

    def __str__(self):
        return "<dircheck [{}]>".format(" ".join(map(str, self.dirs)))
