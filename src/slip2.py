"""
Slip v0.5 alpha by Sp3000

Requires Python 3.4
"""

from collections import defaultdict
from copy import deepcopy
import sys

from constructs import *
from extra import OrderedSet
from slipparser import SlipParser

DIRECTIONS = [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)]

class State():
    def __init__(self, pos, regex):
        self.pos = pos
        self.dir = (1, 0)
        self.regex_stack = [regex]

        # Rather than storing all to-display/traversed cells, keep track of those cells
        # in a stack separately and store the index, then pop as appropriate when backtracking
        self.match_count = 0
        self.display_count = 0
        self.traversed_count = 0
        
        self.groups = {}
        self.anchors = {}
        
        self.no_move = True
        self.no_slip = False


    def clone(self):
        new_state = State(None, None)

        new_state.pos = self.pos
        new_state.dir = self.dir
        new_state.regex_stack = self.regex_stack[:]

        new_state.match_count = self.match_count
        new_state.display_count = self.display_count
        new_state.traversed_count = self.traversed_count

        new_state.groups = deepcopy(self.groups)
        new_state.anchors = deepcopy(self.anchors)

        new_state.no_move = self.no_move
        new_state.no_slip = self.no_slip

        return new_state


    def move(self):
        if self.no_move:
            self.no_move = False

        else:
            self.pos = (self.pos[0] + self.dir[0], self.pos[1] + self.dir[1])


    def rotate(self, offset):
        self.dir = DIRECTIONS[(DIRECTIONS.index(self.dir) + offset) % len(DIRECTIONS)]


    def slip_left(self):
        if self.no_slip:
            self.no_slip = False

        else:
            orthog = DIRECTIONS[(DIRECTIONS.index(self.dir) - 2) % len(DIRECTIONS)]
            self.pos = (self.pos[0] + orthog[0], self.pos[1] + orthog[1])
        

    def slip_right(self):
        if self.no_slip:
            self.no_slip = False

        else:
            orthog = DIRECTIONS[(DIRECTIONS.index(self.dir) + 2) % len(DIRECTIONS)]
            self.pos = (self.pos[0] + orthog[0], self.pos[1] + orthog[1])


    def group_length(self, group_num):
        if group_num not in self.groups:
            return -1

        return len(self.groups[group_num])


    def out_of_bounds(self, board):
        # TODO: Make toggleable with rectangular grid
        return self.pos not in board


class Board():
    def __init__(self, input_string):
        self.board_dict = defaultdict(str)
        x = y = 0
        self.width = 0
        self.height = 1

        for char in input_string:
            if char == "\n":
                 y += 1
                 x = 0
                 self.height = y + 1

            else:
                self.board_dict[(x, y)] = char
                self.width = max(x + 1, self.width)
                x += 1


    def __getitem__(self, pos):
        if pos in self.board_dict:
            return self.board_dict[pos]

        else:
            return ""


    def __contains__(self, elem):
        return elem in self.board_dict


    def __iter__(self):
        return iter(sorted(self.board_dict, key=lambda pos:(pos[1], pos[0])))


    def __repr__(self):
        return repr(dict(self.board_dict))


