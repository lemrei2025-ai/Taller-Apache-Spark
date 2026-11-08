#!/usr/bin/env python3
"""
Genera los datasets sintéticos del taller en la carpeta data/.

  data/clientes.csv      - 500 clientes
  data/productos.json    - 40 productos (JSON Lines)
  data/ventas.csv        - N ventas (por defecto 20.000) del año 2025
  data/texto_bigdata.txt - texto para el conteo de palabras

Uso:
  python scripts/generar_datos.py              # 20.000 ventas
  python scripts/generar_datos.py --ventas 1000000   # dataset grande para pruebas de rendimiento
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
    DATA.mkdir(exist_ok=True)

    # Clientes ---------------------------------------------------------------
    clientes = []
    for i in range(1, 501):
        ciudad = random.choice(list(CIUDADES))
        clientes.append({
            "id_cliente": i,
            "nombre": f"{random.choice(NOMBRES)} {random.choice(APELLIDOS)}",
            "edad": random.randint(18, 75),
            "genero": random.choice(["F", "M"]),
            "ciudad": ciudad,
            "region": CIUDADES[ciudad],
            "fecha_registro": (date(2020, 1, 1) + timedelta(days=random.randint(0, 1800))).isoformat(),
            "segmento": random.choices(["Básico", "Plata", "Oro"], weights=[60, 30, 10])[0],
        })
    with open(DATA / "clientes.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=clientes[0].keys())
        w.writeheader()
        w.writerows(clientes)

    # Productos (JSON Lines) -------------------------------------------------
    productos = []
    pid = 100
    for cat, items in CATEGORIAS.items():
        for nombre, precio in items:
            pid += 1
            productos.append({"id_producto": pid, "producto": nombre, "categoria": cat,
                              "precio_unitario": precio, "stock": random.randint(0, 500)})
    with open(DATA / "productos.json", "w", encoding="utf-8") as f:
        for p in productos:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")

    # Ventas -----------------------------------------------------------------
    inicio = date(2025, 1, 1)
    with open(DATA / "ventas.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id_venta", "fecha", "id_cliente", "id_producto", "cantidad",
                    "precio_unitario", "descuento", "canal", "metodo_pago"])
        for i in range(1, n_ventas + 1):
            p = random.choice(productos)
            dia = inicio + timedelta(days=random.randint(0, 364))
            # Temporada alta en diciembre: más ventas
            if random.random() < 0.08:
                dia = date(2025, 12, random.randint(1, 31))
            cantidad = random.choices([1, 2, 3, 4, 5], weights=[55, 25, 10, 6, 4])[0]
            descuento = random.choice([0, 0, 0, 0.05, 0.10, 0.15, 0.20])
            fila = [i, dia.isoformat(), random.randint(1, 500), p["id_producto"], cantidad,
                    p["precio_unitario"], descuento, random.choice(CANALES), random.choice(METODOS)]
            # ~1 % de registros "sucios" para practicar limpieza
            r = random.random()
            if r < 0.004:
                fila[4] = ""          # cantidad faltante
            elif r < 0.007:
                fila[4] = -cantidad   # cantidad negativa (error)
            elif r < 0.010:
                fila[7] = ""          # canal faltante
            w.writerow(fila)

    (DATA / "texto_bigdata.txt").write_text(TEXTO, encoding="utf-8")

    print(f"Datos generados en {DATA}:")
    for archivo in sorted(DATA.iterdir()):
        print(f"  {archivo.name:22s} {archivo.stat().st_size / 1024:8.1f} KB")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--ventas", type=int, default=20_000, help="número de ventas a generar")
    ap.add_argument("--semilla", type=int, default=42)
    args = ap.parse_args()
    main(args.ventas, args.semilla)
