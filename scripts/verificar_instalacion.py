#!/usr/bin/env python3
"""
Verifica que el entorno del taller esté listo:
  - Versión de Python
  - Java disponible y versión >= 17
  - PySpark importable
  - Una SparkSession se crea y ejecuta un trabajo
  - Lectura/escritura de archivos (Parquet) funciona

Uso:  python scripts/verificar_instalacion.py
"""
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile

OK, FAIL, WARN, INFO = "[OK]   ", "[ERROR]", "[AVISO]", "[INFO] "
errores = 0


def linea(icono, msg):
    print(f"{icono} {msg}")


print("=" * 60)
print(" Verificación del entorno - Taller de Apache Spark")
print("=" * 60)
linea(INFO, f"Sistema operativo: {platform.system()} {platform.release()} ({platform.machine()})")

# 1. Python ------------------------------------------------------------------
v = sys.version_info
if v >= (3, 10):
    linea(OK, f"Python {v.major}.{v.minor}.{v.micro}  ({sys.executable})")
else:
    linea(FAIL, f"Python {v.major}.{v.minor} detectado. Se requiere 3.10 o superior.")
    errores += 1

# 2. Java --------------------------------------------------------------------
java = shutil.which("java")
if os.environ.get("JAVA_HOME"):
    candidato = os.path.join(os.environ["JAVA_HOME"], "bin", "java")
    if shutil.which(candidato):
        java = candidato
if not java:
    linea(FAIL, "Java no encontrado. Se requiere instalar JDK 17 o 21 y configurar JAVA_HOME.")
    errores += 1
else:
    salida = subprocess.run([java, "-version"], capture_output=True, text=True).stderr
    m = re.search(r'version "(\d+)(?:\.(\d+))?', salida)
    mayor = int(m.group(1)) if m else 0
    if mayor == 1 and m and m.group(2):  # formato antiguo 1.8
        mayor = int(m.group(2))
    if mayor >= 17:
        linea(OK, f"Java {mayor}  ({java})")
    else:
        linea(FAIL, f"Java {mayor} detectado. Spark 4.x requiere Java 17 o 21.")
        errores += 1
linea(INFO, f"JAVA_HOME  = {os.environ.get('JAVA_HOME', '(no definido)')}")
linea(INFO, f"SPARK_HOME = {os.environ.get('SPARK_HOME', '(no definido - se usará PySpark de pip)')}")
if platform.system() == "Windows":
    hh = os.environ.get("HADOOP_HOME")
    if hh and os.path.exists(os.path.join(hh, "bin", "winutils.exe")):
        linea(OK, f"HADOOP_HOME con winutils.exe ({hh})")
    else:
        linea(WARN, "HADOOP_HOME/winutils.exe no encontrado: la escritura de archivos puede fallar.")

# 3. PySpark -----------------------------------------------------------------
try:
    import pyspark

    linea(OK, f"PySpark {pyspark.__version__} importado")
except ImportError:
    linea(FAIL, "PySpark no instalado. Ejecutar: pip install -r requirements.txt")
    errores += 1
    sys.exit(1)

if errores:
    print(f"\n{FAIL} Deben corregirse los errores anteriores antes de continuar.")
    sys.exit(1)

# 4. SparkSession ------------------------------------------------------------
from pyspark.sql import SparkSession  # noqa: E402
from pyspark.sql import functions as F  # noqa: E402

try:
    spark = (
        SparkSession.builder.appName("VerificacionTaller")
        .master("local[*]")
        .config("spark.ui.showConsoleProgress", "false")
        .config("spark.sql.shuffle.partitions", "4")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("ERROR")
    linea(OK, f"SparkSession creada - Spark {spark.version}, master={spark.sparkContext.master}")
    linea(INFO, f"Spark UI: {spark.sparkContext.uiWebUrl}")

    total = spark.range(1, 1_000_001).agg(F.sum("id")).first()[0]
    assert total == 500000500000, total
    linea(OK, f"Trabajo de prueba: suma 1..1.000.000 = {total:,}")

    # 5. Escritura / lectura Parquet
    tmp = tempfile.mkdtemp(prefix="spark_test_")
    ruta = os.path.join(tmp, "prueba.parquet")
    df = spark.createDataFrame([(1, "Spark"), (2, "Big Data")], ["id", "texto"])
    df.write.mode("overwrite").parquet(ruta)
    assert spark.read.parquet(ruta).count() == 2
    shutil.rmtree(tmp, ignore_errors=True)
    linea(OK, "Escritura y lectura de Parquet")

    spark.stop()
except Exception as e:  # noqa: BLE001
    linea(FAIL, f"Error al ejecutar Spark: {type(e).__name__}: {str(e)[:400]}")
    print("        Consultar docs/06-solucion-problemas.md")
    sys.exit(1)

print("\n" + "=" * 60)
print(f"{OK} Spark funciona correctamente. El entorno está listo para el taller.")
print("=" * 60)
