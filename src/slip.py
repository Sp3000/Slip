"""
Slip v0.4.2 alpha by Sp3000

Requires Python 3.4
"""

from collections import defaultdict
from copy import deepcopy
import sys

from slipparser import Constructs, SlipParser
from extra import OrderedSet, Regex

DIRECTIONS = [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)]


class State():
    def __init__(self, pos, dir_, regex_stack):
        
        self.pos = pos
        self.dir = dir_
        self.regex_stack = regex_stack

        # Rather than storing all to-display/traversed cells, keep track of those cells
        # in a stack separately and store the index, then pop as appropriate when backtracking
        self.match_count = 0
        self.display_count = 0
        self.traversed_count = 0

        self.no_move = True
        self.no_slip = False
        
        self.groups = {}
        self.anchors = {}
        

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
            state_stack = [State(pos, (1, 0), [deepcopy(self.regex)])]
            match_set = OrderedSet([])
            display_set = OrderedSet([])
            traversed_set = OrderedSet([])

            while not (found and self.first_match): # Otherwise just a while True for overlapping               
                is_match, state_stack, match_set, display_set, traversed_set = self._match(state_stack, match_set, display_set, traversed_set)

                if is_match:
                    state_stack.pop()
                    sorted_matches = tuple(sorted(display_set))

                    if sorted_matches and sorted_matches in found:
                        if self.overlapping:
                            continue
                        else:
                            break

                    match_count += 1
                    
                    if found and not self.numerical and not self.position:
                        print()

                    found.add(sorted_matches)

                    if self.numerical:
                        if self.overlapping:
                            continue
                        else:
                            break

                    if self.position:
                        print(*pos)
                        if self.overlapping:
                            continue
                        else:
                            break
                    
                    min_x = min_y = max_x = max_y = None

                    for mx, my in display_set:                       
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

                        for pos in display_set:
                            array[pos[1]-min_y][pos[0]-min_x] = self.board[pos]

                        for row in array:
                            print("".join(row), flush=True)

                    if not self.overlapping:
                        break

                else:
                    break

        if self.numerical:
            print(match_count)


    def _match(self, state_stack, match_set, display_set, traversed_set):
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

                
        while True:                
            if not state_stack:
                # No more options left in stack
                return (False, state_stack, match_set, display_set, traversed_set)

            elif not state_stack[-1].regex_stack:
                # Regex completely matched
                return (True, state_stack, match_set, display_set, traversed_set)
    
            state = state_stack[-1]
            regex = state.regex_stack.pop()
            construct, *regex_rest = regex


            if construct in [Constructs.LITERAL, Constructs.NEGCHARCLASS]:
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

                if state.pos in self.board:
                    state_char = self.board[state.pos]

                    if construct == Constructs.LITERAL:
                        match_char = regex_rest[0]
                        
                        if self.case_insensitive:
                            cond = (state_char.lower() == match_char.lower())

                        else:
                            cond = (state_char == match_char)

                    else:
                        avoid_chars = regex_rest[0]
                        
                        if self.case_insensitive:
                            cond = (state_char.lower() not in [char.lower() for char in avoid_chars])

                        else:
                            cond = (state_char not in avoid_chars)
                   
                    if state_char and cond:
                        add_to_display()

                    else:
                        backtrack()
                        continue
                        

            elif construct in [Constructs.ANYCHAR, Constructs.NODISPLAY]:
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
                        
                if construct == Constructs.ANYCHAR:
                    add_to_display()

                else:
                    add_to_match_only()


            elif construct == Constructs.CHARCLASS:
                if not regex_rest[0]:
                    backtrack()
                    continue
                    
                new_state = deepcopy(state)
                state.regex_stack.append(regex)
                new_state.regex_stack.append([Constructs.LITERAL, regex_rest[0].pop(0)])                    
                state_stack.append(new_state)
                

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

                if state.out_of_bounds(self.board): # Todo: Autopad toggle flag
                    backtrack()

                
            elif construct == Constructs.CONCATENATION:
                state.regex_stack.append(regex_rest[1])
                state.regex_stack.append(regex_rest[0])
            

            elif construct == Constructs.ASTERISK:         
                new_state = deepcopy(state)
                new_state.regex_stack.append([Constructs.ASTERISK] + regex_rest)
                new_state.regex_stack.append(regex_rest[1])
                state_stack.append(new_state)

                # Lazy match
                if regex_rest[0]:
                    state_stack[-2:] = state_stack[-2:][::-1]


            elif construct == Constructs.PLUS:
                state.regex_stack.append([Constructs.ASTERISK] + regex_rest)
                state.regex_stack.append(regex_rest[1])

                # Lazy match
                if regex_rest[0]:
                    state_stack[-2:] = state_stack[-2:][::-1]


            elif construct == Constructs.NREPEAT:
                lazy_match, inner_regex, *nums = regex_rest

                if len(nums) == 1: # {n}
                    if nums[0] <= 0:
                        continue

                    else:
                        regex[3] -= 1
                        state.regex_stack.append(regex)
                        state.regex_stack.append(inner_regex)
                        

                elif nums[0] is None: # {,n}
                    if nums[1] <= 0:
                        continue

                    else:
                        new_state = deepcopy(state)
                        new_state.regex_stack.append([Constructs.NREPEAT, lazy_match, inner_regex, nums[1]])
                        
                        state.regex_stack.append(regex)
                        regex[4] -= 1
                        
                        state_stack.append(new_state)

                        if lazy_match:
                            state_stack[-2:] = state_stack[-2:][::-1]


                elif nums[1] is None: # {n,}
                    state.regex_stack.append([Constructs.ASTERISK, lazy_match, inner_regex])
                    state.regex_stack.append([Constructs.NREPEAT, lazy_match, inner_regex, nums[0]])
                    

                else: # {n, m}
                    state.regex_stack.append([Constructs.NREPEAT, lazy_match, inner_regex, None, nums[1] - nums[0]])
                    state.regex_stack.append([Constructs.NREPEAT, lazy_match, inner_regex, nums[0]])


            elif construct == Constructs.OPTIONAL:
                new_state = deepcopy(state)
                new_state.regex_stack.append(regex_rest[1])
                state_stack.append(new_state)

                # Lazy match
                if regex_rest[0]:
                    state_stack[-2:] = state_stack[-2:][::-1]


            elif construct == Constructs.NOCAPTURE:
                raise NotImplementedError
            
