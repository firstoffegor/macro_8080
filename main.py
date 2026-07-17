from parser import parse_tokens
from ast import build_program_ast, print_ast
from token_class import Tokentype

text = """
int a = b * c + d
print(a + y)
"""

tokens = parse_tokens(text)


statements = []
current_statement = []

for token in tokens:
    if token.token_type == Tokentype.newline:
        if current_statement:  
            statements.append(current_statement)
            current_statement = []
    else:
        current_statement.append(token)


if current_statement:
    statements.append(current_statement)


program_ast = build_program_ast(statements)
print_ast(program_ast)

    


