#!/usr/bin/env python3
"""
Genera el dataset de ejemplo del taller en data/ejemplo/.

  data/ejemplo/ventas_tienda.csv   N ventas (por defecto 20 000) del año 2025, en una sola tabla
  data/ejemplo/texto_bigdata.txt   texto para el conteo de palabras (cuaderno 02)

El dataset incluye, de forma intencional, problemas de calidad para practicar la limpieza:
valores faltantes, cantidades negativas, filas duplicadas y textos con espacios o
mayúsculas inconsistentes.

Uso:
  python scripts/generar_datos.py                     # 20 000 ventas
  python scripts/generar_datos.py --ventas 2000000    # dataset grande para pruebas de rendimiento
"""
import argparse
import csv
import json
import random
from datetime import date, timedelta
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"

CIUDADES = {
    "Bogotá": "Andina", "Medellín": "Andina", "Cali": "Pacífica", "Barranquilla": "Caribe",
    "Cartagena": "Caribe", "Bucaramanga": "Andina", "Pereira": "Andina", "Manizales": "Andina",
    "Santa Marta": "Caribe", "Villavicencio": "Orinoquía", "Pasto": "Andina", "Montería": "Caribe",
}
NOMBRES = ["Ana", "Luis", "María", "Carlos", "Laura", "Andrés", "Sofía", "Juan", "Valentina",
           "Diego", "Camila", "Santiago", "Daniela", "Felipe", "Paula", "Mateo", "Isabella",
           "Sebastián", "Natalia", "Julián"]
APELLIDOS = ["García", "Rodríguez", "Martínez", "López", "González", "Pérez", "Sánchez",
             "Ramírez", "Torres", "Gómez", "Díaz", "Vargas", "Rojas", "Moreno", "Castro"]
CATEGORIAS = {
    "Tecnología": [("Portátil", 2_800_000), ("Celular", 1_200_000), ("Audífonos", 180_000),
                   ("Monitor", 750_000), ("Teclado", 120_000), ("Mouse", 60_000),
                   ("Tablet", 1_100_000), ("Disco SSD", 320_000)],
    "Hogar": [("Licuadora", 250_000), ("Cafetera", 310_000), ("Aspiradora", 690_000),
              ("Juego de ollas", 420_000), ("Lámpara", 95_000), ("Ventilador", 210_000),
              ("Sábanas", 130_000), ("Microondas", 480_000)],
    "Deportes": [("Bicicleta", 1_500_000), ("Balón", 85_000), ("Tenis running", 380_000),
                 ("Mancuernas", 160_000), ("Colchoneta yoga", 70_000), ("Casco", 140_000),
                 ("Raqueta", 290_000), ("Morral", 150_000)],
    "Libros": [("Novela", 55_000), ("Libro técnico", 120_000), ("Cómic", 40_000),
               ("Diccionario", 75_000), ("Libro infantil", 35_000), ("Biografía", 65_000),
               ("Atlas", 90_000), ("Libro de cocina", 80_000)],
    "Moda": [("Camiseta", 60_000), ("Jean", 150_000), ("Chaqueta", 280_000),
             ("Zapatos", 230_000), ("Gorra", 45_000), ("Reloj", 350_000),
             ("Gafas de sol", 190_000), ("Bolso", 210_000)],
}
CANALES = ["Tienda física", "Web", "App móvil", "Marketplace"]
METODOS = ["Tarjeta crédito", "Tarjeta débito", "PSE", "Efectivo", "Nequi"]

