#!/usr/bin/env python3
"""
Pipeline ETL de ventas: CSV/JSON (crudo) -> limpieza -> enriquecimiento -> Parquet particionado.

  Extract   : lee ventas.csv, clientes.csv y productos.json
  Transform : limpia nulos/errores, calcula total, une con clientes y productos
  Load      : escribe Parquet particionado por mes + reporte agregado

Ejecutar:
  spark-submit src/etl_ventas.py --datos data --salida salida
"""
import argparse
import time

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (DoubleType, IntegerType, StringType, StructField,
                               StructType, DateType)

ESQUEMA_VENTAS = StructType([
    StructField("id_venta", IntegerType(), False),
    StructField("fecha", DateType(), True),
    StructField("id_cliente", IntegerType(), True),
    StructField("id_producto", IntegerType(), True),
    StructField("cantidad", IntegerType(), True),
    StructField("precio_unitario", DoubleType(), True),
    StructField("descuento", DoubleType(), True),
    StructField("canal", StringType(), True),
    StructField("metodo_pago", StringType(), True),
])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datos", default="data")
    ap.add_argument("--salida", default="salida")
    args = ap.parse_args()

    spark = (SparkSession.builder.appName("ETL_Ventas")
             .config("spark.sql.shuffle.partitions", "8")
             .getOrCreate())
    spark.sparkContext.setLogLevel("WARN")
    t0 = time.time()

    # ---------------- EXTRACT
    ventas = spark.read.csv(f"{args.datos}/ventas.csv", header=True, schema=ESQUEMA_VENTAS)
    clientes = spark.read.csv(f"{args.datos}/clientes.csv", header=True, inferSchema=True)
    productos = spark.read.json(f"{args.datos}/productos.json")
    n_crudo = ventas.count()

    # ---------------- TRANSFORM
    ventas_limpias = (
        ventas
        .filter(F.col("cantidad").isNotNull() & (F.col("cantidad") > 0))
        .fillna({"canal": "Desconocido"})
        .withColumn("total", F.round(F.col("cantidad") * F.col("precio_unitario")
                                     * (1 - F.col("descuento")), 2))
        .withColumn("anio", F.year("fecha"))
        .withColumn("mes", F.month("fecha"))
    )
    n_limpio = ventas_limpias.count()

    enriquecidas = (
        ventas_limpias
        .join(productos.select("id_producto", "producto", "categoria"), "id_producto", "left")
        .join(F.broadcast(clientes.select("id_cliente", "ciudad", "region", "segmento")),
              "id_cliente", "left")
    )

    # ---------------- LOAD
    (enriquecidas.write.mode("overwrite")
     .partitionBy("anio", "mes")
     .parquet(f"{args.salida}/ventas_parquet"))

    reporte = (
        enriquecidas.groupBy("region", "categoria")
        .agg(F.count("*").alias("num_ventas"),
             F.round(F.sum("total"), 0).cast("long").alias("ingresos"),
             F.round(F.avg("total"), 0).cast("long").alias("ticket_promedio"))
        .orderBy(F.desc("ingresos"))
    )
    reporte.coalesce(1).write.mode("overwrite").option("header", True) \
        .csv(f"{args.salida}/reporte_region_categoria")

    print("\n===== RESUMEN ETL =====")
    print(f"Registros crudos     : {n_crudo:,}")
    print(f"Registros válidos    : {n_limpio:,}")
    print(f"Registros descartados: {n_crudo - n_limpio:,}")
    print(f"Tiempo               : {time.time() - t0:.1f} s")
    print("\nTop 10 región/categoría por ingresos:")
    reporte.show(10, truncate=False)

    spark.stop()


if __name__ == "__main__":
    main()
