#!/usr/bin/env python3
"""
Soluciones de referencia - Taller de Apache Spark.

Ejecutar desde la raíz del repositorio:
    python ejercicios/soluciones/soluciones.py
o
    spark-submit ejercicios/soluciones/soluciones.py
"""
import os
import re
import shutil
import time
from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

RAIZ = Path(__file__).resolve().parents[2]
DATA = str(RAIZ / "data")

spark = (SparkSession.builder.appName("Soluciones")
         .master(os.environ.get("SPARK_MASTER", "local[*]"))
         .config("spark.sql.shuffle.partitions", "8")
         .getOrCreate())
spark.sparkContext.setLogLevel("ERROR")
sc = spark.sparkContext


def titulo(t):
    print("\n" + "=" * 70 + f"\n{t}\n" + "=" * 70)


# ------------------------------------------------------------------ datos
ventas = spark.read.csv(f"{DATA}/ventas.csv", header=True, inferSchema=True)
clientes = spark.read.csv(f"{DATA}/clientes.csv", header=True, inferSchema=True)
productos = spark.read.json(f"{DATA}/productos.json")

limpias = (ventas.filter(F.col("cantidad") > 0)
           .fillna({"canal": "Desconocido"})
           .withColumn("total", F.col("cantidad") * F.col("precio_unitario") * (1 - F.col("descuento")))
           .withColumn("mes", F.month("fecha")))
full = (limpias.join(productos, ["id_producto", "precio_unitario"], "left")
        .join(clientes, "id_cliente", "left"))
full.createOrReplaceTempView("ventas_full")

# ------------------------------------------------------------------ E1
titulo("E1 · RDD: palabras del texto")
palabras = sc.textFile(f"{DATA}/texto_bigdata.txt") \
             .flatMap(lambda l: re.findall(r"\w+", l.lower()))
palabras.cache()
print("a) Total de palabras   :", palabras.count())
print("   Palabras distintas  :", palabras.distinct().count())
iniciales = (palabras.map(lambda p: (p[0], 1))
             .reduceByKey(lambda a, b: a + b)
             .takeOrdered(5, key=lambda kv: -kv[1]))
print("b) Top 5 letras iniciales:", iniciales)

# ------------------------------------------------------------------ E2
titulo("E2 · Ingreso por mes y canal (pivote, millones COP)")
(limpias.groupBy("mes").pivot("canal")
 .agg(F.round(F.sum("total") / 1e6, 1))
 .orderBy("mes")
 .show(12))

# ------------------------------------------------------------------ E3
titulo("E3 · Top 10 clientes por gasto")
(full.groupBy("id_cliente", "nombre", "ciudad", "segmento")
 .agg(F.count("*").alias("compras"), F.round(F.sum("total")).cast("long").alias("gasto_total"))
 .orderBy(F.desc("gasto_total"))
 .show(10, truncate=False))

# ------------------------------------------------------------------ E4
titulo("E4 · Calidad de datos")
ventas.agg(
    F.sum(F.col("cantidad").isNull().cast("int")).alias("cantidad_nula"),
    F.sum((F.col("cantidad") < 0).cast("int")).alias("cantidad_negativa"),
    F.sum(F.col("canal").isNull().cast("int")).alias("canal_nulo"),
    F.count("*").alias("total_registros"),
).show()

# ------------------------------------------------------------------ E5
titulo("E5 · Categoría con más ingresos por región (SQL)")
spark.sql("""
WITH t AS (
    SELECT region, categoria, SUM(total) AS ingresos
    FROM ventas_full GROUP BY region, categoria
)
SELECT region, categoria, ROUND(ingresos / 1e6, 1) AS ingresos_mill
FROM (SELECT *, ROW_NUMBER() OVER (PARTITION BY region ORDER BY ingresos DESC) AS rn FROM t)
WHERE rn = 1
ORDER BY ingresos_mill DESC
""").show()

# ------------------------------------------------------------------ E6
titulo("E6 · Crecimiento mensual (SQL)")
spark.sql("""
WITH m AS (SELECT mes, SUM(total) AS ingresos FROM ventas_full GROUP BY mes)
SELECT mes,
       ROUND(ingresos / 1e6, 1) AS ingresos_mill,
       ROUND(100 * (ingresos - LAG(ingresos) OVER (ORDER BY mes))
                 / LAG(ingresos) OVER (ORDER BY mes), 1) AS crecimiento_pct
FROM m ORDER BY mes
""").show(12)

# ------------------------------------------------------------------ E7
titulo("E7 · CSV vs Parquet (con el dataset actual)")
tmp = RAIZ / "salida" / "e7"
shutil.rmtree(tmp, ignore_errors=True)
limpias.write.mode("overwrite").option("header", True).csv(str(tmp / "csv"))
limpias.write.mode("overwrite").parquet(str(tmp / "parquet"))


def mb(ruta):
    return sum(f.stat().st_size for f in Path(ruta).rglob("*") if f.is_file()
               and not f.name.endswith(".crc")) / 1024 ** 2


def medir(fn):
    t = time.time()
    fn()
    return time.time() - t


t_csv = medir(lambda: spark.read.csv(str(tmp / "csv"), header=True, inferSchema=True)
              .groupBy("canal").agg(F.sum("total")).collect())
t_pq = medir(lambda: spark.read.parquet(str(tmp / "parquet"))
             .groupBy("canal").agg(F.sum("total")).collect())
print(f"a) Tiempo  CSV: {t_csv:.2f} s | Parquet: {t_pq:.2f} s")
print(f"b) Tamaño  CSV: {mb(tmp / 'csv'):.2f} MB | Parquet: {mb(tmp / 'parquet'):.2f} MB")
print("""c) Parquet es un formato columnar: lee solo las columnas que requiere la consulta,
   comprime mejor porque los valores de una misma columna son homogéneos, conserva el
   esquema (no es necesario inferirlo) y almacena estadísticas (mínimo/máximo) que permiten
   omitir bloques completos (predicate pushdown) (The Apache Software Foundation, s.f.).
   CSV, en cambio, obliga a leer e interpretar todo el texto.""")

spark.stop()
