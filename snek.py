#!/usr/bin/python3

import sys
import ast


output = ""

def parse(string):
    return ast.parse(string)

def write_to_file(str):
    assert(output != "")

    with open(output, 'a') as file:
        file.write(str)

counter = 0

def codegen_func_call(call):
    global counter

    if call.func.id != "__writemem" and call.func.id != "asm":
        write_to_file(f"{call.func.id}(")
        i = 0
        for arg in call.args:
            if arg.value[0].isalpha():
                write_to_file(f"\"{arg.value}\"")

            if i != len(call.args)-1 :
                write_to_file(",")
            i += 1
        write_to_file(")")
    elif call.func.id == "__writemem":
        write_to_file(f"volatile unsigned char *buf{counter} = (unsigned char*){call.args[0].value};\n *buf{counter} = {call.args[1].value}")
        counter += 1

    elif call.func.id == "asm":
        write_to_file(f"asm volatile (\"{call.args[0].value}\")")


def codegen_expr(node):
    if(isinstance(node.value, ast.Call)):
        codegen_func_call(node.value)

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

def codegen_args(args):
    i = 0
    for arg in args:
        write_to_file(f"{py_type_to_c_type(arg.annotation.id)} {arg.arg}")
        if i != len(args)-1 :
            write_to_file(",")
        i += 1

def codegen_func_def(node):
    if isinstance(node.returns, ast.Constant):
        write_to_file(f"void {node.name}(")
    else:
        write_to_file(f"{py_type_to_c_type(node.returns.id)} {node.name}(")
    codegen_args(node.args.args)
    write_to_file(")\n")
    write_to_file("{\n")
    for i in node.body:
        codegen_node(i)
    write_to_file("}")

    pass

def codegen_node(node):
    if isinstance(node, ast.Expr):
        codegen_expr(node)

    if isinstance(node, ast.Return):
        write_to_file(f"return {node.value.value}")

    if isinstance(node, ast.Expr) or isinstance(node, ast.Return):
        write_to_file(";\n")

    if isinstance(node, ast.FunctionDef):
        codegen_func_def(node)

# Generate C code from python AST
def codegen(parsed):
    print(ast.dump(parsed))
    for node in parsed.body:
        codegen_node(node)


def main():
    global output
    data = ""

    if len(sys.argv) >= 3:
        output = sys.argv[2]

        with open(sys.argv[1], 'r') as file:
            data = file.read()

    else:
        print("No file specified")
        sys.exit(1)

    parsed = parse(data)

    codegen(parsed)


main()

    

