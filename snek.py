#!/usr/bin/python3.10

import sys
import ast
import os

# lol global variables go brrr
output = None
counter = 0

# Why does this even exist?
def parse(string):
    return ast.parse(string)

# moment
def write_to_file(string):
    global output

    output.write(string)

# Python cannot do pointers, so I have a builtin function to write to memory
def builtin_writemem(args):
    global counter

    write_to_file(f"volatile {py_type_to_c_type(args[2].id)} *buf{counter} = ({py_type_to_c_type(args[2].id)}*)")
    codegen_expr(args[0])
    write_to_file(";\n")
    write_to_file(f"*buf{counter} = ");
    codegen_expr(args[1])
    
    counter += 1
    return str

# Output asm C-style
def builtin_asm(args):
    write_to_file(f"asm volatile (\"{args[0].value}\")")

# self explanatory
builtin_funcs = {"__writemem" : builtin_writemem, "asm" : builtin_asm}

def codegen_func_call(call):

    # If function is not builtin, don't do special stuff, just codegen it
    if call.func.id not in builtin_funcs:
        write_to_file(f"{call.func.id}(")

        for arg in call.args:
            codegen_expr(arg)

            if arg != call.args[-1]:
                write_to_file(",")

        write_to_file(")")
   
   # Else, codegen its special string
    else:
        builtin_funcs[call.func.id](call.args)


def codegen_op_from_node(op):
    match op.__class__:
        case ast.Add:
            write_to_file("+")
        case ast.Sub:
            write_to_file("-")
        case ast.Mult:
            write_to_file("*")
        case ast.Div:
            write_to_file("/")
        case ast.Mod:
            write_to_file("%")
        case ast.LShift:
            write_to_file("<<")
        case ast.RShift:
            write_to_file(">>")
        case ast.BitOr:
            write_to_file("|")
        case ast.BitXor:
            write_to_file("^")
        case ast.BitAnd:
            write_to_file("&")

# An expr is basically something that can be evaluated
# So like 10 is an expression, so is 10+10 and function calls are too
def codegen_expr(node):
    match node.__class__:
        case ast.Constant:
            if type(node.value) == str:
                if len(node.value) > 1:
                    write_to_file(f"\"{node.value}\"")
                else:
                    write_to_file(f"\'{node.value}\'")
            else:
                write_to_file(f"{node.value}")
        case ast.Name:
            write_to_file(f"{node.id}")
        case ast.BinOp:
            codegen_expr(node.left)
            codegen_op_from_node(node.op)
            codegen_expr(node.right)
        case ast.Call:
            codegen_func_call(node)

def codegen_subscript(node, name=""):
    match node.value.id:
        case "list":
            write_to_file(f"{py_type_to_c_type(node.slice.id)} {name}[]")

# Well that's pretty much self explanatory
# God I'm overcommenting, am I?
def py_type_to_c_type(t):
    match t:
        case "int":
            return "int"
        case "float":
            return "float"
        case "str":
            return "char*"
        case "char":
            return "char"
        case "bool":
            return "int"
        case "u16":
            return "uint16_t"
        case "u32":
            return "uint32_t"
        case "u64":
            return "uint64_t"
        case _:
            return "void"

def codegen_annotation(ann, arg):
    match ann.__class__:
        case ast.Name:
            return write_to_file(py_type_to_c_type(ann.id) + " " + arg)
        case ast.Subscript:
            return codegen_subscript(ann, arg)

# Codegen parameters
# Basically you put a comma if the parameter isn't the last one
def codegen_args(args):
    for arg in args:
        codegen_annotation(arg.annotation, arg.arg)

        if arg != args[-1]:
            write_to_file(",")

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

def codegen_assign(node):
    codegen_annotation(node.annotation, node.target.id)

    write_to_file(f" = ")

    codegen_expr(node.value)


# Yea so this codegens a node apparently
# It checks for the type of node and calls the appropriate function
def codegen_node(node):
    match node.__class__:
        case ast.FunctionDef:
            codegen_func_def(node)

        case ast.AnnAssign:
            codegen_assign(node)
            write_to_file(";\n")

        case ast.Expr:
            codegen_expr(node.value)
            write_to_file(";\n")

        case ast.Return:
            write_to_file(f"return ")
            codegen_expr(node.value)
            write_to_file(";\n")
        case ast.Import:
            write_to_file(f"#include \"{node.names[0].name}.h\"\n")

# Generate C code from python AST
def codegen(parsed, debug=False, stdlib=True):
    if debug:
        print(ast.dump(parsed))
    if stdlib:
        # XXX: Put code here you want in the top of the file
        write_to_file("""
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#define True 1
#define False 0
#ifdef NULL
#undef NULL
#define NULL (*void)0
#endif
#define None NULL
#define print printf
""")
    for node in parsed.body:
        codegen_node(node)


# Makes a default output file for da code
def gen_output_file(filename):
    # 1. Disect the filepath to get the filename
    # one = filename.split("/")[-1]

    # 2. Remove last extension
    # two = ".".join(one.split(".")[0 : -1])

    # 3. Add '.c'
    # three = two + ".c"

    # Combine all to get this malformed mess of code
    return ".".join(filename.split("/")[-1].split(".")[0 : 1]) + ".c"

# Also self-explanitory
def help_menu():
    print("--nostdlib:       Nothing standard is included, you're on your own.")
    print("--help:           Brings this help menu.")
    print("-o [output file]  Specifies the output filename.")

# Main function of the program, idk why I did that but it's here
def main():
    global output
    data = ""
    stdlib = True

    if len(sys.argv) >= 2:
        # Detect help menu
        if "--help" in sys.argv:
            print(f"Syntax: {sys.argv[0]} [args] [input file]")
            help_menu()
            exit(1)

        # Detect '-o'
        if "-o" in sys.argv:
            # Do some black magic frickery
            tmp_index = sys.argv.index("-o")
            try:
                output_filename = sys.argv[tmp_index + 1]
                output = open(output_filename, "w")
            except IndexError:
                print("Warning: Cannot find output filename, ignoring '-o'")

        # Detect '--nostdlib'
        if "--nostdlib" in sys.argv:
            stdlib = False
        else: 
            output = open(gen_output_file(sys.argv[-1]), 'w')

        try:
            with open(sys.argv[-1], 'r') as input_:
                data = input_.read()
        except FileNotFoundError:
            output.close()
            os.remove(output.name)

            print(f"Error: File not found: {sys.argv[-1]}")
            print(f"Syntax: {sys.argv[0]} [args] [input file]")
            exit(1)
    else:
        print(f"Syntax: {sys.argv[0]} [args] [input file]")
        exit(1)

    parsed = parse(data)

    codegen(parsed, stdlib = stdlib)


if __name__ == "__main__":
    main()

    

