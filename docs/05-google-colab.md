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

## Paso 3. Obtención del taller

Los cuadernos del taller ubican automáticamente su carpeta. Al abrir un cuaderno del repositorio
en Colab, basta con escribir en la variable `REPO_URL` de la celda de preparación la dirección del
repositorio (reemplazando `<usuario>`): si el taller no está descargado, la celda lo clona en
`/content/taller-apache-spark`. También puede clonarse de forma manual:

```python
!git clone -q https://github.com/<usuario>/taller-apache-spark.git /content/taller-apache-spark
%cd /content/taller-apache-spark/notebooks
```

La celda de preparación también encuentra el taller si se clonó con otro nombre dentro de
`/content` o si se copió en Google Drive (`/content/drive/MyDrive/`), e instala en Colab las
dependencias que falten (PySpark 4.x y openpyxl).

Si aparece el error `Input path does not exist: file:/data/...`, se está usando una versión
anterior de los cuadernos: debe actualizarse el repositorio en GitHub (véase la guía
[07-subir-a-github.md](07-subir-a-github.md)) y abrir de nuevo el cuaderno.

No deben utilizarse rutas relativas como `"../data"` fuera de la celda de preparación: en Colab
la carpeta de trabajo inicial es `/content`, de modo que `"../data"` apunta a `/data`, que no
existe, y Spark responde con el error `Input path does not exist: file:/data/...`.

Para analizar un dataset propio en Colab, se carga el archivo con la celda correspondiente del
cuaderno 00 (`files.upload()`), que lo guarda en `data/mis_datos/`.

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
