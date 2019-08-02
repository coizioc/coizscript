from token import TokenType
from symbol_table import SemanticAnalyzer
from base_classes import NodeVisitor


class ReturnError(Exception):
    def __init__(self, expr):
        self.expr = expr


class Scope():
    def __init__(self, scope_name, scope_level, enclosing_scope):
        self.scope_name = scope_name
        self.scope_level = scope_level
        self.enclosing_scope = enclosing_scope
        self.variables = {}

    def insert(self, name, data):
        self.variables[name] = data

    def lookup(self, name):
        try:
            data = self.variables[name]
        except KeyError:
            data = None

        if data is not None:
            return data

        # recursively go up the chain and lookup the name
        if self.enclosing_scope is not None:
            return self.enclosing_scope.lookup(name)

    def update(self, name, value):
        try:
            data = self.variables[name]
        except KeyError:
            data = None

        if data is not None:
            self.variables[name] = value
            return

        if self.enclosing_scope is not None:
            return self.enclosing_scope.update(name, value)
        else:
            raise NameError(name)

    def import_vars(self, scope):
        self.variables.update(scope.variables)

    def __str__(self):
        msgs = []
        tab = ''.join(['  ' for _ in range(self.scope_level)])
        out = f'{tab}Scope level {self.scope_level} {self.scope_name}:\n'
        for var_name, var_data in self.variables.items():
            out += f'{tab} * {var_name}: {var_data}\n'
        msgs.append(out)

        if self.enclosing_scope:
            msgs.append(str(self.enclosing_scope))

        return ''.join(reversed(msgs))


