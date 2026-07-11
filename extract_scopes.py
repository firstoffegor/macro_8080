from token_class import Token, Tokentype

class Scope:
    def __init__(self, name: str):
        self.name = name
        self.variables = {}   # Holds the variable name and its breakdown

    def __repr__(self):
        return f"Scope(name='{self.name}', variables={self.variables})"


def extract_scopes(tokens: list[Token]) -> list[Scope]:
    global_scope = Scope("global")
    scopes = [global_scope]
    current_scope = global_scope
    
    i = 0
    while i < len(tokens):
        token = tokens[i]
        
        # 1. Detect function declaration to switch scopes
        if token.name == "function" and (i + 1) < len(tokens):
            func_name_token = tokens[i + 1]
            func_scope = Scope(name=func_name_token.name)
            
            scopes.append(func_scope)
            current_scope = func_scope
            i += 2
            continue
            
        # 2. Detect variable declarations: "int a = 3 + x + y"
        if token.token_type == Tokentype.type and (i + 2) < len(tokens):
            next_token = tokens[i + 1]
            binding_token = tokens[i + 2]
            
            if next_token.token_type == Tokentype.variable_name and binding_token.token_type == Tokentype.binding:
                var_name = next_token.name
                
                # Gather ALL valid tokens belonging to this assignment expression
                expr_elements = []
                expr_idx = i + 3
                while expr_idx < len(tokens):
                    # Stop if we hit a new statement line, a new function, or a return
                    if tokens[expr_idx].token_type == Tokentype.type or tokens[expr_idx].name in ("function", "return"):
                        break
                    
                    # CLEANUP: Skip newlines, spaces, or empty tokens entirely
                    if tokens[expr_idx].name not in ("\n", " ", ""):
                        expr_elements.append(tokens[expr_idx].name)
                        
                    expr_idx += 1
                
                # Format the output beautifully based on how many tokens were found
                if len(expr_elements) == 1:
                    current_scope.variables[var_name] = expr_elements[0]
                elif len(expr_elements) > 1:
                    current_scope.variables[var_name] = tuple(expr_elements)
                
                i = expr_idx
                continue

        # 3. Detect when to return back to global scope
        if token.name == "return" and current_scope != global_scope:
            current_scope = global_scope
            i += 2
            continue

        i += 1
        
    return scopes