# 5. Uso de Spark en Google Colab (sin instalación local)

Esta alternativa resulta adecuada cuando el equipo dispone de pocos recursos o el estudiante no
cuenta con permisos de administrador.

## Paso 1. Apertura de un cuaderno

1. Se ingresa a <https://colab.research.google.com/>.
2. En *Archivo > Abrir cuaderno > GitHub* se indica la URL del repositorio, o bien se carga un archivo `.ipynb` de la carpeta `notebooks/`.

## Paso 2. Instalación de PySpark (primera celda)

```python
!pip install -q pyspark==4.3.0
!java -version
```

Colab incluye Java. Si la versión instalada es anterior a la 17, se ejecuta:

```python
!apt-get install -y -qq openjdk-17-jdk-headless > /dev/null
import os
os.environ["JAVA_HOME"] = "/usr/lib/jvm/java-17-openjdk-amd64"
```

## Paso 3. Obtención de los datos del taller

```python
!git clone -q https://github.com/<usuario>/taller-apache-spark.git
%cd taller-apache-spark
```

## Paso 4. Creación de la sesión

```python
from pyspark.sql import SparkSession
spark = SparkSession.builder.master("local[*]").appName("Colab").getOrCreate()
spark
```

## Paso 5. Acceso a la Spark UI (opcional)

La interfaz web se ejecuta en el puerto 4040 de la máquina virtual de Colab y puede abrirse con:

```python
from google.colab.output import eval_js
print(eval_js("google.colab.kernel.proxyPort(4040)"))
```

## Limitaciones

- La sesión se reinicia tras un periodo de inactividad, por lo que debe repetirse la instalación.
- Se trata de un único nodo (modo `local`), no de un clúster real.
- Los archivos generados se pierden al cerrar la sesión; deben descargarse o guardarse en Google Drive:

```python
from google.colab import drive
drive.mount('/content/drive')
```
