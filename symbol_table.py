from base_classes import NodeVisitor
from collections import OrderedDict
from ast import *


class Symbol():
    def __init__(self, name, type=None):
        self.name = name
        self.type = type


class FuncSymbol(Symbol):
    def __init__(self, name, params=None):
        super(FuncSymbol, self).__init__(name)
        # a list of formal parameters
        self.params = params if params is not None else []

    def __str__(self):
        return '<{class_name}(name={name}, parameters={params})>'.format(
            class_name=self.__class__.__name__,
            name=self.name,
            params=self.params,
        )

    __repr__ = __str__


class VarSymbol(Symbol):
    def __init__(self, name, type=None):
        super().__init__(name, type)

    def __str__(self):
        return '<{name}>'.format(name=self.name)

    __repr__ = __str__


class BuiltinTypeSymbol(Symbol):
    def __init__(self, name):
        super().__init__(name)

    def __str__(self):
        return self.name

    __repr__ = __str__


class SymbolTable():
    def __init__(self, scope_name, scope_level, enclosing_scope=None, debug=False):
        self._symbols = OrderedDict()
        self.scope_name = scope_name
        self.scope_level = scope_level
        self.enclosing_scope = enclosing_scope
        self.debug = debug

    def __str__(self):
        h1 = 'SCOPE (SCOPED SYMBOL TABLE)'
        lines = ['\n', h1, '=' * len(h1)]
        for header_name, header_value in (
            ('Scope name', self.scope_name),
            ('Scope level', self.scope_level),
            ('Enclosing scope', self.enclosing_scope.scope_name if self.enclosing_scope else None)
        ):
            lines.append('%-15s: %s' % (header_name, header_value))
        h2 = 'Scope (Scoped symbol table) contents'
        lines.extend([h2, '-' * len(h2)])
        lines.extend(('%7s: %r' % (key, value)) for key, value in self._symbols.items())
        lines.append('\n')
        s = '\n'.join(lines)
        return s

    __repr__ = __str__

    def insert(self, symbol):
        if self.debug:
            print('Insert: %s' % symbol.name)
        self._symbols[symbol.name] = symbol

    def lookup(self, name, current_scope_only=False):
        if self.debug:
            print('Lookup: %s. (Scope name: %s)' % (name, self.scope_name))
        # 'symbol' is either an instance of the Symbol class or None
        symbol = self._symbols.get(name)

        if symbol is not None:
            return symbol

        if current_scope_only:
            return None

        # recursively go up the chain and lookup the name
        if self.enclosing_scope is not None:
            return self.enclosing_scope.lookup(name)


