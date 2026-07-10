from parser import parse_tokens
from extract_scopes import extract_scopes

text = """
    int a = 123
    int b = 234
    
    function some_func(int x, int y) -> int:
        int a = 3 + x + y
        return a
        
    int d = x + y
        
    
"""


tokens = parse_tokens(text)
scopes = extract_scopes(tokens)
print(scopes)
