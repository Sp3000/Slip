# http://www.cs.sfu.ca/~cameron/Teaching/384/99-3/regexp-plg.html
# http://www.dabeaz.com/ply/

from enum import Enum
import sys
import string

from ply import lex
from ply import yacc

from constructs import *
from extra import *


class InvalidSyntax(Exception):
    pass

    
class SlipLexer():
    def __init__(self):
        self.lexer = lex.lex(module=self)
        
    tokens = ("DIGIT",
              "OTHER",
              "ESCAPED")

    literals = [c for c in string.printable if not c.isdigit()]


    def t_DIGIT(self, t):
        r"\d"
        return t


    def t_OTHER(self, t):
        r"[^!-~]"
        return t


    def t_ESCAPED(self, t):
        r"`[^a-zA-Z]"
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
        

    def p_re(self, p):
        """re : alternation
              | simple
              | empty"""
        p[0] = p[1]


    def p_empty(self, p):
        """empty :"""
        p[0] = Empty()


    def p_alternation(self, p):
        """alternation : re '|' simple
                       | re '|' empty"""
        p[0] = Alternation(p[1], p[3])


    def p_simple(self, p):
        """simple : concatenation
                  | basic"""
        p[0] = p[1]


    def p_concatenation(self, p):
        """concatenation : simple basic"""
        p[0] = Concatenation(p[1], p[2])


    def p_basic(self, p):
        """basic : elementary
                 | quantifier"""
        p[0] = p[1]


    def p_quantifier(self, p):
        """quantifier : basequantifier
                      | basequantifier '?'"""

        p[1].lazy_match = len(p) > 2
        p[0] = p[1]


    def p_basequantifier(self, p):
        """basequantifier : asterisk
                          | plus
                          | optional
                          | nrepeat"""

        p[0] = p[1]


    def p_elementary(self, p):
        """elementary : group
                      | directional
                      | command
                      | literal
                      | charclass
                      | anychar
                      | nodisplay
                      | nomatch
                      | nodispmatch
                      | anchor
                      | predefined"""
        p[0] = p[1]


    def p_asterisk(self, p):
        """asterisk : elementary '*'"""
        p[0] = Asterisk(p[1], False)


    def p_plus(self, p):
        """plus : elementary '+'"""
        p[0] = Plus(p[1], False)


    def p_optional(self, p):
        """optional : elementary '?'"""
        p[0] = Optional(p[1], False)


    def p_nrepeat(self, p):
        """nrepeat : elementary '{' number '}'
                   | elementary '{' ',' number '}'
                   | elementary '{' number ',' '}'
                   | elementary '{' number ',' number '}'"""

        if len(p) == 5:
            p[0] = NRepeat(p[1], False, p[3], p[3])

        elif len(p) == 6:
            if p[3] == ",":
                p[0] = NRepeat(p[1], False, None, p[4])

            else:
                p[0] = NRepeat(p[1], False, p[3], None)

        else:
            p[0] = NRepeat(p[1], False, p[3], p[5])
        

    def p_anychar(self, p):
        """anychar : '.'"""
        p[0] = AnyChar()


    def p_nodisplay(self, p):
        """nodisplay : ','"""
        p[0] = NoDisplay()


    def p_nomatch(self, p):
        """nomatch : ':'"""
        p[0] = NoMatch()


    def p_nodispmatch(self, p):
        """nodispmatch : ';'"""
        p[0] = NoDisplayMatch()


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
                        | ':' nomatchgroup
                        | ',' nodispgroup
                        | ';' nodispmatchgroup
                        | recursive"""

        if len(p) == 3:
            p[0] = p[2]

        else:
            p[0] = p[1]


    def p_lengthcheck(self, p):
        """lengthcheck : '(' number ')' re"""
        p[0] = LengthAssert(-1, p[2], p[4])


    def p_stationarygroup(self, p):
        """stationarygroup : re"""
        p[0] = StationaryGroup(-1, p[1])


    def p_nomatchgroup(self, p):
        """nomatchgroup : re"""
        p[0] = NoMatchGroup(p[1])


    def p_nodispgroup(self, p):
        """nodispgroup : re"""
        p[0] = NoDisplayGroup(-1, p[1])


    def p_nodispmatchgroup(self, p):
        """nodispmatchgroup : re"""
        p[0] = NoDisplayMatchGroup(p[1])


    def p_recursive(self, p):
        """recursive : 'R'
                     | number"""

        if p[1] == "R":
            p[0] = Recursive(None)

        else:
            p[0] = Recursive(p[1])
        

    def p_basicgroup(self, p):
        """basicgroup : re"""        
        p[0] = Group(-1, p[1])


    def p_charclass(self, p):
        """charclass : '[' classitems ']'"""
        p[0] = p[2]


    def p_classitems(self, p):
        """classitems : '^' baseitems
                      | classitems2"""

        if len(p) == 3:
            p[0] = NegatedCharClass(p[2])

        else:
            p[0] = p[1]


    def p_classitems2(self, p):
        """classitems2 : baseitems
                       | baseitems '|' baseitems"""

        if len(p) == 2:
            p[0] = CharClass(p[1])

        else:
            p[0] = CharClass([c for c in p[1] if c not in p[3]])


    def p_baseitems(self, p):
        """baseitems : classatom
                     | classatom baseitems"""


        if len(p) == 2:
            p[0] = p[1]

        else:
            p[0] = p[1] + p[2]


    def p_classatom(self, p):
        """classatom : classliteral
                     | classrange"""

        if isinstance(p[1], list):
            p[0] = p[1]

        else:
            p[0] = [p[1]]
        

    def p_classliteral(self, p):
        r"""classliteral : '!'
                         | '"'
                         | '#'
                         | '$'
                         | '%'
                         | '&'
                         | '\''
                         | '('
                         | ')'
                         | '*'
                         | '+'
                         | ','
                         | '.'
                         | '/'
                         | ':'
                         | ';'
                         | '<'
                         | '='
                         | '>'
                         | '?'
                         | '@'
                         | '['
                         | '\\'
                         | '_'
                         | '`'
                         | '{'
                         | '}'
                         | '~'
                         | literal"""

        # There's got to be a better way...
        # Missing from the above is space/tab and '^]|-'

        if isinstance(p[1], str):
            p[0] = p[1]

        else:
            p[0] = p[1].char


    def p_classrange(self, p):
        """classrange : classliteral '-' classliteral"""

        p[0] = [chr(c) for c in range(ord(p[1]), ord(p[3])+1)]


    def p_predefined(self, p):
        """predefined : '`' alpha"""

        if p[2].lower() in classes:
            if p[2].islower():
                p[0] = CharClass(list(classes[p[2]]))

            else:
                p[0] = NegatedCharClass(list(classes[p[2].lower()]))

        else:
            raise NotImplementedError


    def p_directional(self, p):
        """directional : '^' DIGIT
                       | '^' alpha
                       | '^' '*'
                       | '^' '+'"""

        p[0] = Directional(p[2])


    def p_anchor(self, p):
        """anchor : '$' DIGIT
                  | '$' alpha
                  | '$' '*'
                  | '$' '+'
                  | '$' '^'"""
        
        p[0] = Anchor(p[2])
            

    def p_command(self, p):
        r"""command : '>'
                    | '<'
                    | '/'
                    | '\\'
                    | '#'
                    | '%' """
        
        p[0] = Command(p[1])


    def p_literal(self, p):
        """literal : ESCAPED
                   | alpha
                   | DIGIT
                   | OTHER"""
        
        p[0] = Literal(p[1])


    def p_alpha(self, p):
        """alpha : alpha_lower
                 | alpha_upper"""

        p[0] = p[1]


    def p_alpha_lower(self, p):
        """alpha_lower : 'a'
                       | 'b'
                       | 'c'
                       | 'd'
                       | 'e'
                       | 'f'
                       | 'g'
                       | 'h'
                       | 'i'
                       | 'j'
                       | 'k'
                       | 'l'
                       | 'm'
                       | 'n'
                       | 'o'
                       | 'p'
                       | 'q'
                       | 'r'
                       | 's'
                       | 't'
                       | 'u'
                       | 'v'
                       | 'w'
                       | 'x'
                       | 'y'
                       | 'z'"""

        p[0] = p[1]


    def p_alpha_upper(self, p):
        """alpha_upper : 'A'
                       | 'B'
                       | 'C'
                       | 'D'
                       | 'E'
                       | 'F'
                       | 'G'
                       | 'H'
                       | 'I'
                       | 'J'
                       | 'K'
                       | 'L'
                       | 'M'
                       | 'N'
                       | 'O'
                       | 'P'
                       | 'Q'
                       | 'R'
                       | 'S'
                       | 'T'
                       | 'U'
                       | 'V'
                       | 'W'
                       | 'X'
                       | 'Y'
                       | 'Z'"""

        p[0] = p[1]
        

    def p_error(self, p):
        if p is None:
            raise InvalidSyntax("Unexpected end of input")

        else:
            raise InvalidSyntax("Syntax error at '%s'\n" % p.value)


if __name__ == "__main__":
    code = "|a"
    
    parser = SlipParser().parser
    print(parser.parse(code)) # Debugging