class Slip():    
    def __init__(self, regex, input_string, config=""):
        self.regex = SlipParser().parser.parse(regex)
        self.board = Board(input_string)

        self.case_insensitive = "i" in config
        self.no_repeat = "n" in config
        
        self.verbose = "V" in config


    def match_one(self):
        found = []

        for pos in self.board:
            try:
                result = next(self.match(pos))
                if result and result in [pair[1] for pair in found]:
                    continue

                found.append((pos, result))

            except StopIteration:
                continue

        return found


    def match_all(self):
        found = []

        for pos in self.board:
            for result in self.match(pos):
                if result and result in [pair[1] for pair in found]:
                    continue

                found.append((pos, result))

        return found


    def match_first(self):
        for pos in self.board:
            try:
                result = next(self.match(pos))
                return [result]

            except StopIteration:
                continue

        return []


    def match(self, pos):
        state_stack = [State(pos, self.regex)]
        match_set = OrderedSet([])
        display_set = OrderedSet([])
        traversed_set = OrderedSet([])
        

        def backtrack():
            state_stack.pop()

            if state_stack:
                display_set.keep(state_stack[-1].display_count)
                traversed_set.keep(state_stack[-1].traversed_count)


        def add_to_match_only():
            match_set.add(state.pos)
            state.match_count = len(match_set)
            

        def add_to_display():
            match_set.add(state.pos)
            state.match_count = len(match_set)
            display_set.add(state.pos)
            state.display_count = len(display_set)


        def add_to_traversed():
            traversed_set.add(state.pos)
            state.traversed_count = len(traversed_set)


        while state_stack:
            state = state_stack[-1]


            # For debugging:
            # print(list(map(str, state.regex_stack)))

            if not state.regex_stack:
                yield set(display_set)
                backtrack()
                continue

            construct = state.regex_stack.pop()

            if type(construct) in [Literal, NegatedCharClass, AnyChar]:
                state.move()

                if state.out_of_bounds(self.board):
                    backtrack()
                    continue

                if self.no_repeat:
                    if state.pos in traversed_set:
                        backtrack()
                        continue

                    else:
                        add_to_traversed()

                state_char = self.board[state.pos]

                if isinstance(construct, Literal):
                    match_char = construct.char

                    if self.case_insensitive:
                        cond = (state_char.lower() == match_char.lower())

                    else:
                        cond = (state_char == match_char)

                elif isinstance(construct, NegatedCharClass):
                    avoid_chars = construct.chars

                    if self.case_insensitive:
                        cond = (state_char.lower() not in [char.lower() for char in avoid_chars])
                        
                    else:
                        cond = (state_char not in avoid_chars)

                elif isinstance(construct, AnyChar):
                    cond = True

                if cond:
                    add_to_display()

                else:
                    backtrack()
                    continue


            elif isinstance(construct, CharClass):
                if not construct.chars:
                    backtrack()
                    continue

                new_state = state.clone()
                new_state.regex_stack.append(Literal(construct.chars[0]))
                state.regex_stack.append(CharClass(construct.chars[1:]))
                state_stack.append(new_state)


            elif isinstance(construct, Concatenation):
                state.regex_stack.append(construct.right)
                state.regex_stack.append(construct.left)


            elif isinstance(construct, Asterisk):
                new_state = state.clone()
                new_state.regex_stack.append(construct)
                new_state.regex_stack.append(construct.inner)
                state_stack.append(new_state)

                if construct.lazy_match:
                    state_stack[-2:] = state_stack[-2:][::-1]


            elif isinstance(construct, Plus):
                state.regex_stack.append(Asterisk(construct.inner))
                state.regex_stack.append(construct.inner)

                if construct.lazy_match:
                    state_stack[-2:] = state_stack[-2:][::-1]


            elif isinstance(construct, Optional):
                new_state = state.clone()
                new_state.regex_stack.append(construct.inner)
                state_stack.append(new_state)

                if construct.lazy_match:
                    state_stack[-2:] = state_stack[-2:][::-1]


            elif isinstance(construct, NRepeat):
                if construct.low == construct.high: # {n}:
                    n = construct.low

                    print(n, str(construct.inner))
                    
                    if n <= 0:
                        continue

                    else:
                        new_regex = NRepeat(construct.inner, n-1, n-1)
                        state.regex_stack.append(new_regex)
                        state.regex_stack.append(construct.inner)

                elif construct.low is None: # {,n}
                    n = construct.high
                    
                    if n <= 0:
                        continue

                    else:
                        new_state = state.clone()
                        new_regex1 = NRepeat(construct.inner, n, n)
                        new_state.regex_stack.append(new_regex1)
                        
                        new_regex2 = NRepeat(construct.inner, None, n-1)
                        new_regex2.lazy_match = construct.lazy_match
                        state.regex_stack.append(new_regex2)

                        state_stack.append(new_state)

                        if construct.lazy_match:
                            state_stack[-2:] = state_stack[-2:][::-1]


            elif isinstance(construct, Group):
                raise NotImplementedError

                # Uh oh


            elif isinstance(construct, Command):
                command = construct.char

                if command == ">":
                    state.rotate(2)
                    
                elif command == "<":
                    state.rotate(-2)

                elif command == "/":
                    state.slip_left()

                elif command == "\\":
                    state.slip_right()

                elif command == "#":                    
                    state.no_move = True

                elif command == "%":
                    state.no_slip = True

                if state.out_of_bounds(self.board): # TODO: Autopad toggle flag
                    backtrack()
                    continue


            elif isinstance(construct, Directional):
                if construct.char.isdigit():
                    digit = int(construct.char)

                    if digit == 8:
                        indices = [0, 1, 2, 3, 4, 5, 6, 7]

                    elif digit == 9:
                        indices = [0, 2, 4, 6]

                    else:
                        indices = [digit]

                    dirs_ = [DIRECTIONS[i] for i in indices]
                    state.regex_stack.append(DirectionCheck(dirs_))


            elif isinstance(construct, DirectionCheck):
                if not construct.dirs:
                    backtrack()
                    continue

                new_state = state.clone()
                new_state.dir = construct.dirs[0]
                construct.dirs = construct.dirs[1:]
                state.regex_stack.append(construct)
                state_stack.append(new_state)


        raise StopIteration


    def output(self, pos, cells):
        min_x = min_y = max_x = max_y = None

        for x, y in cells:                       
            if min_x is None or x < min_x:
                min_x = x

            if max_x is None or x > max_x:
                max_x = x

            if min_y is None or y < min_y:
                min_y = y

            if max_y is None or y > max_y:
                max_y = y

        if min_x is None:
            if self.verbose:
                print("Empty match found from ({}, {})".format(*pos), flush=True)

        else:
            if self.verbose:
                print("Match found in rectangle: ({}, {}), ({}, {})".format(
                       min_x, min_y, max_x, max_y), flush=True)

            array = [[" "]*(max_x - min_x + 1)
                     for _ in range(min_y, max_y + 1)]

            for pos in cells:
                array[pos[1]-min_y][pos[0]-min_x] = self.board[pos]

            for row in array:
                print("".join(row), flush=True)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        input_filepath = input("Enter input filepath: ")
        regex = input("Enter regex: ")
        config = input("Enter config string: ")

        with open(input_filepath) as inputfile:
            input_string = inputfile.read()

    elif len(sys.argv) == 2:
        print("Missing file: Need both regex and input files")
        exit()

    else:
        # Command line        
        with open(sys.argv[1]) as regexfile:
            regex = regexfile.read()

        with open(sys.argv[2]) as inputfile:
            input_string = inputfile.read()

        if len(sys.argv) > 3:
            config = sys.argv[3]

        else:
            config = ""

    slip = Slip(regex, input_string, config)

    if "f" in config:
        result = slip.match_first()

    elif "o" in config:
        result = slip.match_all()

    else:
        result = slip.match_one()

    if "N" in config:
        print(len(result))

    else:
        for i, (pos, match) in enumerate(result):
            if i > 0:
                print()
                
            slip.output(pos, match)
                    
