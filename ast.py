class AST(object):
    pass


class Arg(AST):
    def __init__(self, expr):
        self.expr = expr


class Array(AST):
    def __init__(self, array):
        self.array = array


class AssertStmt(AST):
    def __init__(self, condition, print_stmt):
        self.condition = condition
        self.print_stmt = print_stmt


class Assign(AST):
    def __init__(self, left, op, right, index):
        self.left = left
        self.token = self.op = op
        self.right = right
        self.index = index


class BinOp(AST):
    def __init__(self, left, op, right):
        self.left = left
        self.token = self.op = op
        self.right = right


class Block(AST):
    def __init__(self, stmt_list):
        self.stmt_list = stmt_list


class Call(AST):
    def __init__(self, callee, args):
        self.callee = callee
        self.args = args


class Code(AST):
    def __init__(self, token):
        self.token = token
        self.value = token.literal


class Compound(AST):
    def __init__(self):
        self.children = []


class ForStmt(AST):
    def __init__(self, init_stmt, condition, assign_stmt, block):
        self.init_stmt = init_stmt
        self.condition = condition
        self.assign_stmt = assign_stmt
        self.block = block


class FuncCall(AST):
    def __init__(self, name, args):
        self.name = name
        self.args = args  # a list of Arg nodes
        self.return_val = None


class FuncDecl(AST):
    def __init__(self, name, params, block_node):
        self.name = name
        self.params = params  # a list of Param nodes
        self.block_node = block_node


class FuncLen(AST):
    def __init__(self, expr):
        self.expr = expr


class IfElse(AST):
    def __init__(self, condition, if_block, else_block):
        self.condition = condition
        self.if_block = if_block
        self.else_block = else_block


class ImportStmt(AST):
    def __init__(self, filename):
        self.filename = filename


class Logical(AST):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right


class NoOp(AST):
    pass


class Num(AST):
    def __init__(self, token):
        self.token = token
        self.value = token.literal


class Param(AST):
    def __init__(self, var_node):
        self.var_node = var_node


class PrintStmt(AST):
    def __init__(self, args):
        self.args = args


class ReturnStmt(AST):
    def __init__(self, expr):
        self.expr = expr


class String(AST):
    def __init__(self, token):
        self.token = token
        self.value = token.literal


class UnaryOp(AST):
    def __init__(self, op, expr):
        self.token = self.op = op
        self.expr = expr


class Var(AST):
    def __init__(self, token, index=None):
        self.token = token
        self.value = token.lexeme
        self.index = index


class VarDecl(AST):
    def __init__(self, left, op, right):
        self.left = left
        self.token = self.op = op
        self.right = right


class WhileStmt(AST):
    def __init__(self, cond, block):
        self.cond = cond
        self.block = block
