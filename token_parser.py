from ast import *
from token import TokenType


class Parser():
    def __init__(self, scanner):
        self.tokens = scanner.tokens
        self.filename = scanner.filename
        self.current_token_index = 0
        self.current_token = self.tokens[0]
        self.has_error = False

    def print_error(self, line, message):
        print(f"[{self.filename}, line {line}] Error: {message}")
        self.has_error = True

    def eat(self, token_type):
        if self.current_token.type == token_type:
            token_value = self.current_token.literal
            self.get_next_token()
            return token_value
        else:
            self.print_error(self.current_token.line, f"Expected token {TokenType(token_type).name}")

    def get_next_token(self):
        self.current_token_index += 1
        try:
            self.current_token = self.tokens[self.current_token_index]
        except IndexError:
            self.print_error(self.tokens[self.current_token_index - 1].line, "Run out of tokens for expr.")

    def parse(self):
        node = self.program()
        if self.current_token.type != TokenType.EOF:
            print(self.current_token)
            self.print_error(self.current_token.line, "Finished parsing before EOF.")
        return node

    def arg(self):
        """
        arg : expr | string | array
        """
        token = self.current_token
        if token.type == TokenType.STRING:
            return Arg(self.string())
        elif token.type == TokenType.LEFT_BRACKET:
            return Arg(self.array())
        else:
            return Arg(self.expr())

    def args_list(self):
        """
        args_list : arg
                  | arg , args_list
        """
        args = [self.arg()]

        while self.current_token.type == TokenType.COMMA:
            self.eat(TokenType.COMMA)
            args.append(self.arg())

        return args

    def array(self):
        """
        array: [ (expr (, expr)*)* ]
        """
        self.eat(TokenType.LEFT_BRACKET)
        array = []

        if self.current_token.type != TokenType.RIGHT_BRACKET:
            array.append(self.expr())

            while self.current_token.type == TokenType.COMMA:
                self.eat(TokenType.COMMA)
                array.append(self.expr())

        self.eat(TokenType.RIGHT_BRACKET)
        node = Array(array)
        return node

    def block(self):
        """
        block: { statement_list }
        """
        self.eat(TokenType.LEFT_BRACE)
        stmt_list = self.statement_list()
        node = Block(stmt_list)
        self.eat(TokenType.RIGHT_BRACE)
        return node

    def code(self):
        node = Code(self.current_token)
        self.eat(TokenType.CODE)
        return node

    def compound_statement(self):
        """
        compound_statement: statement_list
        """
        nodes = self.statement_list()

        root = Compound()
        for node in nodes:
            root.children.append(node)

        return root

    def condition(self):
        """
        condition: logic_or
        """
        node = self.logic_or()
        return node

    def empty(self):
        return NoOp()

    def expr(self):
        """
        expr : term (+ | - factor)*
        """
        node = self.term()

        while self.current_token.type in (TokenType.PLUS, TokenType.MINUS):
            token = self.current_token
            if token.type == TokenType.PLUS:
                self.eat(TokenType.PLUS)
            elif token.type == TokenType.MINUS:
                self.eat(TokenType.MINUS)

            node = BinOp(left=node, op=token, right=self.factor())

        return node

    def factor(self):
        """
        factor : + factor
               | - factor
               | func_call
               | ( expr )
               | func_len
               | variable ([ expr ])
               | func_call
        """
        token = self.current_token
        if token.type == TokenType.PLUS:
            self.eat(TokenType.PLUS)
            node = UnaryOp(token, self.factor())
            return node
        elif token.type == TokenType.MINUS:
            self.eat(TokenType.MINUS)
            node = UnaryOp(token, self.factor())
            return node
        elif token.type == TokenType.NUMBER:
            self.eat(TokenType.NUMBER)
            return Num(token)
        elif token.type == TokenType.LEFT_PAREN:
            self.eat(TokenType.LEFT_PAREN)
            node = self.expr()
            self.eat(TokenType.RIGHT_PAREN)
            return node
        elif token.type == TokenType.LEN:
            node = self.func_len()
            return node
        else:
            node = self.variable()
            token = self.current_token
            # Array indexing
            if token.type == TokenType.LEFT_BRACKET:
                self.eat(TokenType.LEFT_BRACKET)
                expr = self.expr()
                self.eat(TokenType.RIGHT_BRACKET)
                node.index = expr
            # Function call
            elif token.type == TokenType.LEFT_PAREN:
                node = self.func_call(node)
            return node

    def func_call(self, var):
        """
        func_call : identifier ( args_list* )
        """
        self.eat(TokenType.LEFT_PAREN)
        if self.current_token.type != TokenType.RIGHT_PAREN:
            args = self.args_list()
        else:
            args = []
        self.eat(TokenType.RIGHT_PAREN)
        node = FuncCall(var.value, args)
        return node

    def func_decl(self):
        """
        func_decl : FUNC identifier ( params_list* ) { statement_list }
        """
        self.eat(TokenType.FUNC)
        func_name = self.current_token.lexeme
        self.eat(TokenType.IDENTIFIER)
        self.eat(TokenType.LEFT_PAREN)
        if self.current_token.type != TokenType.RIGHT_PAREN:
            params = self.params_list()
        else:
            params = []
        self.eat(TokenType.RIGHT_PAREN)
        root = self.block()
        node = FuncDecl(func_name, params, root)
        return node

    def func_len(self):
        """
        func_len: LEN ( array | string )
        """
        self.eat(TokenType.LEN)
        self.eat(TokenType.LEFT_PAREN)
        token = self.current_token
        if token.type == TokenType.LEFT_BRACKET:
            expr = self.array()
        elif token.type == TokenType.STRING:
            expr = self.string()
        else:
            expr = self.variable()
        self.eat(TokenType.RIGHT_PAREN)
        node = FuncLen(expr)
        return node

    def ifelse(self):
        """
        ifelse : if ( condition ) block (else ifelse | else block)*
        """
        self.eat(TokenType.IF)
        self.eat(TokenType.LEFT_PAREN)

        condition = self.condition()

        self.eat(TokenType.RIGHT_PAREN)

        if_block = self.block()

        if self.current_token.type == TokenType.ELSE:
            self.eat(TokenType.ELSE)
            if self.current_token.type == TokenType.IF:
                else_block = self.ifelse()
            else:
                else_block = self.block()
            node = IfElse(condition, if_block, else_block)
        else:
            node = IfElse(condition, if_block, None)

        return node

    def logic_and(self):
        """
        logic_and : logic_eq (AND logic_eq)*
        """
        node = self.logic_eq()

        while self.current_token.type == TokenType.AND:
            token = self.current_token
            self.eat(TokenType.AND)

            node = Logical(node, token, self.logic_and())

        return node

    def logic_or(self):
        """
        logic_or : logic_and (OR logic_and)*
        """
        node = self.logic_and()

        while self.current_token.type == TokenType.OR:
            token = self.current_token
            self.eat(TokenType.OR)

            node = Logical(node, token, self.logic_or())

        return node

    def logic_eq(self):
        """
        logic_eq : expr == expr
                 | expr != expr
                 | expr >= expr
                 | expr <= expr
                 | expr > expr
                 | expr < expr
        """
        left = self.expr()

        token = self.current_token
        if token.type == TokenType.EQUAL_EQUAL:
            self.eat(TokenType.EQUAL_EQUAL)
        elif token.type == TokenType.BANG_EQUAL:
            self.eat(TokenType.BANG_EQUAL)
        elif token.type == TokenType.GREATER_EQUAL:
            self.eat(TokenType.GREATER_EQUAL)
        elif token.type == TokenType.LESS_EQUAL:
            self.eat(TokenType.LESS_EQUAL)
        elif token.type == TokenType.GREATER:
            self.eat(TokenType.GREATER)
        elif token.type == TokenType.LESS:
            self.eat(TokenType.LESS)

        right = self.expr()

        node = Logical(left, token, right)
        return node

    def param(self):
        return Param(self.variable())

    def params_list(self):
        """
        params_list : param
                    | param , params_list
        """
        params = [self.param()]

        while self.current_token.type == TokenType.COMMA:
            self.eat(TokenType.COMMA)
            params.append(self.param())

        return params

    def program(self):
        """
        program : compound_statement
        """
        node = self.compound_statement()
        return node

    def statement_list(self):
        """
        statement_list : statement
                       | block ; statement_list
                       | func_decl ; statement_list
                       | ifelse ; statement_list
                       | statement ; statement_list
        """
        results = []

        if self.current_token.type == TokenType.LEFT_BRACE:
            node = self.block()
        elif self.current_token.type == TokenType.FUNC:
            node = self.func_decl()
        elif self.current_token.type == TokenType.IF:
            node = self.ifelse()
        else:
            node = self.statement()

        results.append(node)

        while self.current_token.type in (TokenType.SEMICOLON, TokenType.FUNC, TokenType.IF, TokenType.LEFT_BRACE):
            token = self.current_token
            if token.type == TokenType.SEMICOLON:
                self.eat(TokenType.SEMICOLON)
                results.append(self.statement())
            elif token.type == TokenType.FUNC:
                results.append(self.func_decl())
            elif token.type == TokenType.IF:
                results.append(self.ifelse())
            else:
                results.append(self.block())

        if self.current_token.type == TokenType.IDENTIFIER:
            self.print_error(self.current_token.line, "unknown error")

        return results

    def statement(self):
        """
        statement : assignment_statement ;
                  | assert_statement
                  | print_statement ;
                  | return_statement ;
                  | for_statement ;
                  | import_statement ;
                  | initialization_statement ;
                  | while_statement ;
                  | empty
        """
        token = self.current_token
        if token.type == TokenType.VAR:
            node = self.initialization_statement()
        elif token.type == TokenType.IDENTIFIER:
            node = self.assignment_statement()
        elif token.type == TokenType.ASSERT:
            node = self.assert_statement()
        elif token.type == TokenType.PRINT:
            node = self.print_statement()
        elif token.type == TokenType.RETURN:
            node = self.return_statement()
        elif token.type == TokenType.FOR:
            node = self.for_statement()
        elif token.type == TokenType.WHILE:
            node = self.while_statement()
        elif token.type == TokenType.IMPORT:
            node = self.import_statement()
        else:
            node = self.empty()
        return node

    def assert_statement(self):
        """
        assert_statement : ASSERT ( condition , print_statement )
        """
        self.eat(TokenType.ASSERT)
        self.eat(TokenType.LEFT_PAREN)
        condition = self.condition()
        self.eat(TokenType.COMMA)
        print_stmt = self.print_statement()
        self.eat(TokenType.RIGHT_PAREN)
        node = AssertStmt(condition, print_stmt)
        return node

    def assignment_statement(self):
        """
        assignment_statement : variable ([ expr ]) ASSIGN (expr | string | array)
                             | func_call
        """
        left = self.variable()

        index = None

        token = self.current_token
        if token.type == TokenType.LEFT_BRACKET:
            self.eat(TokenType.LEFT_BRACKET)
            index = self.expr()
            self.eat(TokenType.RIGHT_BRACKET)
        elif token.type == TokenType.LEFT_PAREN:
            node = self.func_call(left)
            return node

        token = self.current_token
        if token.type == TokenType.EQUAL:
            self.eat(TokenType.EQUAL)
        elif token.type == TokenType.PLUS_EQUAL:
            self.eat(TokenType.PLUS_EQUAL)
        elif token.type == TokenType.MINUS_EQUAL:
            self.eat(TokenType.MINUS_EQUAL)
        elif token.type == TokenType.STAR_EQUAL:
            self.eat(TokenType.STAR_EQUAL)
        elif token.type == TokenType.SLASH_EQUAL:
            self.eat(TokenType.SLASH_EQUAL)

        if self.current_token.type == TokenType.STRING:
            right = self.string()
        elif self.current_token.type == TokenType.LEFT_BRACKET:
            right = self.array()
        else:
            right = self.expr()

        node = Assign(left, token, right, index)
        return node

    def for_statement(self):
        """
        for_statement : FOR ( initialization_statement ; condition ; assignment_statement ) block
        """
        self.eat(TokenType.FOR)
        self.eat(TokenType.LEFT_PAREN)
        init_stmt = self.initialization_statement()
        self.eat(TokenType.SEMICOLON)
        condition = self.condition()
        self.eat(TokenType.SEMICOLON)
        assign_stmt = self.assignment_statement()
        self.eat(TokenType.RIGHT_PAREN)
        block = self.block()

        node = ForStmt(init_stmt, condition, assign_stmt, block)
        return node

    def import_statement(self):
        """
        import_statement : IMPORT ( string )
        """
        self.eat(TokenType.IMPORT)
        self.eat(TokenType.LEFT_PAREN)
        filename = self.string()
        self.eat(TokenType.RIGHT_PAREN)
        node = ImportStmt(filename)
        return node

    def initialization_statement(self):
        """
        initialization_statement : VAR variable = (string | array | expr | code)
        """
        self.eat(TokenType.VAR)
        left = self.variable()
        assignment = self.current_token
        self.eat(TokenType.EQUAL)

        token = self.current_token
        if token.type == TokenType.STRING:
            right = self.string()
        elif token.type == TokenType.CODE:
            right = self.code()
        elif token.type == TokenType.LEFT_BRACKET:
            right = self.array()
        else:
            right = self.expr()
        node = VarDecl(left, assignment, right)
        return node

    def print_statement(self):
        """
        print_statement : PRINT (expr | string (, expr)* )
        """
        self.eat(TokenType.PRINT)
        self.eat(TokenType.LEFT_PAREN)
        args = []
        if self.current_token.type == TokenType.STRING:
            args.append(self.string())
        else:
            args.append(self.expr())
        while self.current_token.type == TokenType.COMMA:
            self.eat(TokenType.COMMA)
            args.append(self.expr())
        self.eat(TokenType.RIGHT_PAREN)
        node = PrintStmt(args)
        return node

    def return_statement(self):
        """
        return_statement : RETURN (string | expr)
        """
        self.eat(TokenType.RETURN)
        if self.current_token.type == TokenType.STRING:
            node = ReturnStmt(self.string())
        else:
            node = ReturnStmt(self.expr())
        return node

    def while_statement(self):
        """
        while_statement : WHILE ( condition ) block
        """
        self.eat(TokenType.WHILE)
        self.eat(TokenType.LEFT_PAREN)
        cond = self.condition()
        self.eat(TokenType.RIGHT_PAREN)
        block = self.block()
        node = WhileStmt(cond, block)
        return node

    def string(self):
        node = String(self.current_token)
        self.eat(TokenType.STRING)
        return node

    def term(self):
        """term : factor ((* | / | %) factor)*"""
        node = self.factor()

        while self.current_token.type in (TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            token = self.current_token
            if token.type == TokenType.STAR:
                self.eat(TokenType.STAR)
            elif token.type == TokenType.SLASH:
                self.eat(TokenType.SLASH)
            elif token.type == TokenType.PERCENT:
                self.eat(TokenType.PERCENT)

            node = BinOp(left=node, op=token, right=self.factor())

        return node

    def variable(self):
        """
        variable : IDENTIFIER
        """
        node = Var(self.current_token)
        self.eat(TokenType.IDENTIFIER)
        return node
