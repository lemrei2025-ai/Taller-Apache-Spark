#!/usr/bin/env python3
"""
Structured Streaming: conteo de palabras en tiempo real.

Modo 1 - Socket (requiere netcat):
   Terminal 1:  nc -lk 9999          (Windows: ncat -lk 9999, viene con Nmap)
   Terminal 2:  spark-submit src/streaming_wordcount.py socket
   Las frases escritas en la Terminal 1 se cuentan y se muestran en la Terminal 2.

Modo 2 - Carpeta (no requiere netcat):
   spark-submit src/streaming_wordcount.py carpeta entrada_stream/
   Los archivos .txt copiados en entrada_stream/ se procesan mientras el programa se ejecuta.

La ejecución se detiene con Ctrl+C.
"""
import sys

from pyspark.sql import SparkSession
from pyspark.sql import functions as F


def main():
    modo = sys.argv[1] if len(sys.argv) > 1 else "socket"
    spark = (SparkSession.builder.appName("StreamingWordCount")
             .config("spark.sql.shuffle.partitions", "4")
             .getOrCreate())
    spark.sparkContext.setLogLevel("WARN")

    if modo == "socket":
        lineas = (spark.readStream.format("socket")
                  .option("host", "localhost").option("port", 9999).load())
    else:
        carpeta = sys.argv[2] if len(sys.argv) > 2 else "entrada_stream"
        lineas = spark.readStream.format("text").load(carpeta)

    palabras = lineas.select(F.explode(F.split(F.lower("value"), r"\W+")).alias("palabra")) \
                     .filter(F.length("palabra") > 2)
    conteo = palabras.groupBy("palabra").count().orderBy(F.desc("count"))

    consulta = (conteo.writeStream
                .outputMode("complete")
                .format("console")
                .option("numRows", 15)
                .trigger(processingTime="5 seconds")
                .start())
    consulta.awaitTermination()


if __name__ == "__main__":
    main()
