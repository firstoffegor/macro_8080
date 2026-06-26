from token_class import Token, Tokentype

class Scope:
    scope_name: str
    variables: dict
    
    def __init__(self, name: str):
        self.scope_name = name
        self.variables = {}

    # Adding a __repr__ makes printing and debugging your scopes beautiful
    def __repr__(self):
        return f"Scope(name='{self.scope_name}', variables={self.variables})"


def extract_scopes(tokens: list[Token]) -> list[Scope]:
    # Initialize with a Scope object for the global scope
    scopes = [Scope("global")]
    
    i = 0
    while i < len(tokens):
        token = tokens[i]
        
        # 1. Detect entering a new function scope
        if token.token_type == Tokentype.variable_name and token.name == "function":
            if i + 1 < len(tokens) and tokens[i+1].token_type == Tokentype.variable_name:
                func_name = tokens[i+1].name
                # Append a new Scope instance to the stack
                scopes.append(Scope(func_name))
                i += 2
                continue

        # 2. NEW VARIABLE DECLARATION: [type] [variable_name] [binding] [literal]
        elif (i + 3 < len(tokens) and 
              token.token_type == Tokentype.type and
              tokens[i+1].token_type == Tokentype.variable_name and
              tokens[i+2].token_type == Tokentype.binding and
              tokens[i+3].token_type == Tokentype.literal):
            
            var_name = tokens[i+1].name
            raw_val = tokens[i+3].name
            
            # Add to the active scope object's variables dictionary
            scopes[-1].variables[var_name] = parse_literal_value(raw_val)
            i += 4
            continue
            
        # 3. VARIABLE REASSIGNMENT: [variable_name] [binding] [literal]
        elif (i + 2 < len(tokens) and 
              token.token_type == Tokentype.variable_name and
              tokens[i+1].token_type == Tokentype.binding and
              tokens[i+2].token_type == Tokentype.literal):
            
            var_name = token.name
            raw_val = tokens[i+2].name
            
            variable_found = False
            # Look backwards through the scope objects
            for scope_obj in reversed(scopes):
                if var_name in scope_obj.variables:
                    scope_obj.variables[var_name] = parse_literal_value(raw_val)
                    variable_found = True
                    break
            
            if not variable_found:
                raise NameError(
                    f"Syntax Error: Variable '{var_name}' is not defined. "
                    f"You must specify a type (e.g., 'int {var_name} = ...') to declare a new variable."
                )
                
            i += 3
            continue

        i += 1
        
    return scopes

def parse_literal_value(val: str):
    if val.isnumeric(): 
        return int(val)         # Converts "123" (str) -> 123 (int)
        
    if val in ("True", "False"): 
        return val == "True"    # Converts "True" (str) -> True (bool)
        
    if val == "None": 
        return None             # Converts "None" (str) -> None (NoneType)
        
    return val.strip("'\"")     # Converts "'hello'" (str) -> "hello" (str)