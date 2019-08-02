from token import Token, TokenType
from keywords import KEYWORDS


class Scanner():
    def __init__(self, source, filename):
        self.source = source
        self.filename = filename
        self.start = 0
        self.current = 0
        self.line = 1
        self.tokens = []
        self.has_error = False

    def print_error(self, line, message):
        print(f"[{self.filename}, line {line}] Error: {message}")
        self.has_error = True

    def advance(self):
        self.current += 1
        return self.source[self.current - 1]

    def match(self, expected):
        # Advances current if match is expected, otherwise current is unchanged.
        if self.is_at_end():
            return False
        if self.source[self.current] != expected:
            return False

        self.current += 1
        return True

    def peek(self):
        if self.is_at_end():
            return '\0'
        return self.source[self.current]

    def peek_next(self):
        if self.current + 1 > len(self.source):
            return '\0'
        return self.source[self.current + 1]

    def handle_code(self):
        # Advance until terminating ` or EOF is found.
        while self.peek() != '`' and not self.is_at_end():
            if self.peek() == '\n':
                self.line += 1
            self.advance()

        if self.is_at_end():
            self.print_error(self.line, "Unterminated code.")
            return

        # The closing "
        self.advance()

        # Trim the surrounding quotes
        value = self.source[self.start + 1: self.current - 1]
        self.add_token(TokenType.CODE, value)

    def handle_string(self):
        # Advance until terminating " or EOF is found.
        while self.peek() != '"' and not self.is_at_end():
            if self.peek() == '\n':
                self.line += 1
            self.advance()

        if self.is_at_end():
            self.print_error(self.line, "Unterminated string.")
            return

        # The closing "
        self.advance()

        # Trim the surrounding quotes
        value = self.source[self.start + 1: self.current - 1]
        self.add_token(TokenType.STRING, value)

    def handle_number(self):
        # Advance while current is a digit.
        while self.peek().isdigit():
            self.advance()

        # Handle floats.
        if self.peek() == '.' and self.peek_next().isdigit():
            self.advance()
            while self.peek().isdigit():
                self.advance()
        self.add_token(TokenType.NUMBER, float(self.source[self.start:self.current]))

    def handle_identifier(self):
        # Advance while current character is an alphanumeric character or an underscore.
        while self.peek().isalnum() or self.peek() == '_':
            self.advance()
        text = self.source[self.start:self.current]

        # Determine if word is an identifier or a keyword.
        if text not in KEYWORDS.keys():
            self.add_token(TokenType.IDENTIFIER)
        else:
            self.add_token(KEYWORDS[text])

    def is_at_end(self):
        return self.current >= len(self.source)

    def add_token(self, tok, literal=None):
        text = self.source[self.start:self.current]
        self.tokens.append(Token(tok, text, literal, self.line))

    def scan_tokens(self):
        while not self.is_at_end():
            self.start = self.current
            self.scan_token()
        self.tokens.append(Token(TokenType.EOF, "", None, self.line))

    def scan_token(self):
        curr_tok = None
        curr_char = self.advance()

        # Single character operators
        if curr_char == '(':
            curr_tok = TokenType.LEFT_PAREN
        elif curr_char == ')':
            curr_tok = TokenType.RIGHT_PAREN
        elif curr_char == '[':
            curr_tok = TokenType.LEFT_BRACKET
        elif curr_char == ']':
            curr_tok = TokenType.RIGHT_BRACKET
        elif curr_char == '{':
            curr_tok = TokenType.LEFT_BRACE
        elif curr_char == '}':
            curr_tok = TokenType.RIGHT_BRACE
        elif curr_char == ',':
            curr_tok = TokenType.COMMA
        elif curr_char == '.':
            curr_tok = TokenType.DOT
        elif curr_char == '%':
            curr_tok = TokenType.PERCENT
        elif curr_char == ';':
            curr_tok = TokenType.SEMICOLON

        # Handle X or X= operators
        elif curr_char == '!':
            curr_tok = TokenType.BANG_EQUAL if self.match('=') else TokenType.BANG
        elif curr_char == '=':
            curr_tok = TokenType.EQUAL_EQUAL if self.match('=') else TokenType.EQUAL
        elif curr_char == '<':
            curr_tok = TokenType.LESS_EQUAL if self.match('=') else TokenType.LESS
        elif curr_char == '>':
            curr_tok = TokenType.GREATER_EQUAL if self.match('=') else TokenType.GREATER
        elif curr_char == '+':
            curr_tok = TokenType.PLUS_EQUAL if self.match('=') else TokenType.PLUS
        elif curr_char == '-':
            curr_tok = TokenType.MINUS_EQUAL if self.match('=') else TokenType.MINUS
        elif curr_char == '*':
            curr_tok = TokenType.STAR_EQUAL if self.match('=') else TokenType.STAR

        # Comments or slash operator
        elif curr_char == '/':
            # Single line comment
            if self.match('/'):
                while self.peek() != '\n' and not self.is_at_end():
                    self.advance()
            # Multi-line comment
            elif self.match('*'):
                while not (self.peek() == '*' and self.peek_next() == '/') and not self.is_at_end():
                    self.advance()
                if self.is_at_end():
                    self.print_error(self.line, "Unterminated comment block.")
                    return
                # Consume the trailing */
                self.advance()
                self.advance()
            # Slash-equal /=
            elif self.match('='):
                curr_tok = TokenType.SLASH_EQUAL
            else:
                curr_tok = TokenType.SLASH

        # Whitespace handling
        elif curr_char in [' ', '\r', '\t']:
            return
        elif curr_char == '\n':
            self.line += 1
            return

        # Handling literals
        elif curr_char == '"':
            self.handle_string()
            return
        elif curr_char == '`':
            self.handle_code()
            return
        elif curr_char.isdigit():
            self.handle_number()
            return
        elif curr_char.isalpha() or curr_char == '_':
            self.handle_identifier()
            return
        else:
            self.print_error(self.line, "Unexpected character.")
            return
        if curr_tok is not None:
            self.add_token(curr_tok)
