from token_class import Token, Tokentype

def recognise_token(buffer: str) -> Token | None:
    result = Token(buffer, Tokentype.variable_name)
    if buffer == "":
        return
    if buffer == "\n":
        result.token_type = Tokentype.newline
    elif buffer == "function":
        result.token_type = Tokentype.func
    elif buffer == ",":
        result.token_type = Tokentype.comma
    elif buffer == "return":
        result.token_type = Tokentype.ret
    elif buffer == ":":
        result.token_type = Tokentype.column
    elif buffer == "->":
        result.token_type = Tokentype.return_type
    elif buffer in ("int", "str", "float", "bool"):
        result.token_type = Tokentype.type
    elif buffer in "+_**//%":
        result.token_type = Tokentype.aop
    elif buffer == "(":
        result.token_type = Tokentype.open_p
    elif buffer == ")":
        result.token_type = Tokentype.closed_p
    elif "'" in buffer or '"' in buffer or buffer.isnumeric() or buffer == "True" or buffer == "False" or buffer == "None":
        result.token_type = Tokentype.literal
    elif "=" in buffer:
        result.token_type = Tokentype.binding
    return result
    

if __name__ == "__main__":
    assert recognise_token("") == None
    assert recognise_token("\n").token_type == Tokentype.newline
    assert recognise_token("+").token_type == Tokentype.aop
    assert recognise_token("**").token_type == Tokentype.aop
    assert recognise_token("(").token_type == Tokentype.open_p
    assert recognise_token(")").token_type == Tokentype.closed_p
    assert recognise_token("123").token_type == Tokentype.literal
    assert recognise_token("'hello'").token_type == Tokentype.literal
    assert recognise_token("True").token_type == Tokentype.literal
    assert recognise_token("None").token_type == Tokentype.literal
    assert recognise_token("=").token_type == Tokentype.binding
    assert recognise_token("my_var").token_type == Tokentype.variable_name
    assert recognise_token("function").token_type == Tokentype.func
    assert recognise_token(",").token_type == Tokentype.comma