##                display_count = state.display_count
##                groups = deepcopy(state.groups)
##                state.regex_stack.append([Constructs.MATCHREMOVE, display_count, groups])
##                state.regex_stack.append(regex_rest[0])


            elif construct == Constructs.MATCHREMOVE:
                raise NotImplementedError
            
##                display_count, groups = regex_rest
##                state.display_count = display_count
##                state.groups = groups

            ## TODO: Make like char class
            elif construct == Constructs.ALTERNATION:
                new_state = deepcopy(state)
                
                state.regex_stack.append(regex_rest[1])
                new_state.regex_stack.append(regex_rest[0])

                state_stack.append(new_state)
                

            elif construct == Constructs.GROUP:
                group_num = regex_rest[0]
                display = state.display
                state.display = set()
                state.regex_stack[-1:] = [[Constructs.GROUPSTORE, group_num, display], regex_rest[1]]
                state_stack.append(state)
            

            elif construct == Constructs.GROUPSTORE:
                group_num, display = regex_rest
                state.groups[group_num] = deepcopy(state.display)
                state.display |= display
                
                state.regex_stack.pop()
                state_stack.append(state)


            elif construct == Constructs.STATIONARY:
                group_num, regex = regex_rest

                state.regex_stack[-1:] = [[Constructs.STATIONARYRESET, deepcopy(state)],
                                          [Constructs.GROUP, group_num, regex]]

                state_stack.append(state)


            elif construct == Constructs.STATIONARYRESET:
                prev_state = regex_rest[0]
                state.regex_stack.pop()

                state.pos = prev_state.pos
                state.dir = prev_state.dir
                state.no_move = prev_state.no_move
                state.no_slip = prev_state.no_slip

                state_stack.append(state)
            

            elif construct == Constructs.LENGTHCHECK:
                group_num1 = regex_rest[0]

                if group_num1 not in state.groups:
                    continue

                group_num2 = regex_rest[1]
                length = state.group_length(group_num1)

                state.regex_stack[-1:] = [[Constructs.LENGTHVERIFY, group_num2, length],
                                          [Constructs.GROUP, group_num2, regex_rest[2]]]

                state_stack.append(state)
            

            elif construct == Constructs.LENGTHVERIFY:
                group_num = regex_rest[0]
                length = regex_rest[1]

                if state.group_length(group_num) == length:
                    state.regex_stack.pop()
                    state_stack.append(state)


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
            

            elif construct == Constructs.ANCHOR:
                char = regex_rest[0]
                state.regex_stack.pop()

                if char.isdigit():
                    digit = int(char)
                    width, height = self.board.width, self.board.height

                    anchor_checks = [state.pos[1] == 0,
                                     state.pos[0] == width - 1 and state.pos[1] == 0,
                                     state.pos[0] == width - 1,
                                     state.pos[0] == width - 1 and state.pos[1] == height - 1,
                                     state.pos[1] == height - 1,
                                     state.pos[0] == 0 and state.pos[1] == height - 1,
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

                elif char.islower():
                    state.anchors[char] = state.pos
                    state_stack.append(state)


                elif char.isupper():                    
                    if char.lower() in state.anchors and state.pos == state.anchors[char.lower()]:
                        state_stack.append(state)


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
    
        
