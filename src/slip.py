"""
Slip v0.5.1 alpha by Sp3000

Requires Python 3.4
"""

from collections import defaultdict
from copy import deepcopy
import sys

from constructs import *
from extra import OrderedSet
from slipparser import SlipParser, InvalidSyntax

DIRECTIONS = [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)]

class State():
    def __init__(self, pos, regex):
        self.pos = pos
        self.dir = (1, 0)
        self.regex_stack = [regex]

        self.match = OrderedSet([])
        
        # Rather than storing all to-display/traversed cells, keep track of those cells
        # in a stack separately and store the index, then pop as appropriate when backtracking
        self.display_count = 0
        self.traversed_count = 0
        
        self.groups = {}
        self.anchors = {}
        
        self.no_move = True
        self.no_slip = False

        self.no_disp_count = 0 # Increases/decreases depending on depth


    def clone(self):
        new_state = State(None, None)

        new_state.pos = self.pos
        new_state.dir = self.dir
        new_state.regex_stack = self.regex_stack[:]

        new_state.match = deepcopy(self.match)
        new_state.display_count = self.display_count
        new_state.traversed_count = self.traversed_count

        new_state.groups = deepcopy(self.groups)
        new_state.anchors = deepcopy(self.anchors)

        new_state.no_move = self.no_move
        new_state.no_slip = self.no_slip

        new_state.no_disp_count = self.no_disp_count

        return new_state


    def next_pos(self):
        return (self.pos[0] + self.dir[0], self.pos[1] + self.dir[1])


    def move(self):
        if self.no_move:
            self.no_move = False

        else:
            self.pos = self.next_pos()


    def rotate_right(self):
        self.dir = (-self.dir[1], self.dir[0])

        
    def rotate_left(self):
        self.dir = (self.dir[1], -self.dir[0])


    def slip_left(self):
        if self.no_slip:
            self.no_slip = False

        else:
            orthog = (self.dir[1], -self.dir[0])
            self.pos = (self.pos[0] + orthog[0], self.pos[1] + orthog[1])


    def slip_right(self):
        if self.no_slip:
            self.no_slip = False

        else:
            orthog = (-self.dir[1], self.dir[0])
            self.pos = (self.pos[0] + orthog[0], self.pos[1] + orthog[1])


    def group_length(self, group_num):
        if group_num not in self.groups:
            return -1

        return len(self.groups[group_num])


    def out_of_bounds(self, board):
        # TODO: Make toggleable with rectangular grid
        return self.pos not in board


    def wrap(self, board):
        # Need to make more efficient
        new_y = self.pos[1] % board.height

        row_length = max(p[0] for p in board if p[1] == new_y) + 1
        new_x = self.pos[0] % row_length
        self.pos = (new_x, new_y)

        
