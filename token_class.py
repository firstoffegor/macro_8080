from enum import Enum

class Tokentype(Enum):
    literal = 1
    variable_name = 2
    binding = 3
    open_p = 4
    closed_p = 5
    aop = 6 # Arithmetical OPeration
    type = 7
    newline = 8
    

class Token:
    token_type: Tokentype
    name: str
    
    def __init__(self, name, token_type):
        self.name = name
        self.token_type = token_type