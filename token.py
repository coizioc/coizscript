from enum import Enum, auto


class TokenType(Enum):
    # One character tokens
    LEFT_PAREN = auto()
    RIGHT_PAREN = auto()
    LEFT_BRACKET = auto()
    RIGHT_BRACKET = auto()
    LEFT_BRACE = auto()
    RIGHT_BRACE = auto()
    COMMA = auto()
    DOT = auto()
    MINUS = auto()
    PERCENT = auto()
    PLUS = auto()
    SEMICOLON = auto()
    SLASH = auto()
    STAR = auto()
    GRAVE = auto()

    # One or two character tokens
    BANG = auto()
    BANG_EQUAL = auto()
    EQUAL = auto()
    EQUAL_EQUAL = auto()
    GREATER = auto()
    GREATER_EQUAL = auto()
    LESS = auto()
    LESS_EQUAL = auto()
    PLUS_EQUAL = auto()
    MINUS_EQUAL = auto()
    STAR_EQUAL = auto()
    SLASH_EQUAL = auto()
    
    # Literals
    IDENTIFIER = auto()
    STRING = auto()
    CODE = auto()
    NUMBER = auto()

    # Keywords
    AND = auto()
    ASSERT = auto()
    CLASS = auto()
    ELSE = auto()
    FALSE = auto()
    FUNC = auto()
    FOR = auto()
    IF = auto()
    IMPORT = auto()
    LEN = auto()
    NIL = auto()
    OR = auto()
    PRINT = auto()
    RETURN = auto()
    SUPER = auto()
    THIS = auto()
    TRUE = auto()
    VAR = auto()
    WHILE = auto()
    
    EOF = auto()


class Token():
    def __init__(self, token_type, lexeme, literal, line):
        self.type = token_type
        self.lexeme = lexeme
        self.literal = literal
        self.line = line

    def __repr__(self):
        return f"{TokenType(self.type).name} {self.lexeme} {self.literal}"

    def __str__(self):
        return self.__repr__()