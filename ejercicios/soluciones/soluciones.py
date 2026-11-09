#!/usr/bin/env python3
"""
Soluciones de referencia del taller.

Las soluciones son genéricas: se aplican al dataset configurado en data/dataset_config.json
(por defecto, el dataset de ejemplo). Las columnas se eligen según los roles detectados.

Ejecutar desde la raíz del repositorio:
    python ejercicios/soluciones/soluciones.py
    spark-submit ejercicios/soluciones/soluciones.py
"""
import os
import re
import shutil
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "scripts"))
from taller_spark import (cargar_desde_config, clasificar_columnas, columna_objetivo,  # noqa: E402
                          iniciar_spark, ruta_absoluta, tamano_mb)
from pyspark.sql import functions as F  # noqa: E402

spark = iniciar_spark("Soluciones")
sc = spark.sparkContext


def titulo(t):
    print("\n" + "=" * 72 + f"\n{t}\n" + "=" * 72)


df, cfg = cargar_desde_config(spark, version="auto")
roles = clasificar_columnas(df, excluir=cfg["columnas_excluir"], max_categorias=cfg["max_categorias"])
NUM, CAT, FEC, TXT = roles["numericas"], roles["categoricas"], roles["fechas"], roles["texto"]
obj = columna_objetivo(cfg, df)
CAT1 = CAT[0] if CAT else None
CAT2 = CAT[1] if len(CAT) > 1 else None
NUM1 = (obj if obj in NUM else NUM[0]) if NUM else None
FECHA = FEC[0] if FEC else None
tabla = cfg["nombre_tabla"]
df.createOrReplaceTempView(tabla)
print(f"CAT1={CAT1} | CAT2={CAT2} | NUM1={NUM1} | FECHA={FECHA}")

# ------------------------------------------------------------------ E1
titulo("E1 · RDD: valores distintos y conteo de palabras")
if CAT1:
    valores = df.select(CAT1).rdd.map(lambda r: r[0])
    print(f"a) Valores distintos de {CAT1}: {valores.distinct().count()}")
lineas = (df.select(TXT[0]).dropna().rdd.map(lambda r: str(r[0])) if TXT
          else sc.textFile(str(ruta_absoluta("data/ejemplo/texto_bigdata.txt"))))
palabras = lineas.flatMap(lambda l: re.findall(r"\w+", l.lower())).cache()
print(f"b) Palabras: {palabras.count()} | distintas: {palabras.distinct().count()}")
iniciales = (palabras.map(lambda p: (p[0], 1)).reduceByKey(lambda a, b: a + b)
             .takeOrdered(5, key=lambda kv: -kv[1]))
print("   Letras iniciales más frecuentes:", iniciales)

# ------------------------------------------------------------------ E2
titulo("E2 · Tabla dinámica")
if CAT1 and NUM1:
    if FECHA:
        base, filas = df.withColumn("mes", F.month(FECHA)), "mes"     # meses en filas
    else:
        base, filas = df, (CAT2 or CAT1)                              # segunda categoría en filas
    (base.groupBy(filas).pivot(CAT1).agg(F.sum(NUM1).cast("decimal(22,0)"))     # CAT1 en columnas
         .orderBy(filas).show(13, truncate=False))

# ------------------------------------------------------------------ E3
titulo("E3 · Diez grupos con mayor suma")
if CAT1 and NUM1:
    grupo = [c for c in (CAT1, CAT2) if c]
    (df.groupBy(*grupo)
       .agg(F.count("*").alias("registros"), F.sum(NUM1).cast("decimal(22,2)").alias("suma"))
       .orderBy(F.desc("suma")).show(10, truncate=False))

# ------------------------------------------------------------------ E4
titulo("E4 · Reporte de calidad")
reglas = [F.sum(F.col(c).isNull().cast("int")).alias(f"nulos_{c}") for c in df.columns]
reglas += [F.sum((F.col(c) < 0).cast("int")).alias(f"negativos_{c}") for c in NUM]
reporte = df.agg(*reglas).first().asDict()
print({k: v for k, v in reporte.items() if v})
print("Duplicados exactos:", df.count() - df.dropDuplicates().count())

# ------------------------------------------------------------------ E5
titulo("E5 · Categoría con mayor suma dentro de cada grupo (ROW_NUMBER)")
if CAT1 and CAT2 and NUM1:
    spark.sql(f"""
    WITH t AS (SELECT `{CAT1}`, `{CAT2}`, SUM(`{NUM1}`) AS suma FROM {tabla} GROUP BY 1, 2)
    SELECT `{CAT1}`, `{CAT2}`, CAST(suma AS DECIMAL(22,2)) AS suma
    FROM (SELECT *, ROW_NUMBER() OVER (PARTITION BY `{CAT1}` ORDER BY suma DESC) AS rn FROM t)
    WHERE rn = 1 ORDER BY suma DESC
    """).show(truncate=False)

# ------------------------------------------------------------------ E6
titulo("E6 · Variación mensual (LAG)")
if FECHA and NUM1:
    spark.sql(f"""
    WITH m AS (SELECT DATE_TRUNC('month', `{FECHA}`) AS periodo, SUM(`{NUM1}`) AS s
               FROM {tabla} WHERE `{FECHA}` IS NOT NULL GROUP BY 1)
    SELECT DATE_FORMAT(periodo, 'yyyy-MM') AS mes, CAST(s AS DECIMAL(22,2)) AS suma,
           ROUND(100 * (s - LAG(s) OVER (ORDER BY periodo)) / LAG(s) OVER (ORDER BY periodo), 1) AS variacion_pct
    FROM m ORDER BY periodo
    """).show(36)
else:
    print("El dataset no tiene fecha o variable numérica.")

# ------------------------------------------------------------------ E7
titulo("E7 · CSV frente a Parquet")
tmp = RAIZ / "data" / "procesado" / "_e7"
shutil.rmtree(tmp, ignore_errors=True)
simple = df.select([c for c, t in df.dtypes if not t.startswith(("array", "struct", "map"))])
simple.write.mode("overwrite").option("header", True).csv(str(tmp / "csv"))
simple.write.mode("overwrite").parquet(str(tmp / "parquet"))


def medir(fn):
    t = time.time()
    fn()
    return time.time() - t


if NUM1:
    t_csv = medir(lambda: spark.read.csv(str(tmp / "csv"), header=True, inferSchema=True)
                  .agg(F.sum(NUM1)).collect())
    t_pq = medir(lambda: spark.read.parquet(str(tmp / "parquet")).agg(F.sum(NUM1)).collect())
    print(f"a) Tiempo  CSV: {t_csv:.2f} s | Parquet: {t_pq:.2f} s")
print(f"b) Tamaño  CSV: {tamano_mb(tmp / 'csv'):.2f} MB | Parquet: {tamano_mb(tmp / 'parquet'):.2f} MB")
print("""c) Parquet es un formato columnar: lee solo las columnas que requiere la consulta,
   comprime mejor porque los valores de una misma columna son homogéneos, conserva el
   esquema (no es necesario inferirlo) y almacena estadísticas (mínimo/máximo) que permiten
   omitir bloques completos (The Apache Software Foundation, s.f.). CSV, en cambio, obliga
   a leer e interpretar todo el texto.""")
shutil.rmtree(tmp, ignore_errors=True)

spark.stop()
