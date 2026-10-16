from token_class import Tokentype, Token
from recognizer import recognise_token

INDENT_WIDTH = 4  # this many leading spaces (or one "\t") = one tab token


def parse_tokens(text: str) -> list[Token]:
    buffer = ""
    result = []
    at_line_start = True
    indent_spaces = 0
    for letter in text:
        # Leading whitespace of a line is indentation: one tab token per level.
        if at_line_start:
            if letter == "\t":
                result.append(recognise_token("\t"))
                continue
            if letter == " ":
                indent_spaces += 1
                if indent_spaces == INDENT_WIDTH:
                    result.append(recognise_token("\t"))
                    indent_spaces = 0
                continue
            at_line_start = False
        if letter == "\n":
            at_line_start = True
            indent_spaces = 0
            if token := recognise_token(buffer):
                result.append(token)
            result.append(recognise_token("\n")) 
            buffer = ""
            continue
        if letter == "(":
            # A name right before "(" is a call; a bare "(" is just grouping.
            if buffer:
                if recognise_token(buffer).token_type == Tokentype.flow_control:
                    result.append(recognise_token(buffer))  # "while(" is still the keyword
                else:
                    result.append(Token(buffer, Tokentype.func_name))
            result.append(recognise_token("("))
            buffer = ""
            continue
        if letter == ")":
            if token := recognise_token(buffer):
                result.append(token)
            result.append(recognise_token(")"))
            buffer = ""
            continue
        if letter == ",":
            if token := recognise_token(buffer):
                result.append(token)
            result.append(recognise_token(","))
            buffer = ""
            continue
        if letter == ":":
            if token := recognise_token(buffer):
                result.append(token)
            result.append(recognise_token(":"))
            buffer = ""
            continue
        if letter == " ":
            if token := recognise_token(buffer):
                result.append(token)
            buffer = ""
            continue
        
        buffer += letter
    # Flush whatever is left when the text doesn't end with a delimiter.
    if token := recognise_token(buffer):
        result.append(token)
    return result
    

if __name__ == "__main__":
    t1 = parse_tokens("a = 123\n")
    assert (t1[0].name, t1[0].token_type) == ("a", Tokentype.variable_name)
    assert (t1[1].name, t1[1].token_type) == ("=", Tokentype.binding)
    assert (t1[2].name, t1[2].token_type) == ("123", Tokentype.literal)

    t2 = parse_tokens("print(a + b)")
    assert (t2[0].name, t2[0].token_type) == ("print", Tokentype.func_name)
    assert (t2[1].name, t2[1].token_type) == ("(", Tokentype.open_p)
    assert (t2[2].name, t2[2].token_type) == ("a", Tokentype.variable_name)
    assert (t2[3].name, t2[3].token_type) == ("+", Tokentype.aop)
    assert (t2[4].name, t2[4].token_type) == ("b", Tokentype.variable_name)
    assert (t2[5].name, t2[5].token_type) == (")", Tokentype.closed_p)

    t3 = parse_tokens("True False None")
    assert len(t3) == 3
    for t in t3:
        assert t.token_type == Tokentype.literal
