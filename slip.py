"""
Slip v0.1 alpha by Sp3000

Requires Python 3.4
"""

from collections import defaultdict
from copy import deepcopy
import sys

from slipparser import Constructs, SlipParser

DIRECTIONS = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]
sys.setrecursionlimit(100000)

class State():
    def __init__(self, pos, dir_, regex_queue, board, match):
        self.pos = pos
        self.dir = dir_
        self.regex_queue = regex_queue
        self.board = board
        self.match = match

        self.groups = {}


    def move(self):
        self.pos[0] += self.dir[0]
        self.pos[1] += self.dir[1]


    def rotate(self, offset):
        self.dir = DIRECTIONS[(DIRECTIONS.index(self.dir) + offset) % len(DIRECTIONS)]


    def get_char(self):
        if self.pos[1] in self.board and self.pos[0] in self.board[self.pos[1]]:
            return self.board[self.pos[1]][self.pos[0]]

        return ""


    def slip_left(self):
        orthog = DIRECTIONS[(DIRECTIONS.index(self.dir) - 2) % len(DIRECTIONS)]
        self.pos[0] += orthog[0]
        self.pos[1] += orthog[1]
        

    def slip_right(self):
        orthog = DIRECTIONS[(DIRECTIONS.index(self.dir) + 2) % len(DIRECTIONS)]
        self.pos[0] += orthog[0]
        self.pos[1] += orthog[1]


    def group_length(self, group_num):
        if group_num not in self.groups:
            return -1
        
        length = 0

        for y in self.groups[group_num]:
            for x in self.groups[group_num][y]:
                length += 1

        return length