TEXTO = """Big Data es el término que describe grandes volúmenes de datos que no pueden
procesarse con herramientas tradicionales. Se caracteriza por las cinco V: volumen,
velocidad, variedad, veracidad y valor. Apache Spark es un motor de procesamiento
distribuido que permite analizar datos a gran escala de forma rápida porque trabaja en
memoria. Spark divide los datos en particiones y las procesa en paralelo en un cluster
de computadores. Cada computador del cluster ejecuta tareas sobre una parte de los datos.
Spark ofrece varias bibliotecas: Spark SQL para consultas sobre datos estructurados,
Structured Streaming para datos en tiempo real, MLlib para aprendizaje automático y
GraphX para grafos. Los datos en Spark se representan como RDD o como DataFrame.
Un DataFrame organiza los datos en columnas con nombre, igual que una tabla en una base
de datos. Las operaciones sobre un DataFrame se dividen en transformaciones y acciones.
Las transformaciones son perezosas: Spark solo las ejecuta cuando se llama una acción.
Esta evaluación perezosa permite a Spark optimizar el plan de ejecución completo.
El optimizador Catalyst reorganiza las consultas para leer menos datos y hacer menos
trabajo. Los datos pueden leerse desde archivos CSV, JSON, Parquet, bases de datos o
sistemas distribuidos como HDFS y almacenamiento en la nube. Parquet es un formato
columnar que comprime los datos y acelera las consultas analíticas. En un proyecto de
Big Data los datos pasan por etapas de ingesta, limpieza, transformación, análisis y
visualización. Spark se usa en todas estas etapas y por eso es una herramienta central
en la ingeniería de datos y en la ciencia de datos. Aprender Spark permite procesar
millones de registros con unas pocas líneas de código en Python, Scala, Java, R o SQL.
"""


def main(n_ventas: int, semilla: int = 42) -> None:
    random.seed(semilla)
    destino = DATA / "ejemplo"
    destino.mkdir(parents=True, exist_ok=True)

    clientes = []
    for i in range(1, 501):
        ciudad = random.choice(list(CIUDADES))
        clientes.append({"ciudad": ciudad, "region": CIUDADES[ciudad],
                         "edad": random.randint(18, 75), "genero": random.choice(["F", "M"]),
                         "segmento": random.choices(["Básico", "Plata", "Oro"], weights=[60, 30, 10])[0]})
    productos = [(cat, nombre, precio) for cat, items in CATEGORIAS.items() for nombre, precio in items]

    columnas = ["id_venta", "fecha", "ciudad", "region", "canal", "metodo_pago", "categoria",
                "producto", "cantidad", "precio_unitario", "descuento", "edad_cliente",
                "genero_cliente", "segmento_cliente", "total"]
    inicio = date(2025, 1, 1)
    filas = []
    for i in range(1, n_ventas + 1):
        cli = random.choice(clientes)
        cat, prod, precio = random.choice(productos)
        dia = inicio + timedelta(days=random.randint(0, 364))
        if random.random() < 0.08:                       # temporada alta de diciembre
            dia = date(2025, 12, random.randint(1, 31))
        cantidad = random.choices([1, 2, 3, 4, 5], weights=[55, 25, 10, 6, 4])[0]
        descuento = random.choice([0, 0, 0, 0.05, 0.10, 0.15, 0.20])
        total = round(cantidad * precio * (1 - descuento), 2)
        fila = [i, dia.isoformat(), cli["ciudad"], cli["region"], random.choice(CANALES),
                random.choice(METODOS), cat, prod, cantidad, precio, descuento, cli["edad"],
                cli["genero"], cli["segmento"], total]
        r = random.random()                              # problemas de calidad (~2 %)
        if r < 0.004:
            fila[8] = ""; fila[14] = ""                  # cantidad y total faltantes
        elif r < 0.007:
            fila[8] = -cantidad; fila[14] = -total       # cantidad negativa (error de digitación)
        elif r < 0.010:
            fila[4] = ""                                 # canal faltante
        elif r < 0.014:
            fila[2] = random.choice([fila[2].upper(), " " + fila[2], fila[2].lower() + " "])
        elif r < 0.016:
            fila[11] = ""                                # edad faltante
        filas.append(fila)
        if random.random() < 0.005:                      # fila duplicada
            filas.append(list(fila))

    with open(destino / "ventas_tienda.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(columnas)
        w.writerows(filas)
    (destino / "texto_bigdata.txt").write_text(TEXTO, encoding="utf-8")

    print(f"Datos generados en {destino}:")
    for archivo in sorted(destino.iterdir()):
        print(f"  {archivo.name:22s} {archivo.stat().st_size / 1024:8.1f} KB")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--ventas", type=int, default=20_000, help="número de ventas a generar")
    ap.add_argument("--semilla", type=int, default=42)
    args = ap.parse_args()
    main(args.ventas, args.semilla)
