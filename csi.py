import sys

from scanner import Scanner
from token_parser import Parser
from interpreter import Interpreter


def run_file(filename):
    with open(filename, 'r') as f:
        had_error = run(f.read(), filename)
    if had_error:
        sys.exit(65)


def run_prompt():
    while True:
        source = input("> ")
        run(source, "")


def run(source, filename):
    scanner = Scanner(source, filename)
    scanner.scan_tokens()
    if scanner.has_error:
        return True

    parser = Parser(scanner)
    interpreter = Interpreter(parser)
    interpreter.interpret()
    return False


if __name__ == '__main__':
    if len(sys.argv) > 2:
        print("Usage: python csi.py [script]")
        sys.exit(64)
    elif len(sys.argv) == 2:
        run_file(sys.argv[1])
    else:
        run_prompt()
