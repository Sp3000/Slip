"""
Slip v0.3.4 alpha by Sp3000

Requires Python 3.4
"""

from collections import defaultdict
from copy import deepcopy
import sys

from slipparser import Constructs, SlipParser

DIRECTIONS = [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)]


class ContinueSearch(Exception):
    pass


class State():
    def __init__(self, pos, dir_, regex_stack, match, display,
                 no_move=True, no_slip=False, traversed=None):
        
        self.pos = pos
        self.dir = dir_
        self.regex_stack = regex_stack
        self.match = match
        self.display = display

        self.no_move = no_move
        self.no_slip = no_slip
        
        self.groups = {}

        self.traversed = traversed

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
        if 0 <= self.pos[0] < board.width and 0 <= self.pos[1] < board.height:
            return False

        return True


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
            return " "


    def __contains__(self, elem):
        return elem in self.board_dict


    def __iter__(self):
        return iter(sorted(self.board_dict, key=lambda pos:(pos[1], pos[0])))


class Slip():    
    def __init__(self, regex, input_string, config=""):
        self.regex = SlipParser().parser.parse(regex)
        self.board = Board(input_string)

        self.case_insensitive = "i" in config
        self.no_repeat = "n" in config
        self.overlapping = "o" in config

        self.first_match = "F" in config
        self.numerical = "N" in config
        self.position = "P" in config
        self.verbose = "V" in config


    def match(self):
        found = set()
        match_count = 0
        
        for pos in self.board:
            state_stack = [State(pos, (1, 0), [deepcopy(self.regex)], set(),
                                 set(), traversed=set())]

            while not (found and self.first_match): # Otherwise just a while True for overlapping               
                is_match, state_stack = self._match(state_stack)

                if is_match:
                    display_squares = state_stack.pop().display
                    sorted_matches = tuple(sorted(display_squares))

                    if sorted_matches and sorted_matches in found:
                        continue

                    match_count += 1
                    
                    if found and not self.numerical and not self.position:
                        print()

                    found.add(sorted_matches)

                    if self.numerical:
                        continue

                    if self.position:
                        print(*pos)
                        continue
                    
                    min_x = min_y = max_x = max_y = None

                    for mx, my in display_squares:                       
                        if min_x is None or mx < min_x:
                            min_x = mx

                        if max_x is None or mx > max_x:
                            max_x = mx

                        if min_y is None or my < min_y:
                            min_y = my

                        if max_y is None or my > max_y:
                            max_y = my

                    if min_x is None:
                        if self.verbose:
                            print("Empty match found from ({}, {})".format(*pos), flush=True)

                    else:
                        if self.verbose:
                            print("Match found in rectangle: ({}, {}), ({}, {})".format(
                                   min_x, min_y, max_x, max_y), flush=True)

                        array = [[" "]*(max_x - min_x + 1)
                                 for _ in range(min_y, max_y + 1)]

                        for pos in display_squares:
                            array[pos[1]-min_y][pos[0]-min_x] = self.board[pos]

                        for row in array:
                            print("".join(row), flush=True)

                    if not self.overlapping:
                        break

                else:
                    break

        if self.numerical:
            print(match_count)


    def _match(self, state_stack):
        while True:            
            if not state_stack:
                return (False, state_stack)

            elif not state_stack[-1].regex_stack:
                return (True, state_stack)

            try:        
                state = state_stack.pop()
                construct, *regex_rest = state.regex_stack[-1]

                if construct in [Constructs.LITERAL, Constructs.NEGCHARCLASS]:
                    state.move()

                    if state.out_of_bounds(self.board):
                        raise ContinueSearch

                    if self.no_repeat:
                        if tuple(state.pos) in state.traversed:
                            raise ContinueSearch

                        else:
                            state.traversed.add(tuple(state.pos))

                    if state.pos in self.board:
                        state_char = self.board[state.pos]

                        if construct == Constructs.LITERAL:
                            if self.case_insensitive:
                                cond = (state_char.lower() == regex_rest[0].lower())

                            else:
                                cond = (state_char == regex_rest[0])

                        else:
                            if self.case_insensitive:
                                cond = (state_char.lower() not in [char.lower() for char in regex_rest[0]])

                            else:
                                cond = (state_char not in regex_rest[0])
                       
                        if state_char and cond:
                            state.match.add(tuple(state.pos))
                            state.display.add(tuple(state.pos))
                            state.regex_stack.pop()
                            state_stack.append(state)

                    raise ContinueSearch
                

                elif construct in [Constructs.ANYCHAR, Constructs.NODISPLAY]:
                    state.move()

                    if state.out_of_bounds(self.board):
                        raise ContinueSearch

                    if self.no_repeat:
                        if tuple(state.pos) in state.traversed:
                            raise ContinueSearch

                        else:
                            state.traversed.add(tuple(state.pos))
                    
                    state.match.add(tuple(state.pos))

                    if construct == Constructs.ANYCHAR:
                        state.display.add(tuple(state.pos))
                        
                    state.regex_stack.pop()
                    state_stack.append(state)
                        
                    raise ContinueSearch


                elif construct == Constructs.CHARCLASS:
                    for char in regex_rest[0]:
                        new_state = deepcopy(state)
                        new_state.regex_stack[-1] = [Constructs.LITERAL, char]

                        state_stack.append(new_state)

                    raise ContinueSearch


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

                    elif command == "#":
                        state.no_move = True

                    elif command == "%":
                        state.no_slip = True

                    state.regex_stack.pop()

                    if not state.out_of_bounds(self.board): # Todo: Autopad toggle flag
                        state_stack.append(state)

                    raise ContinueSearch
                        
                    
                elif construct == Constructs.CONCATENATION:
                    state.regex_stack[-1:] = regex_rest[::-1]
                    state_stack.append(state)

                    raise ContinueSearch
                

                elif construct == Constructs.ASTERISK:
                    new_state = deepcopy(state)
                    state.regex_stack.pop()
                    state_stack.append(state)
                    
                    new_state.regex_stack[-1] = [Constructs.CONCATENATION, regex_rest[0],
                                                [Constructs.ASTERISK, regex_rest[0]]]
                    
                    state_stack.append(new_state)
                    raise ContinueSearch


                elif construct == Constructs.PLUS:           
                    state.regex_stack[-1] = [Constructs.CONCATENATION, regex_rest[0],
                                                [Constructs.ASTERISK, regex_rest[0]]]
                    
                    state_stack.append(state)
                    raise ContinueSearch


                elif construct == Constructs.NREPEAT:
                    regex, *nums = regex_rest

                    if len(nums) == 1: # {n}
                        new_state = deepcopy(state)
                        
                        if nums[0] <= 0:
                            new_state.regex_stack.pop()

                        else:
                            new_state.regex_stack[-1][2] -= 1
                            new_state.regex_stack.append(regex)
                            
                        state_stack.append(new_state)
                        

                    elif nums[0] is None: # {,n}
                        new_state = deepcopy(state)

                        if nums[1] < 0:
                            new_state.regex_stack.pop()
                            state_stack.append(new_state)

                        else:
                            new_state.regex_stack[-1][3] -= 1

                            new_state2 = deepcopy(state)
                            new_state2.regex_stack[-1] = [Constructs.NREPEAT, regex, nums[1]]

                            state_stack.append(new_state)
                            state_stack.append(new_state2)


                    elif nums[1] is None: # {n,}
                        state.regex_stack[-1:] = [[Constructs.ASTERISK, regex],
                                                  [Constructs.NREPEAT, regex, nums[0]]]
                        state_stack.append(state)
                        

                    else: # {n, m}
                        state.regex_stack[-1:] = [[Constructs.NREPEAT, regex, None, nums[1] - nums[0]],
                                                  [Constructs.NREPEAT, regex, nums[0]]]
                        state_stack.append(state)


                    raise ContinueSearch
                

                elif construct == Constructs.OPTIONAL:           
                    state2 = deepcopy(state)
                    state2.regex_stack[-1] = regex_rest[0]
                    state.regex_stack.pop()
                    
                    state_stack.append(state)
                    state_stack.append(state2)
                    
                    raise ContinueSearch


                elif construct == Constructs.NOCAPTURE:
                    match = deepcopy(state.match)
                    display = deepcopy(state.display)
                    groups = deepcopy(state.groups)
                    state.regex_stack[-1:] = [[Constructs.MATCHREMOVE, match, display, groups], regex_rest[0]]
                    state_stack.append(state)

                    raise ContinueSearch


                elif construct == Constructs.MATCHREMOVE:
                    match, display, groups = regex_rest
                    state.match = match
                    state.display = display
                    state.groups = groups
                    state.regex_stack.pop()
                    state_stack.append(state)

                    raise ContinueSearch


                elif construct == Constructs.ALTERNATION:           
                    for regex_part in regex_rest[::-1]:
                        new_state = deepcopy(state)
                        new_state.regex_stack = state.regex_stack[:-1] + [regex_part]

                        state_stack.append(new_state)

                    raise ContinueSearch


                elif construct == Constructs.GROUP:
                    group_num = regex_rest[0]
                    match = state.match
                    state.match = set()
                    state.regex_stack[-1:] = [[Constructs.GROUPSTORE, group_num, match], regex_rest[1]]
                    state_stack.append(state)
                    raise ContinueSearch
                

                elif construct == Constructs.GROUPSTORE:
                    group_num, match = regex_rest
                    state.groups[group_num] = deepcopy(state.match)
                    state.match |= match
                    
                    state.regex_stack.pop()
                    state_stack.append(state)
                    raise ContinueSearch


                elif construct == Constructs.STATIONARY:
                    group_num, regex = regex_rest

                    state.regex_stack[-1:] = [[Constructs.STATIONARYRESET, deepcopy(state)],
                                              [Constructs.GROUP, group_num, regex]]

                    state_stack.append(state)
                    raise ContinueSearch


                elif construct == Constructs.STATIONARYRESET:
                    prev_state = regex_rest[0]
                    state.regex_stack.pop()

                    state.pos = prev_state.pos
                    state.dir = prev_state.dir
                    state.no_move = prev_state.no_move

                    state_stack.append(state)
                    raise ContinueSearch
                

                elif construct == Constructs.LENGTHCHECK:
                    group_num1 = regex_rest[0]

                    if group_num1 not in state.groups:
                        raise ContinueSearch

                    group_num2 = regex_rest[1]
                    length = state.group_length(group_num1)

                    state.regex_stack[-1:] = [[Constructs.LENGTHVERIFY, group_num2, length],
                                              [Constructs.GROUP, group_num2, regex_rest[2]]]

                    state_stack.append(state)
                    raise ContinueSearch
                

                elif construct == Constructs.LENGTHVERIFY:
                    group_num = regex_rest[0]
                    length = regex_rest[1]

                    if state.group_length(group_num) == length:
                        state.regex_stack.pop()
                        state_stack.append(state)

                    raise ContinueSearch


                elif construct == Constructs.DIRECTIONSET:
                    digit = regex_rest[0]
                    
                    if digit == 8:
                        dirs_ = [7, 6, 5, 4, 3, 2, 1, 0]

                    elif digit == 9:
                        dirs_ = [6, 4, 2, 0]

                    else:
                        dirs_ = [digit]

                    new_state = deepcopy(state)
                    new_state.regex_stack[-1] = [Constructs.DIRECTIONCHECK, dirs_]
                    state_stack.append(new_state)

                    raise ContinueSearch
                

                elif construct == Constructs.DIRECTIONCHECK:
                    nums = regex_rest[0]

                    new_state = deepcopy(state)
                    *new_state.regex_stack[-1][1], dir_ = new_state.regex_stack[-1][1]

                    new_state2 = deepcopy(state)
                    new_state2.regex_stack.pop()
                    new_state2.dir = DIRECTIONS[dir_]

                    if new_state.regex_stack[-1][1]:
                        state_stack.append(new_state)

                    state_stack.append(new_state2)
                    
                    raise ContinueSearch
                

                elif construct == Constructs.ANCHOR:
                    digit = regex_rest[0]
                    state.regex_stack.pop()

                    width, height = self.board.width, self.board.height

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

                    raise ContinueSearch

            except ContinueSearch:
                continue


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
    slip.match()
    
        