class Slip():    
    def __init__(self, regex, input_string, config=""):
        self.regex = SlipParser().parser.parse(regex)
        self.board = defaultdict(lambda: defaultdict(str))
        x = y = 0

        self.case_insensitive = "i" in config
        
        for char in input_string:
            if char == "\n":
                y += 1
                x = 0

            else:
                if self.case_insensitive:
                    self.board[y][x] = char

                else:
                    self.board[y][x] = char
                    
                x += 1


    def match(self):
        found = set()
        
        for y in self.board:
            for x in self.board[y]:
                state_stack = [State([x-1, y], (1, 0), [self.regex], self.board,
                                     defaultdict(lambda: defaultdict(str)))]
                
                is_match, state_stack = self._match(state_stack)

                if is_match:
                    min_x = min_y = max_x = max_y = None
                    match = state_stack.pop().match

                    matched_squares = set()

                    for y in match:
                        for x in match[y]:
                            matched_squares.add((x, y))
                            
                            if min_x is None or x < min_x:
                                min_x = x

                            if max_x is None or x > max_x:
                                max_x = x

                            if min_y is None or y < min_y:
                                min_y = y

                            if max_y is None or y > max_y:
                                max_y = y

                    sorted_matches = tuple(sorted(matched_squares))

                    if sorted_matches in found:
                        continue

                    else:
                        found.add(sorted_matches)

                    if min_x is None:
                        print("Empty match found from ({}, {})".format(x, y))
                        print()

                    else:
                        print("Match found in rectangle: ({}, {}), ({}, {})".format(
                               min_x, min_y, max_x, max_y))
                        print()

                        array = [[" "]*(max_x - min_x + 1)
                                 for _ in range(min_y, max_y+1)]

                        for y in match:
                            for x in match[y]:
                                array[y-min_y][x-min_x] = match[y][x]

                        for row in array:
                            print("".join(row))

                        print()


    def _match(self, state_stack):
        if not state_stack:
            return (False, state_stack)

        elif not state_stack[-1].regex_queue:
            return (True, state_stack)
        
        state = state_stack.pop()
        construct, *regex_rest = state.regex_queue[0]

        if construct == Constructs.LITERAL:
            char = regex_rest[0]    
            state.move()

            if self.case_insensitive:
                cond = (state.get_char().lower() == char.lower())

            else:
                cond = (state.get_char() == char)
           
            if cond:
                state.match[state.pos[1]][state.pos[0]] = char
                state.regex_queue.pop(0)
                state_stack.append(state)
                return self._match(state_stack)

            else:
                return self._match(state_stack)


        elif construct == Constructs.COMMAND:
            command = regex_rest[0]

            if command == ">":
                state.rotate(2)

            elif command == "<":
                state.rotate(-2)

            elif command == "/":
                state.slip_left()

            elif command == "\\":
                state.slip_right()

            state.regex_queue.pop(0)

            if (-1 <= state.pos[1] <= max(state.board) + 1
                and state.pos[1] in state.board
                and -1 <= state.pos[0] <= max(state.board[state.pos[1]]) + 1):
                
                state_stack.append(state)

            return self._match(state_stack)
                
            
        elif construct == Constructs.CONCATENATION:
            state.regex_queue[:1] = regex_rest
            state_stack.append(state)

            return self._match(state_stack)
        

        elif construct == Constructs.ASTERISK:
            new_state = deepcopy(state)
            state.regex_queue.pop(0)
            state_stack.append(state)
            
            new_state.regex_queue[0] = [Constructs.CONCATENATION, regex_rest[0],
                                        [Constructs.ASTERISK, regex_rest[0]]]
            
            state_stack.append(new_state)
            return self._match(state_stack)


        elif construct == Constructs.PLUS:           
            state.regex_queue[0] = [Constructs.CONCATENATION, regex_rest[0],
                                        [Constructs.ASTERISK, regex_rest[0]]]
            
            state_stack.append(state)
            return self._match(state_stack)


        elif construct == Constructs.ALTERNATION:
            for regex_part in regex_rest[::-1]:
                new_state = deepcopy(state)
                new_state.regex_queue = [regex_part] + state.regex_queue[1:]

                state_stack.append(new_state)

            return self._match(state_stack)


        elif construct == Constructs.GROUP:
            group_num = regex_rest[0]
            match = state.match
            state.match = defaultdict(lambda: defaultdict(str))
            state.regex_queue[:1] = [regex_rest[1], [Constructs.GROUPSTORE, group_num, match]]
            state_stack.append(state)
            return self._match(state_stack)
        

        elif construct == Constructs.GROUPSTORE:
            group_num, match = regex_rest
            state.groups[group_num] = deepcopy(state.match)

            for y in match:
                for x in match[y]:
                    state.match[y][x] = match[y][x]

            state.regex_queue.pop(0)
            state_stack.append(state)
            return self._match(state_stack)


        elif construct == Constructs.STATIONARY:
            group_num, regex = regex_rest

            state.regex_queue[:1] = [[Constructs.GROUP, group_num, regex],
                                     [Constructs.STATIONARYRESET, deepcopy(state)]]

            state_stack.append(state)
            return self._match(state_stack)


        elif construct == Constructs.STATIONARYRESET:
            prev_state = regex_rest[0]
            state.regex_queue.pop(0)

            state.pos = prev_state.pos
            state.dir = prev_state.dir

            state_stack.append(state)
            return self._match(state_stack)
        

        elif construct == Constructs.LENGTHCHECK:
            group_num1 = regex_rest[0]

            if group_num1 not in state.groups:
                return self._match(state_stack)

            group_num2 = regex_rest[1]
            length = state.group_length(group_num1)

            state.regex_queue[:1] = [[Constructs.GROUP, group_num2, regex_rest[2]],
                                     [Constructs.LENGTHVERIFY, group_num2, length]]

            state_stack.append(state)
            return self._match(state_stack)
        

        elif construct == Constructs.LENGTHVERIFY:
            group_num = regex_rest[0]
            length = regex_rest[1]

            if state.group_length(group_num) == length:
                state.regex_queue.pop(0)
                state_stack.append(state)

            return self._match(state_stack)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Please run from command line, with arguments <regex file> and <input file>")
        exit()
        
    with open(sys.argv[1]) as regexfile:
        regex = regexfile.read()

    with open(sys.argv[2]) as inputfile:
        input_string = inputfile.read()

    if len(sys.argv) > 3:
        config = sys.argv[3]

    else:
        config = ""

    slip = Slip(regex, input_string, config)
    slip.match()
    
        
