from typing import Union
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from classes.operation import Operation

import itertools
import re

from sympy import symbols, sympify
from sympy.logic.boolalg import Not, And, Or, Nand, Nor, Xor
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application


app = FastAPI()

origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def verificar_sintaxis(expresion):
    stack = []
    for char in expresion:
        if char == '(':
            stack.append(char)
        elif char == ')':
            if not stack:
                return False
            stack.pop()
    return not stack


def convertir_sympy(expresion):
    # Define las funciones lambda para NAND, NOR y XOR
    nand = lambda a, b: ~(a & b)
    nor = lambda a, b: ~(a | b)
    xor = lambda a, b: a ^ b
    
    # Obtiene las variables en la expresión
    variables = sorted(list(set(re.findall(r'[A-Za-z]', expresion))))
    simbolos = symbols(" ".join(variables))
    simbolo_dict = {str(var): var for var in simbolos}
    
    # Define una función para aplicar la función de operador adecuada a las variables
    def apply_operator(op, a, b):
        if op == '∧':
            return a & b
        elif op == '∨':
            return a | b
        elif op == '¬':
            return ~b
        elif op == '⊕':
            return xor(a, b)
        elif op == '⊼':
            return nand(a, b)
        elif op == '⊽':
            return nor(a, b)

    # Define una función recursiva para analizar y construir la expresión Sympy
    def parse_recursive(exp):
        stack = []
        i = 0
        while i < len(exp):
            char = exp[i]
            if char in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
                stack.append(simbolo_dict[char])
            elif char in '∧∨⊕⊼⊽':
                if len(stack) >= 2:
                    b = stack.pop()
                    a = stack.pop()
                    stack.append(apply_operator(char, a, b))
                else:
                    stack.append(char)
            elif char == '¬':
                if len(stack) >= 1:
                    stack.append(apply_operator(char, None, stack.pop()))
                else:
                    stack.append(char)
            elif char == '(':
                j = i
                open_parens = 1
                while open_parens > 0:
                    j += 1
                    if exp[j] == '(':
                        open_parens += 1
                    elif exp[j] == ')':
                        open_parens -= 1
                inner_expr = exp[i + 1:j]
                stack.append(parse_recursive(inner_expr))
                i = j
            i += 1

        while len(stack) > 1:
            b = stack.pop()
            op = stack.pop()
            a = stack.pop()
            stack.append(apply_operator(op, a, b))

        return stack[0]

    # Llama a la función recursiva para construir la expresión Sympy
    sympy_expresion = parse_recursive(expresion)
    
    return sympy_expresion




def revertir_operadores(expresion_sympy):
    expresion = str(expresion_sympy)
    expresion = expresion.replace("~", "¬").replace("&", "∧").replace("|", "∨")
    expresion = expresion.replace("Xor", "⊕").replace("Nand", "⊼").replace("Nor", "⊽")
    return expresion

def generar_tabla_de_verdad(expresion):
    if not verificar_sintaxis(expresion):
        raise ValueError("Sintaxis de la proposición incorrecta")

    variables = sorted(list(set(re.findall(r'[A-Za-z]', expresion))))
    simbolos = symbols(" ".join(variables))
    #simbolo_dict = {str(var): var for var in simbolos}
    formula = convertir_sympy(expresion)
    print(formula)
    encabezado = variables + [expresion]
    tabla = [encabezado]

    for valores in itertools.product([False, True], repeat=len(variables)):
        asignacion = dict(zip(simbolos, valores))
        fila = [valor for valor in valores]

        if not isinstance(formula, bool):
            print("Expresión antes de subs:", formula)
            fila.append(formula.subs(asignacion))
        else:
            fila += [formula]

        tabla.append([("V" if valor else "F") for valor in fila[:-1]] + [("V" if fila[-1] else "F")])
    
    for fila in tabla:
        print(" | ".join(fila))

    return tabla

expresion = "A⊽B"
tabla_de_verdad = generar_tabla_de_verdad(expresion)
# La variable "tabla_de_verdad" esta la matriz
print("Probando")


@app.get("/")
def read_root():
    return {"response": "Welcome to use free Algebra boolean calculator"}

#Corregir
@app.post('/formula')
def procesar_proposicion(operation: Operation):
    proposicion = operation.formula
    expresion = proposicion
    print(expresion)
    if expresion is not None:
        response = generar_tabla_de_verdad(str(expresion))
        print(response)
        return {"response": response}
    else:
        return {"error": 'La proposición no está bien formada'}