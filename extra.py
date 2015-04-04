import collections
import string

classes = {"a": string.ascii_lowercase + string.ascii_uppercase,
           "c": "".join(c for c in string.ascii_lowercase + string.ascii_uppercase if
                        c.lower() not in "aeiou"),
           "d": string.digits,
           "h": string.hexdigits,
           "l": string.ascii_lowercase,
           "o": string.octdigits,
           "p": string.punctuation,
           "s": " \t\x0b\x0c", # Not \r\n
           "u": string.ascii_uppercase,
           "v": "aeiouAEIOU",
           "w": string.ascii_lowercase + string.ascii_uppercase + string.digits + "_",
           "y": "aeiouyAEIOUY"}

# https://code.activestate.com/recipes/576694/
class OrderedSet(collections.MutableSet):

    def __init__(self, iterable=None):
        self.end = end = [] 
        end += [None, end, end]         # sentinel node for doubly linked list
        self.map = {}                   # key --> [key, prev, next]
        if iterable is not None:
            self |= iterable

    def __len__(self):
        return len(self.map)

    def __contains__(self, key):
        return key in self.map

    def add(self, key):
        if key not in self.map:
            end = self.end
            curr = end[1]
            curr[2] = end[1] = self.map[key] = [key, curr, end]

    def discard(self, key):
        if key in self.map:        
            key, prev, next = self.map.pop(key)
            prev[2] = next
            next[1] = prev

    def __iter__(self):
        end = self.end
        curr = end[2]
        while curr is not end:
            yield curr[0]
            curr = curr[2]

    def __reversed__(self):
        end = self.end
        curr = end[1]
        while curr is not end:
            yield curr[0]
            curr = curr[1]

    def pop(self, last=True):
        if not self:
            raise KeyError('set is empty')
        key = self.end[1][0] if last else self.end[2][0]
        self.discard(key)
        return key

    def keep(self, n):
        while len(self.map) > n:
            self.pop()

    def __repr__(self):
        if not self:
            return '%s()' % (self.__class__.__name__,)
        return '%s(%r)' % (self.__class__.__name__, list(self))

    def __eq__(self, other):
        if isinstance(other, OrderedSet):
            return len(self) == len(other) and list(self) == list(other)
        return set(self) == set(other)
