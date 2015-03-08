"""
Slip v0.2 alpha by Sp3000

Requires Python 3.4
"""

from collections import defaultdict
from copy import deepcopy
import sys

from slipparser import Constructs, SlipParser

DIRECTIONS = [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)]
sys.setrecursionlimit(100000)

class State():
    def __init__(self, pos, dir_, regex_queue, board, match, to_move=False, traversed=None):
        self.pos = pos
        self.dir = dir_
        self.regex_queue = regex_queue
        self.board = board
        self.match = match

        self.to_move = to_move
        self.groups = {}

        self.traversed = traversed

    def move(self):
        if self.to_move:
            self.pos[0] += self.dir[0]
            self.pos[1] += self.dir[1]

        else:
            self.to_move = True


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

        return len(self.groups[group_num])


class Slip():    
    def __init__(self, regex, input_string, config=""):
        self.regex = SlipParser().parser.parse(regex)
        self.board = defaultdict(lambda: defaultdict(str))
        x = y = 0

        self.case_insensitive = "i" in config
        self.no_repeat = "n" in config
        
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
                state_stack = [State([x, y], (1, 0), [deepcopy(self.regex)], self.board, set(),
                                     traversed=set())]
                
                is_match, state_stack = self._match(state_stack)

                if is_match:
                    min_x = min_y = max_x = max_y = None
                    matched_squares = state_stack.pop().match

                    for mx, my in matched_squares:                            
                        if min_x is None or mx < min_x:
                            min_x = mx

                        if max_x is None or mx > max_x:
                            max_x = mx

                        if min_y is None or my < min_y:
                            min_y = my

                        if max_y is None or my > max_y:
                            max_y = my

                    sorted_matches = tuple(sorted(matched_squares))

                    if sorted_matches in found:
                        continue

                    else:
                        found.add(sorted_matches)

                    if min_x is None:
                        print("Empty match found from ({}, {})".format(x, y))

                    else:
                        print("Match found in rectangle: ({}, {}), ({}, {})".format(
                               min_x, min_y, max_x, max_y))

                        array = [[" "]*(max_x - min_x + 1)
                                 for _ in range(min_y, max_y + 1)]

                        for mx, my in matched_squares:
                            array[my-min_y][mx-min_x] = self.board[my][mx]

                        for row in array:
                            print("".join(row).rstrip())

                        print()


    def _match(self, state_stack):
        if not state_stack:
            return (False, state_stack)

        elif not state_stack[-1].regex_queue:
            return (True, state_stack)
        
        state = state_stack.pop()
        construct, *regex_rest = state.regex_queue[0]

        if construct in [Constructs.LITERAL, Constructs.NEGLITERAL]:
            char = regex_rest[0]
            state.move()

            if self.no_repeat:
                if tuple(state.pos) in state.traversed:
                    return self._match(state_stack)

                else:
                    state.traversed.add(tuple(state.pos))

            if state.pos[1] in state.board and state.pos[0] in state.board[state.pos[1]]:
                state_char = state.get_char()

                if construct == Constructs.LITERAL:
                    if self.case_insensitive:
                        cond = (state_char.lower() == char.lower())

                    else:
                        cond = (state_char == char)

                else:
                    if self.case_insensitive:
                        cond = (state_char.lower() != char.lower())

                    else:
                        cond = (state_char != char)
               
                if state_char and cond:
                    state.match.add(tuple(state.pos))
                    state.regex_queue.pop(0)
                    state_stack.append(state)

            return self._match(state_stack)
        

        elif construct == Constructs.ANYCHAR:
            state.move()

            if self.no_repeat:
                if tuple(state.pos) in state.traversed:
                    return self._match(state_stack)

                else:
                    state.traversed.add(tuple(state.pos))
            
            if state.pos[1] in state.board and state.pos[0] in state.board[state.pos[1]]:
                char = state.board[state.pos[1]][state.pos[0]]
                state.match.add(tuple(state.pos))
                state.regex_queue.pop(0)
                state_stack.append(state)
                
            return self._match(state_stack)


        elif construct in [Constructs.CHARCLASS, Constructs.NEGCHARCLASS]:
            for literal in regex_rest[0]:
                new_state = deepcopy(state)
                
                type_ = (Constructs.LITERAL if construct == Constructs.CHARCLASS
                         else Constructs.NEGLITERAL)                
                new_state.regex_queue[0] = [type_, literal[1]]

                state_stack.append(new_state)

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

            if (0 <= state.pos[1] <= max(state.board)
                and state.pos[1] in state.board
                and 0 <= state.pos[0] <= max(state.board[state.pos[1]])): # Todo: Autopad toggle flag
                
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


        elif construct == Constructs.NREPEAT:
            regex, *nums = regex_rest

            if len(nums) == 1: # {n}
                new_state = deepcopy(state)
                
                if nums[0] == 0:
                    new_state.regex_queue.pop(0)

                else:
                    new_state.regex_queue[0][2] -= 1
                    new_state.regex_queue.insert(0, regex)
                    
                state_stack.append(new_state)
                
            return self._match(state_stack)
        

        elif construct == Constructs.OPTIONAL:           
            state2 = deepcopy(state)
            state2.regex_queue[0] = regex_rest[0]
            state.regex_queue.pop(0)
            
            state_stack.append(state)
            state_stack.append(state2)
            
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
            state.match = set()
            state.regex_queue[:1] = [regex_rest[1], [Constructs.GROUPSTORE, group_num, match]]
            state_stack.append(state)
            return self._match(state_stack)
        

        elif construct == Constructs.GROUPSTORE:
            group_num, match = regex_rest
            state.groups[group_num] = deepcopy(state.match)
            state.match |= match
            
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
            state.to_move = prev_state.to_move

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

        elif construct == Constructs.DIRECTIONSET:
            digit = regex_rest[0]

            if digit == 8:
                dir_list = DIRECTIONS[::-1]

            elif digit == 9:
                dir_list = DIRECTIONS[::2][::-1]

            else:
                dir_list = [DIRECTIONS[regex_rest[0]]]

            for dir_ in dir_list:
                new_state = deepcopy(state)
                new_state.dir = dir_
                new_state.regex_queue.pop(0)
                state_stack.append(new_state)

            return self._match(state_stack)

        elif construct == Constructs.ANCHOR:
            digit = regex_rest[0]
            state.regex_queue.pop(0)

            width = max(max(state.board[y]) for y in state.board)
            height = max(state.board)

            anchor_checks = [state.pos[1] == 0,
                             state.pos[0] == width and state.pos[1] == 0,
                             state.pos[0] == width,
                             state.pos[0] == width and state.pos[1] == height,
                             state.pos[1] == height,
                             state.pos[0] == 0 and state.pos[1] == height,
                             state.pos[0] == 0,
                             state.pos[0] == 0 and state.pos[1] == 0]

            if digit == 8:
                if any(anchor_checks[::2]):
                    state_stack.append(state)

            elif digit == 9:
                if any(anchor_checks[1::2]):
                    state_stack.append(state)

            else:
                if anchor_checks[digit]:
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
    
        
