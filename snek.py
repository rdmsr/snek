#!/usr/bin/python3

import sys
import ast



# lol global variables go brrr
output = None
counter = 0

# Why does this even exist?
def parse(string):
    return ast.parse(string)

# moment
def write_to_file(str):
    global output

    output.write(str)

# Python cannot do pointers, so I have a builtin function to write to memory
def builtin_writemem(args):
    str = f"volatile unsigned char *buf{counter} = (unsigned char*){args[0].value};\n *buf{counter} = {args[0].value}"
    counter += 1
    return str

# Output asm C-style
def builtin_asm(args):
    return f"asm volatile (\"{args[0].value}\")"

# self explanatory
builtin_funcs = [(builtin_writemem, "__writemem"), (builtin_asm, "asm")]

def codegen_func_call(call):
    global counter

    # If function is not builtin, don't do special stuff, just codegen it
    if call.func.id not in builtin_funcs:
        write_to_file(f"{call.func.id}(")
        i = 0
        for arg in call.args:
            codegen_expr(arg)

            if i != len(call.args)-1 :
                write_to_file(",")

            i += 1
        write_to_file(")")
   
   # Else, codegen its special string
    else:
        builtin_funcs[call.func.id](call.args)


def codegen_op_from_node(op):
    if isinstance(op, ast.Add):
        write_to_file("+")
    elif isinstance(op, ast.Sub):
        write_to_file("-")
    elif isinstance(op, ast.Mult):
        write_to_file("*")
    elif isinstance(op, ast.Div):
        write_to_file("/")
    elif isinstance(op, ast.Mod):
        write_to_file("%")
    elif isinstance(op, ast.LShift):
        write_to_file("<<")
    elif isinstance(op, ast.RShift):
        write_to_file(">>")
    elif isinstance(op, ast.BitOr):
        write_to_file("|")
    elif isinstance(op, ast.BitXor):
        write_to_file("^")
    elif isinstance(op, ast.BitAnd):
        write_to_file("&")
    else:
        print("Unknown operator")

# An expr is basically something that can be evaluated
# So like 10 is an expression, so is 10+10 and function calls are too
def codegen_expr(node):

    if isinstance(node, ast.Constant):
        write_to_file(f"{node.value}")
   
    elif isinstance(node, ast.Name):
        write_to_file(f"{node.id}")
    # BinOperators
    elif (isinstance(node, ast.BinOp)):
        codegen_expr(node.left)
        codegen_op_from_node(node.op)
        codegen_expr(node.right)

    elif isinstance(node, ast.Call):
            codegen_func_call(node)

# Well that's pretty much self explanatory
# God I'm overcommenting, am I?
def py_type_to_c_type(t):
    if t == "int":
        return "int"
    elif t == "float":
        return "float"
    elif t == "str":
        return "char*"
    elif t == "bool":
        return "bool"
    elif t == "None":
        return "void"
    else:
        return "void"

# Codegen parameters
# Basically you put a comma if the parameter isn't the last one
def codegen_args(args):
    i = 0
    for arg in args:
        write_to_file(f"{py_type_to_c_type(arg.annotation.id)} {arg.arg}")
        if i != len(args)-1 :
            write_to_file(",")
        i += 1

def codegen_func_def(node):
    # If you don't know the return type, it's void
    if isinstance(node.returns, ast.Constant) or node.returns is None:
        write_to_file(f"void {node.name}(")

    # Else, it's specified
    else:
        write_to_file(f"{py_type_to_c_type(node.returns.id)} {node.name}(")
    # Codegen parameters
    codegen_args(node.args.args)

    # Start of function body
    write_to_file(")\n{\n")

    # Iterate through each node of the body and codegen it
    for i in node.body:
        codegen_node(i)

    # End of function body
    write_to_file("}\n")

    pass

# Yea so this codegens a node apparently
# It checks for the type of node and calls the appropriate function
def codegen_node(node):
    if isinstance(node, ast.Expr):
        codegen_expr(node)

    if isinstance(node, ast.Return):
        write_to_file(f"return ")
        codegen_expr(node.value)

    if isinstance(node, ast.Expr) or isinstance(node, ast.Return):
        write_to_file(";\n")

    if isinstance(node, ast.FunctionDef):
        codegen_func_def(node)

# Generate C code from python AST
def codegen(parsed):
    print(ast.dump(parsed))
    for node in parsed.body:
        codegen_node(node)


# Main function of the program, idk why I did that but it's here
def main():
    global output
    data = ""

    if len(sys.argv) >= 3:
        output = open(sys.argv[2], 'w')

        with open(sys.argv[1], 'r') as input:
            data = input.read()
    else:
        print(f"Command syntax is {sys.argv[0]} [FILE] [OUTPUT]")
        sys.exit(1)

    parsed = parse(data)

    codegen(parsed)


main()

    

