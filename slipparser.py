# http://www.cs.sfu.ca/~cameron/Teaching/384/99-3/regexp-plg.html
# http://www.dabeaz.com/ply/

from enum import Enum

import ply.lex as lex
import ply.yacc as yacc


class Constructs(Enum):
    (ALTERNATION,
     CONCATENATION,
     COMMAND,
     LITERAL,
     CHARCLASS,
     NEGCHARCLASS,
     ASTERISK,
     PLUS,
     OPTIONAL,
     GROUP,
     GROUPSTORE,
     STATIONARY,
     STATIONARYRESET,
     LENGTHCHECK,
     LENGTHVERIFY,
     DIRECTIONSET,
     ANYCHAR,
     NEGLITERAL,
     ANCHOR) = range(19)
    
    
class SlipLexer():
    def __init__(self):
        self.lexer = lex.lex(module=self)
        
    tokens = ("PIPE",
              "LPARENS",
              "RPARENS",
              "LSQBRACKET",
              "RSQBRACKET",
              "CARET",
              "QMARK",
              "EMARK",
              "EQUALS",
              "ASTERISK",
              "PLUS",
              "UNDERSCORE",
              "DOT",
              "DOLLAR",
              "COMMAND",
              "DIGIT",
              "LITERAL")

    # Tokens
    t_PIPE = r"\|"
    t_LPARENS = r"\("
    t_RPARENS = r"\)"
    t_LSQBRACKET = r"\["
    t_RSQBRACKET = r"\]"
    t_CARET = r"\^"
    t_QMARK = r"\?"
    t_EMARK = r"!"
    t_EQUALS = r"="
    t_ASTERISK = r"\*"
    t_PLUS = r"\+"
    t_UNDERSCORE = r"_"
    t_DOT = r"\."
    t_DIGIT = r"\d"
    t_DOLLAR = r"\$"

    def t_COMMAND(self, t):
        r"[<>/\\]"
        return t


    def t_LITERAL(self, t):
        r"`.|[^][|()^?!=*+_.$0-9]"
        t.value = t.value[t.value[0] == "`"]
        return t


    def t_error(self, t):
        print("Illegal character '%s'" % t.value[0])
        raise Exception

    
class SlipParser():
    def __init__(self):
        self.tokens = SlipLexer.tokens
        self.lexer = SlipLexer().lexer
        self.parser = yacc.yacc(module=self)
        self.groupnum = 1
        

    def p_re(self, p):
        """re : alternation
              | simple"""
        p[0] = p[1]


    def p_alternation(self, p):
        """alternation : re PIPE simple"""
        p[0] = [Constructs.ALTERNATION, p[1], p[3]]


    def p_simple(self, p):
        """simple : concatenation
                  | basic"""
        p[0] = p[1]


    def p_concatenation(self, p):
        """concatenation : simple basic"""
        p[0] = [Constructs.CONCATENATION, p[1], p[2]]


    def p_basic(self, p):
        """basic : elementary
                 | asterisk
                 | plus
                 | optional"""
        p[0] = p[1]


    def p_elementary(self, p):
        """elementary : group
                      | directionset
                      | command
                      | literal
                      | charclass
                      | any
                      | anchor"""
        p[0] = p[1]


    def p_asterisk(self, p):
        """asterisk : elementary ASTERISK"""
        p[0] = [Constructs.ASTERISK, p[1]]


    def p_plus(self, p):
        """plus : elementary PLUS"""
        p[0] = [Constructs.PLUS, p[1]]


    def p_optional(self, p):
        """optional : elementary QMARK"""
        p[0] = [Constructs.OPTIONAL, p[1]]


    def p_any(self, p):
        """any : DOT"""
        p[0] = [Constructs.ANYCHAR]


    def p_number(self, p):
        """number : DIGIT
                  | DIGIT number"""

        if len(p) == 2:
            p[0] = int(p[1])

        else:
            p[0] = p[2] + 10 * int(p[1])


    def p_group(self, p):
        """group : LPARENS groupbody RPARENS"""
        p[0] = p[2]


    def p_groupbody(self, p):
        """groupbody : QMARK specialgroup
                     | basicgroup"""

        if len(p) == 2:
            p[0] = p[1]

        else:
            p[0] = p[2]


    def p_specialgroup(self, p):
        """specialgroup : UNDERSCORE lengthcheck
                        | PIPE stationarygroup"""
        p[0] = p[2]


    def p_lengthcheck(self, p):
        """lengthcheck : LPARENS number RPARENS re"""
        p[0] = [Constructs.LENGTHCHECK, p[2], self.groupnum, p[4]]
        self.groupnum += 1


    def p_stationarygroup(self, p):
        """stationarygroup : re"""
        p[0] = [Constructs.STATIONARY, self.groupnum, p[1]]
        self.groupnum += 1
        

    def p_basicgroup(self, p):
        """basicgroup : re"""
        p[0] = [Constructs.GROUP, self.groupnum, p[1]]
        self.groupnum += 1


    def p_charclass(self, p):
        """charclass : pcharclass
                     | ncharclass"""
        p[0] = p[1]


    def p_pcharclass(self, p):
        """pcharclass : LSQBRACKET classitems RSQBRACKET"""
        p[0] = [Constructs.CHARCLASS, p[2]]


    def p_ncharclass(self, p):
        """ncharclass : LSQBRACKET CARET classitems RSQBRACKET"""
        p[0] = [Constructs.NEGCHARCLASS, p[3]]


    def p_classitems(self, p):
        """classitems : literal
                      | literal classitems"""

        if len(p) == 2:
            p[0] = [p[1]]

        else:
            p[0] = [p[1]] + p[2]


    def p_directionset(self, p):
        """directionset : CARET DIGIT"""
        p[0] = [Constructs.DIRECTIONSET, int(p[2])]


    def p_anchor(self, p):
        """anchor : DOLLAR DIGIT"""
        p[0] = [Constructs.ANCHOR, int(p[2])]
            

    def p_command(self, p):
        """command : COMMAND"""
        p[0] = [Constructs.COMMAND, p[1]]


    def p_literal(self, p):
        """literal : LITERAL
                   | DIGIT"""
        p[0] = [Constructs.LITERAL, p[1]]


    def p_error(self, p):
        print("Syntax error at '%s'" % p.value)
        exit()


if __name__ == "__main__":
    parser = SlipParser().parser
    print(parser.parse("(?_(10)abc)"))