class Interpreter(NodeVisitor):
    def __init__(self, parser):
        self.parser = parser
        self.symantic_analyzer = SemanticAnalyzer()
        self.current_scope = Scope("global", 1, None)

    def interpret(self):
        tree = self.parser.parse()
        self.symantic_analyzer.visit(tree)

        # Import variables and functions from imported files.
        for import_int in self.symantic_analyzer.imports:
            self.current_scope.import_vars(import_int.current_scope)

        return self.visit(tree)

    def visit_Array(self, node):
        array = []
        for expr in node.array:
            array.append(self.visit(expr))
        return array

    def visit_AssertStmt(self, node):
        if not self.visit(node.condition):
            self.visit(node.print_stmt)

    def visit_Assign(self, node):
        var_name = node.left.value
        if node.index is None:
            if node.token.type == TokenType.EQUAL:
                result = self.visit(node.right)
                self.current_scope.update(var_name, result)
            elif node.token.type == TokenType.PLUS_EQUAL:
                new_val = self.current_scope.lookup(var_name) + self.visit(node.right)
                self.current_scope.update(var_name, new_val)
            elif node.token.type == TokenType.MINUS_EQUAL:
                new_val = self.current_scope.lookup(var_name) - self.visit(node.right)
                self.current_scope.update(var_name, new_val)
            elif node.token.type == TokenType.STAR_EQUAL:
                new_val = self.current_scope.lookup(var_name) * self.visit(node.right)
                self.current_scope.update(var_name, new_val)
            elif node.token.type == TokenType.SLASH_EQUAL:
                new_val = self.current_scope.lookup(var_name) / self.visit(node.right)
                self.current_scope.update(var_name, new_val)
        else:
            i = int(self.visit(node.index))
            if node.token.type == TokenType.EQUAL:
                val_arr = self.current_scope.lookup(var_name)
                val_arr[i] = self.visit(node.right)
                self.current_scope.update(var_name, val_arr)
            elif node.token.type == TokenType.PLUS_EQUAL:
                val_arr = self.current_scope.lookup(var_name)
                val_arr[i] += self.visit(node.right)
                self.current_scope.update(var_name, val_arr)
            elif node.token.type == TokenType.MINUS_EQUAL:
                val_arr = self.current_scope.lookup(var_name)
                val_arr[i] -= self.visit(node.right)
                self.current_scope.update(var_name, val_arr)
            elif node.token.type == TokenType.STAR_EQUAL:
                val_arr = self.current_scope.lookup(var_name)
                val_arr[i] *= self.visit(node.right)
                self.current_scope.update(var_name, val_arr)
            elif node.token.type == TokenType.SLASH_EQUAL:
                val_arr = self.current_scope.lookup(var_name)
                val_arr[i] /= self.visit(node.right)
                self.current_scope.update(var_name, val_arr)

    def visit_BinOp(self, node):
        if node.op.type == TokenType.PLUS:
            return self.visit(node.left) + self.visit(node.right)
        elif node.op.type == TokenType.MINUS:
            return self.visit(node.left) - self.visit(node.right)
        elif node.op.type == TokenType.STAR:
            return self.visit(node.left) * self.visit(node.right)
        elif node.op.type == TokenType.SLASH:
            return self.visit(node.left) / self.visit(node.right)
        elif node.op.type == TokenType.PERCENT:
            return self.visit(node.left) % self.visit(node.right)

    def visit_Block(self, node):
        # Create new scope
        new_scope = Scope("block", self.current_scope.scope_level + 1, self.current_scope)
        self.current_scope = new_scope

        for child in node.stmt_list:
            self.visit(child)

        self.current_scope = self.current_scope.enclosing_scope

    def visit_Code(self, node):
        from io import StringIO
        import sys
        old_stdout = sys.stdout
        redirected_output = sys.stdout = StringIO()
        try:
            exec(node.value)
        except Exception as e:
            print(e)
            raise e
        sys.stdout = old_stdout
        return redirected_output.getvalue()

    def visit_Compound(self, node):
        for child in node.children:
            self.visit(child)

    def visit_ForStmt(self, node):
        # Create new scope.

        new_scope = Scope("for", self.current_scope.scope_level + 1, self.current_scope)
        self.current_scope = new_scope

        self.visit(node.init_stmt)
        while self.visit(node.condition):
            self.visit(node.block)
            self.visit(node.assign_stmt)

        self.current_scope = self.current_scope.enclosing_scope

    def visit_FuncCall(self, node):
        func_decl = self.current_scope.lookup(node.name)
        if not func_decl:
            raise NameError(repr(node.name))
        block = func_decl.block_node

        # Create new scope.
        calling_scope = self.current_scope
        new_scope = Scope(node.name, self.current_scope.scope_level + 1, self.current_scope)
        self.current_scope = new_scope

        # Put argument values into new scope.
        if node.args:
            arg_values = []
            for arg in node.args:
                arg_values.append(self.visit(arg.expr))
            for arg_value, param in zip(arg_values,  func_decl.params):
                self.current_scope.insert(param.var_node.value, arg_value)

        try:
            self.visit(block)
        except ReturnError as e:
            return_val = self.visit(e.expr)
            self.current_scope = calling_scope
            return return_val

        self.current_scope = calling_scope
        return None

    def visit_FuncDecl(self, node):
        self.current_scope.insert(node.name, node)

    def visit_FuncLen(self, node):
        return len(self.visit(node.expr))

    def visit_IfElse(self, node):
        if self.visit(node.condition):
            # Create new scope.
            new_scope = Scope("if", self.current_scope.scope_level + 1, self.current_scope)
            self.current_scope = new_scope

            self.visit(node.if_block)

            self.current_scope = self.current_scope.enclosing_scope
        elif node.else_block:
            # Create new scope.
            new_scope = Scope("else", self.current_scope.scope_level + 1, self.current_scope)
            self.current_scope = new_scope

            self.visit(node.else_block)

            self.current_scope = self.current_scope.enclosing_scope

    def visit_ImportStmt(self, node):
        pass

    def visit_Logical(self, node):
        if node.op.type == TokenType.OR:
            return self.visit(node.left) or self.visit(node.right)
        elif node.op.type == TokenType.AND:
            return self.visit(node.left) and self.visit(node.right)
        elif node.op.type == TokenType.EQUAL_EQUAL:
            return self.visit(node.left) == self.visit(node.right)
        elif node.op.type == TokenType.BANG_EQUAL:
            return self.visit(node.left) != self.visit(node.right)
        elif node.op.type == TokenType.GREATER_EQUAL:
            return self.visit(node.left) >= self.visit(node.right)
        elif node.op.type == TokenType.LESS_EQUAL:
            return self.visit(node.left) <= self.visit(node.right)
        elif node.op.type == TokenType.GREATER:
            return self.visit(node.left) > self.visit(node.right)
        elif node.op.type == TokenType.LESS:
            return self.visit(node.left) < self.visit(node.right)

    def visit_PrintStmt(self, node):
        formatted_args = []
        for arg in node.args:
            result = self.visit(arg)
            # If result is a float, check if it is an integer. If so, truncate the decimal portion.
            if type(result) == float and round(result) == result:
                    formatted_args.append(int(result))
            elif type(result) == list:
                formatted_args.append([int(e) for e in result if round(e) == e])
            else:
                formatted_args.append(result)

        if len(node.args) == 1:
            print(formatted_args[0])
        # Printf syntax
        else:
            print(formatted_args[0] % tuple(formatted_args[1:]))

    def visit_ReturnStmt(self, node):
        raise ReturnError(node.expr)

    def visit_WhileStmt(self, node):
        # Create new scope.
        new_scope = Scope("while", self.current_scope.scope_level + 1, self.current_scope)
        self.current_scope = new_scope

        while self.visit(node.cond):
            self.visit(node.block)

        self.current_scope = self.current_scope.enclosing_scope

    def visit_NoOp(self, node):
        pass

    def visit_String(self, node):
        return node.value

    def visit_UnaryOp(self, node):
        op = node.op.type
        if op == TokenType.PLUS:
            return +self.visit(node.expr)
        elif op == TokenType.MINUS:
            return -self.visit(node.expr)

    def visit_Num(self, node):
        return node.value

    def visit_Var(self, node):
        var_name = node.value
        val = self.current_scope.lookup(var_name)
        if val is None:
            raise NameError(repr(var_name))
        else:
            if node.index is not None:
                i = int(self.visit(node.index))
                return val[i]
            return val

    def visit_VarDecl(self, node):
        var_name = node.left.value
        var_value = self.visit(node.right)
        self.current_scope.insert(var_name, var_value)