class Board():
    def __init__(self, input_string, padding=False):
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

        # Experimental
        if padding:
            for x in range(self.width):
                for y in range(self.height):
                    if (x, y) not in self.board_dict:
                        self.board_dict[(x, y)] = ""


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
    def __init__(self, regex, config=""):
        try:
            self.regex = SlipParser().parser.parse(regex)
            
        except InvalidSyntax as e:
            if "!" in config: # For online interpreter only
                raise e

            else:
                print(e, file=sys.stderr)
                exit()
            
        
        self.recurse_regexes = {}
        self.config = config.lower()

        self.case_insensitive = "i" in config
        self.no_repeat = "r" in config        
        self.verbose = "v" in config
        self.debug = "d" in config
        self.wrapping = "w" in config
        self.padding = "g" in config

        self.__number_groups(self.regex)


    def __number_groups(self, regex):
        # TODO: Fix this terrible, terrible code
        numbering_stack = [regex]
        capture_group_num = 1
        no_capture_num = -1
        
        while numbering_stack:
            curr_regex = numbering_stack.pop()

            if type(curr_regex) in [StationaryGroup, NoDisplayGroup, Group]:
                curr_regex.group_num = capture_group_num
                self.recurse_regexes[curr_regex.group_num] = curr_regex.inner
                capture_group_num += 1

            elif type(curr_regex) in [LengthAssert, NoDisplayMatchGroup, NoMatchGroup]:
                curr_regex.group_num = no_capture_num
                self.recurse_regexes[curr_regex.group_num] = curr_regex.inner
                no_capture_num += 1

            else:
                continue

            for child in list(curr_regex)[::-1]:
                numbering_stack.append(child)


    def match(self, input_string, output=False):
        self.board = Board(input_string, self.padding)

        if "f" in self.config:
            result = self.__match_first()

        elif "o" in self.config:
            result = self.__match_all()

        else:
            result = self.__match_one()

        if "n" in self.config:
            if output:
                print(len(result))

            return len(result)

        elif "s" in self.config:
            if output:
                for pos, match in result:
                    print(*pos)

            return {r[0] for r in result}

        elif "p" in self.config:
            if output:
                for pos, match in result:
                    print(*match)

            return result

        else:
            # TODO: Expand to return actual strings rather than positions
            if output:
                for i, (pos, match) in enumerate(result):
                    if i > 0:
                        print()
                        
                    self.__output(pos, match)

            return result


    def __match_one(self):
        found = []

        for pos in self.board:
            try:
                result = next(self.__match(pos))
                if result and result in [pair[1] for pair in found]:
                    continue

                found.append((pos, result))

            except StopIteration:
                continue

        return found


    def __match_all(self):
        found = []

        for pos in self.board:
            for result in self.__match(pos):
                if result and result in [pair[1] for pair in found]:
                    continue

                found.append((pos, result))

        return found


    def __match_first(self):
        for pos in self.board:
            try:
                result = next(self.__match(pos))
                return [(pos, result)]

            except StopIteration:
                continue

        return []


    def __match(self, pos):
        state_stack = [State(pos, self.regex)]
        display_set = OrderedSet([])
        traversed_set = OrderedSet([])
        

        def backtrack():
            state_stack.pop()
            
            if state_stack:
                last = state_stack[-1]
                display_set.keep(last.display_count)
                traversed_set.keep(last.traversed_count)


        def add_to_match_only(arg=None):            
            state.match.add(arg if arg is not None else state.pos)


        def add_to_display():
            add_to_match_only(state.pos)

            if state.no_disp_count > 0:
                return
            
            display_set.add(state.pos)
            state.display_count = len(display_set)


        def add_to_traversed():
            traversed_set.add(state.pos)
            state.traversed_count = len(traversed_set)


        while state_stack:
            state = state_stack[-1]

            if not state.regex_stack:
                if self.debug:
                    # To be changed later
                    print(state.groups, flush=True)
                    
                yield set(display_set)
                backtrack()
                continue

            construct = state.regex_stack.pop()

            # print(construct, state.regex_stack)

            if type(construct) in [Literal, NegatedCharClass, AnyChar]:
                state.move()

                if state.out_of_bounds(self.board):
                    if self.wrapping:
                        state.wrap(self.board)
                    else:
                        backtrack()
                        continue

                if self.no_repeat:
                    if state.pos in traversed_set:
                        backtrack()
                        continue

                    else:
                        add_to_traversed()

                state_char = self.board[state.pos]

                if isinstance(construct, Empty):
                    continue
                
                elif isinstance(construct, Literal):
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


            elif isinstance(construct, Alternation):
                new_state = state.clone()

                state.regex_stack.append(construct.right)
                new_state.regex_stack.append(construct.left)

                state_stack.append(new_state)


            elif isinstance(construct, Asterisk):
                new_state = state.clone()
                new_state.regex_stack.append(construct)
                new_state.regex_stack.append(construct.inner)
                state_stack.append(new_state)

                if construct.lazy_match:
                    state_stack[-2:] = state_stack[-2:][::-1]


            elif isinstance(construct, Plus):
                state.regex_stack.append(Asterisk(construct.inner, construct.lazy_match))
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
                    
                    if n <= 0:
                        continue

                    else:
                        new_regex = NRepeat(construct.inner, construct.lazy_match, n-1, n-1)
                        state.regex_stack.append(new_regex)
                        state.regex_stack.append(construct.inner)

                elif construct.low is None: # {,n}
                    n = construct.high
                    
                    if n <= 0:
                        continue

                    else:
                        new_state = state.clone()
                        new_regex1 = NRepeat(construct.inner, construct.lazy_match, n, n)
                        new_state.regex_stack.append(new_regex1)

                        new_regex2 = NRepeat(construct.inner, construct.lazy_match, None, n-1)
                        state.regex_stack.append(new_regex2)

                        state_stack.append(new_state)

                        if construct.lazy_match:
                            state_stack[-2:] = state_stack[-2:][::-1]

                elif construct.high is None: # {n,}
                    n = construct.low

                    state.regex_stack.append(Asterisk(construct.inner, construct.lazy_match))
                    state.regex_stack.append(NRepeat(construct.inner, construct.lazy_match, n, n))

                else: # {m, n}
                    m = construct.low
                    n = construct.high

                    state.regex_stack.append(NRepeat(construct.inner, construct.lazy_match, None, n-m))
                    state.regex_stack.append(NRepeat(construct.inner, construct.lazy_match, m, m))                        


            elif isinstance(construct, Group):
                match = state.match
                state.match = set()
                state.regex_stack.append(GroupStore(construct.group_num, match))
                state.regex_stack.append(construct.inner)


            elif isinstance(construct, GroupStore):
                group_num = construct.group_num                
                state.groups[group_num] = deepcopy(state.match)
                state.match |= construct.prev_match


            elif isinstance(construct, NoMatchGroup):
                state.regex_stack.append(construct.inner)


            elif isinstance(construct, NoDisplayGroup):
                state.no_disp_count += 1
                state.regex_stack.append(NoDisplayDecrement())
                state.regex_stack.append(Group(construct.group_num, construct.inner))


            elif isinstance(construct, NoDisplayMatchGroup):
                state.no_disp_count += 1
                state.regex_stack.append(NoDisplayDecrement())
                state.regex_stack.append(construct.inner)


            elif isinstance(construct, StationaryGroup):
                state.regex_stack.append(StationaryReset(state.pos, state.dir,
                                                         state.no_move, state.no_slip))
                state.regex_stack.append(Group(construct.group_num, construct.inner))


            elif isinstance(construct, StationaryReset):
                state.pos = construct.pos
                state.dir = construct.dir
                state.no_move = construct.no_move
                state.no_slip = construct.no_slip


            elif isinstance(construct, LengthAssert):
                if construct.equal_to not in state.groups:
                    backtrack()
                    continue

                length = state.group_length(construct.equal_to)
                state.regex_stack.append(LengthCheck(construct.group_num, length))
                state.regex_stack.append(Group(construct.group_num, construct.inner))
                

            elif isinstance(construct, LengthCheck):
                if state.group_length(construct.group_num) != construct.length:
                    backtrack()
                    continue


            elif isinstance(construct, NoDisplay):
                state.no_disp_count += 1
                
                state.regex_stack.append(NoDisplayDecrement())
                state.regex_stack.append(AnyChar())


            elif isinstance(construct, NoMatch):
                state.regex_stack.append(AnyChar())


            elif isinstance(construct, NoDisplayMatch):
                state.no_disp_count += 1
                state.regex_stack.append(NoDisplayDecrement())
                state.regex_stack.append(AnyChar())


            elif isinstance(construct, NoDisplayDecrement):
                state.no_disp_count -= 1
                assert state.no_disp_count >= 0


            elif isinstance(construct, Recursive):                
                if construct.group_num:
                    state.regex_stack.append(self.recurse_regexes[construct.group_num])

                else:
                    state.regex_stack.append(self.regex)
                
                
            elif isinstance(construct, Command):
                command = construct.char

                if command == ">":
                    state.rotate_right()
                    
                elif command == "<":
                    state.rotate_left()

                elif command == "/":
                    state.slip_left()

                elif command == "\\":
                    state.slip_right()

                elif command == "#":                    
                    state.no_move = True

                elif command == "%":
                    state.no_slip = True

                if state.out_of_bounds(self.board):
                    if self.wrapping:
                        state.wrap(self.board)

                    else:
                        backtrack()
                        continue


            elif isinstance(construct, Anchor):
                char = construct.char

                if char in "01234567+*^":
                    width, height = self.board.width, self.board.height

                    anchor_checks = [state.pos[1] == 0,
                                     state.pos[0] == width - 1 and state.pos[1] == 0,
                                     state.pos[0] == width - 1,
                                     state.pos[0] == width - 1 and state.pos[1] == height - 1,
                                     state.pos[1] == height - 1,
                                     state.pos[0] == 0 and state.pos[1] == height - 1,
                                     state.pos[0] == 0,
                                     state.pos[0] == 0 and state.pos[1] == 0]

                    if char == "*":
                        if not any(anchor_checks[::2]):
                            backtrack()
                            continue

                    elif char == "+":
                        if not any(anchor_checks[1::2]):
                            backtrack()
                            continue

                    elif char == "^":
                        new_pos = state.next_pos()

                        if new_pos in self.board:
                            backtrack()
                            continue

                    else:
                        if not anchor_checks[int(char)]:
                            backtrack()
                            continue


                elif char.islower():
                    state.anchors[char] = state.pos
                    

                elif char.isupper():                    
                    if char.lower() not in state.anchors or state.pos != state.anchors[char.lower()]:
                        backtrack()
                        continue


            elif isinstance(construct, Directional):
                char = construct.char
                
                if char in "01234567+*":
                    if char == "*":
                        indices = [0, 1, 2, 3, 4, 5, 6, 7]

                    elif char == "+":
                        indices = [0, 2, 4, 6]

                    else:
                        indices = [int(char)]

                    dirs_ = [DIRECTIONS[i] for i in indices]
                    state.regex_stack.append(DirectionCheck(dirs_))

                elif char == "T":
                    state.regex_stack.append(Alternation(Command("<"), Command(">")))


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


    def __output(self, pos, cells):
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
                print()

        else:
            if self.verbose:
                print("Match found in rectangle: ({}, {}), ({}, {})".format(
                       min_x, min_y, max_x, max_y), flush=True)

            array = [[""]*(max_x - min_x + 1)
                     for _ in range(min_y, max_y + 1)]

            for pos in cells:
                array[pos[1]-min_y][pos[0]-min_x] = self.board[pos]

            for row in array:
                non_empty = max([-1] + list(filter(row.__getitem__, range(len(row)))))
                print("".join(c if c else " " for c in row[:non_empty+1]), flush=True)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        input_filepath = input("Enter input filepath: ")
        regex = input("Enter regex: ")
        config = input("Enter config string: ")

        with open(input_filepath) as inputfile:
            input_string = inputfile.read()

    elif len(sys.argv) == 2:
        print("Missing file: Need both regex and input files", file=sys.stderr)
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

    slip = Slip(regex, config)
    slip.match(input_string, output=True)
                    