class SemanticAnalyzer(NodeVisitor):
    def __init__(self):
        self.symtab = SymbolTable('global', 1)
        self.current_scope = None
        self.imports = []

    def visit_Array(self, node):
        for expr in node.array:
            self.visit(expr)

    def visit_AssertStmt(self, node):
        self.visit(node.condition)
        self.visit(node.print_stmt)

    def visit_Assign(self, node):
        var_name = node.left.value
        var_symbol = self.current_scope.lookup(var_name)

        if not var_symbol:
            raise NameError(repr(var_name))

        if node.index:
            if var_symbol.type != 'array':
                raise TypeError("Variable %s is not indexed." % var_name)

        self.visit(node.right)

    def visit_BinOp(self, node):
        self.visit(node.left)
        self.visit(node.right)

    def visit_Block(self, node):
        block_scope = SymbolTable(
            scope_name="block",
            scope_level=self.current_scope.scope_level + 1,
            enclosing_scope=self.current_scope
        )
        self.current_scope = block_scope

        for child in node.stmt_list:
            self.visit(child)

        self.current_scope = self.current_scope.enclosing_scope

    def visit_ForStmt(self, node):
        for_scope = SymbolTable(
            scope_name="for",
            scope_level=self.current_scope.scope_level + 1,
            enclosing_scope=self.current_scope
        )
        self.current_scope = for_scope

        self.visit(node.init_stmt)

        self.visit(node.condition)
        self.visit(node.assign_stmt)
        self.visit(node.block)

    def visit_FuncCall(self, node):
        func_name = node.name
        func_decl = self.symtab.lookup(func_name)
        if not func_decl:
            raise NameError(repr(func_name))
        if type(func_decl) != FuncSymbol:
            raise Exception("Error: identifier %s not a function." % func_name)
        func_args = node.args
        if len(func_args) != len(func_decl.params):
            raise Exception("Error: mismatched number of arguments (got %d, expected %d)"
                            % (len(func_args), len(func_decl.params)))

    def visit_FuncDecl(self, node):
        func_name = node.name
        func_symbol = FuncSymbol(func_name)
        self.symtab.insert(func_symbol)
        func_scope = SymbolTable(
            scope_name=func_name,
            scope_level=self.current_scope.scope_level + 1,
            enclosing_scope=self.current_scope
        )
        self.current_scope = func_scope

        for param in node.params:
            param_name = param.var_node.value
            var_symbol = VarSymbol(param_name)
            self.current_scope.insert(var_symbol)
            func_symbol.params.append(var_symbol)

        self.current_scope = self.current_scope.enclosing_scope

    def visit_FuncLen(self, node):
        self.visit(node.expr)

    def visit_IfElse(self, node):
        self.visit(node.condition)
        self.visit(node.if_block)
        if node.else_block:
            self.visit(node.else_block)

    def visit_ImportStmt(self, node):
        try:
            with open(f'{node.filename.value}.coiz', 'r') as f:
                source = f.read()
            from scanner import Scanner
            from token_parser import Parser
            from interpreter import Interpreter
            scanner = Scanner(source, node.filename.value)
            scanner.scan_tokens()

            parser = Parser(scanner)
            interpreter = Interpreter(parser)
            interpreter.interpret()

            for var_name, data in interpreter.current_scope.variables.items():
                if type(data) == FuncDecl:
                    self.symtab.insert(FuncSymbol(var_name, data.params))
                else:
                    self.current_scope.insert(VarSymbol(var_name))
            # for func_name, func_decl in interpreter.callables.items():
            #     self.symtab.insert(FuncSymbol(func_name, func_decl.params))
            self.imports.append(interpreter)
        except Exception as e:
            print(e)

    def visit_Logical(self, node):
        self.visit(node.left)
        self.visit(node.right)

    def visit_Num(self, node):
        pass

    def visit_String(self, node):
        pass

    def visit_UnaryOp(self, node):
        self.visit(node.expr)

    def visit_Compound(self, node):
        global_scope = SymbolTable(
            scope_name='global',
            scope_level=1,
            enclosing_scope=self.current_scope,  # None
        )
        self.current_scope = global_scope
        for child in node.children:
            self.visit(child)
        self.current_scope = self.current_scope.enclosing_scope

    def visit_NoOp(self, node):
        pass

    def visit_PrintStmt(self, node):
        for arg in node.args:
            self.visit(arg)

    def visit_Var(self, node):
        var_name = node.value
        var_symbol = self.current_scope.lookup(var_name)

        if var_symbol is None:
            raise NameError(repr(var_name))

        if node.index is not None and var_symbol.type is None:
            raise TypeError("Variable %s is not indexed." % var_name)

    def visit_VarDecl(self, node):
        # We have all the information we need to create a variable symbol.
        # Create the symbol and insert it into the symbol table.
        var_name = node.left.value
        if type(node.right) == Array:
            var_type = "array"
        elif type(node.right) == String:
            var_type = "string"
        else:
            var_type = None
        var_symbol = VarSymbol(var_name, var_type)

        # Signal an error if the table already has a symbol with the same name in the current scope.
        if self.current_scope.lookup(var_name, current_scope_only=True):
            raise Exception(
                "Error: Duplicate identifier '%s' found" % var_name
            )

        self.current_scope.insert(var_symbol)

    def visit_WhileStmt(self, node):
        self.visit(node.cond)
        self.visit(node.block)
