#!/usr/bin/env python3
"""
Verifica que el entorno del taller esté listo y corrige automáticamente la
configuración de Java cuando es posible:
  - Versión de Python (3.10 a 3.14)
  - Java 17 o 21. Si JAVA_HOME apunta a otra versión (por ejemplo, Java 8) o a una
    instalación dañada, se busca un JDK compatible que funcione, se activa y se guardan
    JAVA_HOME y el Path. Si no existe ninguno, se ofrece instalar Eclipse Temurin 17.
  - PySpark importable
  - Una SparkSession se crea y ejecuta un trabajo
  - Lectura/escritura de archivos (Parquet) funciona

Uso:
  python scripts/verificar_instalacion.py                 # verifica y corrige
  python scripts/verificar_instalacion.py --instalar-java # instala Java 17 sin preguntar
  python scripts/verificar_instalacion.py --reinstalar-java  # reinstala Java 17
  python scripts/verificar_instalacion.py --sistema       # Windows (administrador): variables del sistema
  python scripts/verificar_instalacion.py --solo-sesion   # no guarda cambios permanentes
"""
import argparse
import os
import platform
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from configurar_java import asegurar_java, diagnostico  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--instalar-java", action="store_true", help="instala Java 17 si no se encuentra")
ap.add_argument("--reinstalar-java", action="store_true", help="reinstala Java 17 aunque exista")
ap.add_argument("--sistema", action="store_true", help="Windows (administrador): corrige variables del sistema")
ap.add_argument("--solo-sesion", action="store_true", help="no guarda JAVA_HOME de forma permanente")
args = ap.parse_args()

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
if (3, 10) <= v[:2] <= (3, 14):
    linea(OK, f"Python {v.major}.{v.minor}.{v.micro}  ({sys.executable})")
elif v[:2] > (3, 14):
    linea(WARN, f"Python {v.major}.{v.minor} es más reciente que las versiones probadas (3.10 a 3.14).")
else:
    linea(FAIL, f"Python {v.major}.{v.minor} detectado. Se requiere 3.10 o superior.")
    errores += 1

# 2. Java (detección y corrección automática) ---------------------------------
home = asegurar_java(persistir=not args.solo_sesion, instalar=args.instalar_java, preguntar=True,
                     reinstalar=args.reinstalar_java, sistema=args.sistema)
if home is None:
    errores += 1
    diagnostico()
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
