#!/usr/bin/env python3
"""
Conteo de palabras (WordCount) - el "Hola Mundo" de Big Data.

Ejecutar:
  spark-submit src/wordcount.py data/ejemplo/texto_bigdata.txt
  spark-submit --master local[4] src/wordcount.py data/ejemplo/texto_bigdata.txt data/procesado/wordcount
  spark-submit --master spark://spark-master:7077 src/wordcount.py data/ejemplo/texto_bigdata.txt
"""
import re
import sys

from pyspark.sql import SparkSession

# Palabras muy comunes que no aportan información
STOPWORDS = {
    "de", "la", "el", "en", "y", "a", "los", "las", "que", "un", "una", "por", "con",
    "para", "se", "es", "del", "al", "o", "como", "sobre", "son", "lo", "su", "sus",
}


def main():
    if len(sys.argv) < 2:
        print("Uso: spark-submit wordcount.py <archivo_entrada> [carpeta_salida]")
        sys.exit(1)
    entrada = sys.argv[1]
    salida = sys.argv[2] if len(sys.argv) > 2 else None

    spark = SparkSession.builder.appName("WordCount").getOrCreate()
    sc = spark.sparkContext
    sc.setLogLevel("WARN")

    conteo = (
        sc.textFile(entrada)                                     # RDD de líneas
        .flatMap(lambda linea: re.findall(r"\w+", linea.lower()))  # línea -> palabras
        .filter(lambda p: p not in STOPWORDS and len(p) > 2)       # quitar stopwords
        .map(lambda p: (p, 1))                                     # (palabra, 1)
        .reduceByKey(lambda a, b: a + b)                           # sumar por palabra (shuffle)
        .sortBy(lambda par: par[1], ascending=False)
    )

    print("\nTop 15 palabras:")
    print("-" * 30)
    for palabra, n in conteo.take(15):
        print(f"{palabra:<20}{n:>5}")

    if salida:
        conteo.map(lambda par: f"{par[0]},{par[1]}").saveAsTextFile(salida)
        print(f"\nResultado completo guardado en: {salida}")

    spark.stop()


if __name__ == "__main__":
    main()
