#!/usr/bin/env python3
"""
ETL genérico para spark-submit: aplica una limpieza básica al dataset configurado en
data/dataset_config.json y lo guarda en Parquet.

Pasos: lectura con detección automática -> eliminación de duplicados -> limpieza de espacios
en textos -> eliminación de filas sin variable objetivo -> variables de fecha -> Parquet.

Ejecutar desde la raíz del repositorio:
  spark-submit src/etl_generico.py
  spark-submit src/etl_generico.py --ruta data/mis_datos/archivo.csv --salida data/procesado/archivo_etl
  spark-submit --master spark://spark-master:7077 src/etl_generico.py      (Docker)
"""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
from taller_spark import (cargar_dataset, columna_objetivo, iniciar_spark, leer_config,  # noqa: E402
                          normalizar_nombre, parametros_carga, ruta_absoluta, tamano_mb)
from pyspark.sql import functions as F  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ruta", help="archivo de entrada (por defecto, el de la configuración)")
    ap.add_argument("--salida", help="carpeta de salida Parquet")
    args = ap.parse_args()

    cfg = leer_config()
    if args.ruta:
        cfg["ruta"] = args.ruta
    salida = args.salida or f"data/procesado/{cfg['nombre']}_etl"

    spark = iniciar_spark("ETL_Generico")
    t0 = time.time()

    df, _ = cargar_dataset(spark, **parametros_carga(cfg))
    n0 = df.count()

    df = df.dropDuplicates()
    for c, t in df.dtypes:
        if t == "string":
            df = df.withColumn(c, F.regexp_replace(F.trim(F.col(c)), r"\s+", " "))
    obj = columna_objetivo(cfg, df)
    if obj:
        df = df.dropna(subset=[obj])

    fecha = normalizar_nombre(cfg["columna_fecha"]) if cfg.get("columna_fecha") else None
    particion = []
    if fecha in df.columns and dict(df.dtypes)[fecha] in ("date", "timestamp", "timestamp_ntz"):
        df = df.withColumn("anio", F.year(fecha)).withColumn("mes", F.month(fecha))
        particion = ["anio"]

    escritor = df.write.mode("overwrite")
    if particion:
        escritor = escritor.partitionBy(*particion)
    escritor.parquet(str(ruta_absoluta(salida)))
    n1 = spark.read.parquet(str(ruta_absoluta(salida))).count()

    print("\n===== RESUMEN ETL =====")
    print(f"Dataset              : {cfg['nombre']} ({cfg['ruta']})")
    print(f"Registros de entrada : {n0:,}")
    print(f"Registros de salida  : {n1:,}")
    print(f"Tamaño original      : {tamano_mb(cfg['ruta']):.2f} MB")
    print(f"Tamaño Parquet       : {tamano_mb(salida):.2f} MB  ({salida})")
    print(f"Tiempo               : {time.time() - t0:.1f} s")
    spark.stop()


if __name__ == "__main__":
    main()
