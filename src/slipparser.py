# http://www.cs.sfu.ca/~cameron/Teaching/384/99-3/regexp-plg.html
# http://www.dabeaz.com/ply/

from enum import Enum

import ply.lex as lex
import ply.yacc as yacc

import string


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
     DIRECTIONCHECK,
     ANYCHAR,
     ANCHOR,
     NREPEAT,
     NOCAPTURE,
     MATCHREMOVE,
     NODISPLAY) = range(23)
    
    
class SlipLexer():
    def __init__(self):
        self.lexer = lex.lex(module=self)
        
    tokens = ("ALPHA",
              "DIGIT",
              "ESCAPED")

    literals = [c for c in string.printable if not c.isalnum()]


    def t_ALPHA(self, t):
        r"[a-zA-Z]"
        return t


    def t_DIGIT(self, t):
        r"\d"
        return t


    def t_ESCAPED(self, t):
        r"`."
        t.value = t.value[1]
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
        """alternation : re '|' simple"""
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
                 | optional
                 | nrepeat"""
        p[0] = p[1]


    def p_elementary(self, p):
        """elementary : group
                      | directionset
                      | command
                      | literal
                      | charclass
                      | any
                      | nodisplay
                      | anchor"""
        p[0] = p[1]


    def p_asterisk(self, p):
        """asterisk : elementary '*'"""
        p[0] = [Constructs.ASTERISK, p[1]]


    def p_plus(self, p):
        """plus : elementary '+'"""
        p[0] = [Constructs.PLUS, p[1]]


    def p_optional(self, p):
        """optional : elementary '?'"""
        p[0] = [Constructs.OPTIONAL, p[1]]


    def p_nrepeat(self, p):
        """nrepeat : elementary '{' number '}'
                   | elementary '{' ',' number '}'
                   | elementary '{' number ',' '}'
                   | elementary '{' number ',' number '}'"""

        if len(p) == 5:
            p[0] = [Constructs.NREPEAT, p[1], p[3]]

        elif len(p) == 6:
            if p[3] == ",":
                p[0] = [Constructs.NREPEAT, p[1], None, p[4]]

            else:
                p[0] = [Constructs.NREPEAT, p[1], p[3], None]

        else:
            p[0] = [Constructs.NREPEAT, p[1], p[3], p[5]]
        

    def p_any(self, p):
        """any : '.'"""
        p[0] = [Constructs.ANYCHAR]


    def p_nodisplay(self, p):
        """nodisplay : '!'"""
        p[0] = [Constructs.NODISPLAY]


    def p_number(self, p):
        """number : DIGIT
                  | DIGIT number"""

        if len(p) == 2:
            p[0] = int(p[1])

        else:
            p[0] = p[2] + 10 * int(p[1])


    def p_group(self, p):
        """group : '(' groupbody ')'"""
        p[0] = p[2]


    def p_groupbody(self, p):
        """groupbody : '?' specialgroup
                     | basicgroup"""

        if len(p) == 2:
            p[0] = p[1]

        else:
            p[0] = p[2]


    def p_specialgroup(self, p):
        """specialgroup : '_' lengthcheck
                        | '|' stationarygroup
                        | ':' nocapture"""
        p[0] = p[2]


    def p_lengthcheck(self, p):
        """lengthcheck : '(' number ')' re"""
        p[0] = [Constructs.LENGTHCHECK, p[2], self.groupnum, p[4]]
        self.groupnum += 1


    def p_stationarygroup(self, p):
        """stationarygroup : re"""
        p[0] = [Constructs.STATIONARY, self.groupnum, p[1]]
        self.groupnum += 1


    def p_nocapture(self, p):
        """nocapture : re"""
        p[0] = [Constructs.NOCAPTURE, p[1]]
        

    def p_basicgroup(self, p):
        """basicgroup : re"""
        p[0] = [Constructs.GROUP, self.groupnum, p[1]]
        self.groupnum += 1


    def p_charclass(self, p):
        """charclass : pcharclass
                     | ncharclass"""
        p[0] = p[1]


    def p_pcharclass(self, p):
        """pcharclass : '[' classitems ']'"""
        p[0] = [Constructs.CHARCLASS, p[2]]


    def p_ncharclass(self, p):
        """ncharclass : '[' '^' classitems ']'"""
        p[0] = [Constructs.NEGCHARCLASS, p[3]]


    def p_classitems(self, p):
        """classitems : literal
                      | literal classitems"""

        if len(p) == 2:
            p[0] = [p[1]]

        else:
            p[0] = [p[1]] + p[2]


    def p_directionset(self, p):
        """directionset : '^' DIGIT"""
        p[0] = [Constructs.DIRECTIONSET, int(p[2])]


    def p_anchor(self, p):
        """anchor : '$' DIGIT"""
        p[0] = [Constructs.ANCHOR, int(p[2])]
            

    def p_command(self, p):
        """command : '>'
                   | '<'
                   | '/'
                   | '\\\\'
                   | '#'
                   | '%' """
        p[0] = [Constructs.COMMAND, p[1]]


    def p_literal(self, p):
        """literal : ESCAPED
                   | ALPHA
                   | DIGIT"""
        p[0] = [Constructs.LITERAL, p[1]]


    def p_error(self, p):
        print("Syntax error at '%s'" % p.value)
        exit()


if __name__ == "__main__":
    parser = SlipParser().parser
    print(parser.parse("``"))
