from parser import parse_tokens
from macro_ast import build_program_ast, make_statements_from_tokens, print_ast


text = """while (a > b):
    int a = 1
    """


    

tokens = parse_tokens(text)
statements = make_statements_from_tokens(tokens)

program_ast = build_program_ast(statements)
print_ast(program_ast)



    


