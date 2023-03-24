from typing import Union
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.requests import Request
from starlette.middleware.cors import CORSMiddleware as StarletteCORSMiddleware
from classes.operation import Operation

from sympy import *
from sympy.parsing.sympy_parser import parse_expr
import pandas as pd
import regex as re


from sympy.logic.boolalg import BooleanFunction
from sympy.parsing.sympy_parser import (parse_expr, standard_transformations, implicit_multiplication_application)
from sympy import sympify, SympifyError
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

"""# Definir las funciones personalizadas
class Nand(BooleanFunction):
    @classmethod
    def eval(cls, *args):
        result = And(*args)
        if result is not None:
            return Not(result)

class Nor(BooleanFunction):
    @classmethod
    def eval(cls, *args):
        result = Or(*args)
        if result is not None:
            return Not(result)

class Xor(BooleanFunction):
    @classmethod
    def eval(cls, *args):
        if len(args) != 2:
            raise ValueError("Xor requiere exactamente dos argumentos")
        a, b = args
        return Or(And(a, Not(b)), And(Not(a), b))"""


# Define los operadores lógicos permitidos
# logical_operators = {'and', 'or', 'not', 'implies', 'iff'}
logical_operators = {'∧', '∨', '¬', '⊼', '⊽', '⊕'}
# Función para verificar la sintaxis de la proposición


def is_well_formed(proposition):
    # Elimina todos los espacios en blanco y paréntesis
    proposition = ''.join(proposition.split())
    proposition = proposition.replace('(', '')
    proposition = proposition.replace(')', '')

    # Comprueba que solo se usen operadores lógicos permitidos
    words = proposition.split()

    # Comprueba que no haya dos operadores consecutivos
    for i in range(len(words) - 1):
        if words[i] in logical_operators and words[i + 1] in logical_operators:
            return f"Hay dos operadores lógicos consecutivos: '{words[i]}' y '{words[i+1]}'"

    # Comprueba que la proposición no termine con un operador lógico
    if words[-1] in logical_operators:
        return f"La proposición no puede terminar con el operador lógico '{words[-1]}'"

    return True


# Función para convertir la proposición en una expresión de Sympy
def to_sympy_expression(proposition):
    # Reemplaza los operadores lógicos por sus equivalentes en Sympy
    proposition = proposition.replace('∧', '&')
    proposition = proposition.replace('∨', '|')
    proposition = proposition.replace('¬', '~')
    proposition = proposition.replace('⊕', '^')

    # Define las funciones lambda para NAND y NOR
    nand = lambda a, b: Not(And(a, b))
    nor = lambda a, b: Not(Or(a, b))

    # Reemplaza los operadores NAND y NOR en la proposición
    while '⊼' in proposition or '⊽' in proposition:
        for op, func in [('⊼', nand), ('⊽', nor)]:
            i = proposition.find(op)
            if i != -1:
                left = symbols(proposition[i - 1])
                right = symbols(proposition[i + 1])
                new_expr = func(left, right)
                proposition = proposition[:i - 1] + str(new_expr) + proposition[i + 2:]

    try:
        expr = parse_expr(proposition, evaluate=False)
        return expr
    except SympifyError as e:
        error_type = type(e).__name__
        error_location = str(e).split('\'')[1]
        raise SympifyError(f"Error de sintaxis en la proposición: {error_type} en {error_location}")


def revert_operators(expression):
    expression = expression.replace('&', '∧')
    expression = expression.replace('|', '∨')
    expression = expression.replace('~', '¬')
    expression = expression.replace('~&', '⊼')
    expression = expression.replace('~|', '⊽')
    expression = expression.replace('^', '⊕')

    # Reemplaza las expresiones equivalentes de NAND y NOR por sus símbolos originales
    expression = expression.replace('~&', '⊼')
    expression = expression.replace('~|', '⊽')
    
    return expression


def realizar_calculo(proposicion):
    check = is_well_formed(proposicion)
    if check is True:
        expresion = to_sympy_expression(proposicion)
        if expresion is not None:
            return expresion
        else:
            print('Error al convertir la proposición a una expresión de Sympy')
    else:
        print(check)

# Función para obtener los valores de verdad de una proposición
def obtener_valores_de_verdad(proposicion):
    # Parsear la proposición como una expresión simbólica
    expr = to_sympy_expression(proposicion)
    # Obtener las variables de la proposición
    variables = list(expr.free_symbols)
    # Crear una tabla de verdad completa
    tabla = []
    # Crear una lista para almacenar las columnas de operaciones lógicas
    columnas_operaciones = []
    for i in range(2**len(variables)):
        fila = []
        for j, variable in enumerate(variables):
            valor_variable = (i // 2**j) % 2
            fila.append(True if valor_variable == 1 else False)
        # Evaluamos cada operación lógica y añadimos su resultado como una columna adicional
        for operacion in expr.atoms(And, Or, Not, Xor, Nand, Nor):
            resultado_operacion = operacion.subs(
                {variables[k]: (i // 2**k) % 2 for k in range(len(variables))})
            nombre_operacion = str(operacion)
            if nombre_operacion not in columnas_operaciones:
                columnas_operaciones.append(nombre_operacion)
            fila.append(str(bool(resultado_operacion)))
        tabla.append(fila)

    # Agregar las columnas de operaciones lógicas al conjunto de columnas
    columnas = [str(var) for var in variables] + columnas_operaciones

    # Ordenar las columnas de menor a mayor longitud
    columnas_ordenadas = sorted(columnas, key=lambda x: len(str(x)))

    # Crear un DataFrame de pandas con la tabla de verdad
    df = pd.DataFrame(tabla, columns=columnas_ordenadas)

    # Agregar una columna con los valores finales de la proposición
    df[proposicion] = df.apply(lambda row: str(
        bool(expr.subs({variables[k]: row[k] for k in range(len(variables))}))), axis=1)

    matriz_de_listas = [df.columns.tolist()] + df.values.tolist()

    # Aplicar la función revert_operators a cada elemento de la matriz de listas
    matriz_de_listas_revertida = [[revert_operators(str(item)) for item in row] for row in matriz_de_listas]

    return (matriz_de_listas_revertida)


@app.get("/")
def read_root():
    return {"response": "Welcome to use free Algebra boolean calculator"}


@app.post('/formula')
def procesar_proposicion(operation: Operation):
    proposicion = operation.formula
    expresion = realizar_calculo(proposicion)
    print(expresion)
    if expresion is not None:
        response = obtener_valores_de_verdad(str(expresion))
        print(response)
        return {"response": response}
    else:
        return {"error": 'La proposición no está bien formada'}