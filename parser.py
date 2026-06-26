
from token_class import Tokentype, Token
from recognizer import recognise_token

def parse_tokens(text: str) -> list[Token]:
    buffer = ""
    result = []
    for letter in text:
        if letter == "\n":
            if token := recognise_token(buffer):
                result.append(token)
            buffer = ""
            continue
        if letter == "(":
            if token := recognise_token(buffer):
                result.append(token)
            result.append(recognise_token("("))
            buffer = ""
            continue
        if letter == ")":
            if token := recognise_token(buffer):
                result.append(token)
            result.append(recognise_token(")"))
            buffer = ""
            continue
        if letter == " ":
            if token := recognise_token(buffer):
                result.append(token)
            buffer = ""
            continue
        buffer += letter
    return result
    

if __name__ == "__main__":
    t1 = parse_tokens("a = 123\n")
    assert (t1[0].name, t1[0].token_type) == ("a", Tokentype.variable_name)
    assert (t1[1].name, t1[1].token_type) == ("=", Tokentype.binding)
    assert (t1[2].name, t1[2].token_type) == ("123", Tokentype.literal)

    t2 = parse_tokens("print(a + b)")
    assert (t2[0].name, t2[0].token_type) == ("print", Tokentype.variable_name)
    assert (t2[1].name, t2[1].token_type) == ("(", Tokentype.open_p)
    assert (t2[2].name, t2[2].token_type) == ("a", Tokentype.variable_name)
    assert (t2[3].name, t2[3].token_type) == ("+", Tokentype.aop)
    assert (t2[4].name, t2[4].token_type) == ("b", Tokentype.variable_name)
    assert (t2[5].name, t2[5].token_type) == (")", Tokentype.closed_p)

    t3 = parse_tokens("True False None")
    for t in t3:
        assert t.token_type == Tokentype.literal
