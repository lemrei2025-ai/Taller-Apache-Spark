# 2. Instalación de Apache Spark en Linux (Ubuntu/Debian)

El script `bash scripts/instalar_spark_linux.sh` ejecuta todos los pasos de esta guía de forma automática.

El procedimiento fue probado en Ubuntu 22.04 y 24.04 y en Debian 12. También aplica a WSL2 en Windows.

## Paso 1. Actualización del sistema e instalación de dependencias

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y openjdk-17-jdk python3 python3-pip python3-venv wget curl git
```

Verificación:

```bash
java -version     # openjdk version "17.x"
python3 --version # Python 3.10 o superior
```

## Paso 2. Descarga de Spark

Los paquetes oficiales se obtienen del sitio de descargas del proyecto (The Apache Software Foundation [ASF], 2026f):

```bash
SPARK_VERSION=4.3.0
cd /tmp
wget https://dlcdn.apache.org/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop3.tgz
```

Cuando el enlace no está disponible (las versiones anteriores se trasladan al archivo histórico),
se utiliza:
`https://archive.apache.org/dist/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop3.tgz`

Verificación opcional de integridad:

```bash
wget https://downloads.apache.org/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop3.tgz.sha512
sha512sum -c spark-${SPARK_VERSION}-bin-hadoop3.tgz.sha512
```

## Paso 3. Descompresión en `/opt/spark`

```bash
tar -xzf spark-${SPARK_VERSION}-bin-hadoop3.tgz
sudo mv spark-${SPARK_VERSION}-bin-hadoop3 /opt/spark
sudo chown -R $USER:$USER /opt/spark
```

## Paso 4. Variables de entorno

Las variables se agregan al final de `~/.bashrc` (o `~/.zshrc`):

```bash
cat >> ~/.bashrc <<'EOF'

# ---- Apache Spark ----
export JAVA_HOME=$(dirname $(dirname $(readlink -f $(which java))))
export SPARK_HOME=/opt/spark
export PATH=$PATH:$SPARK_HOME/bin:$SPARK_HOME/sbin
export PYSPARK_PYTHON=python3
EOF

source ~/.bashrc
```

## Paso 5. Verificación

```bash
spark-submit --version
echo 'spark.range(10).show()' | pyspark   # prueba rápida
```

Consolas interactivas disponibles:

```bash
pyspark        # Python
spark-shell    # Scala
spark-sql      # SQL
```

Ejecución de un ejemplo incluido en la distribución:

```bash
spark-submit $SPARK_HOME/examples/src/main/python/pi.py 10
# ... Pi is roughly 3.14...
```

## Paso 6. Entorno de Python del taller

```bash
git clone https://github.com/<usuario>/taller-apache-spark.git
cd taller-apache-spark
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/verificar_instalacion.py
jupyter lab
```

El paquete `pyspark` instalado con pip incluye su propia copia de Spark (ASF, 2026e). Si se desea
que los cuadernos utilicen la instalación de `/opt/spark`, la versión de `pyspark` debe coincidir
(4.3.0) o puede emplearse `findspark`:

```python
import findspark; findspark.init("/opt/spark")
```

## Paso 7 (opcional). Clúster *Standalone* en el equipo local

El modo *Standalone* permite levantar un nodo maestro y uno o varios *workers* en la misma máquina (ASF, 2026d):

```bash
# Inicio del maestro (interfaz web en http://localhost:8080)
$SPARK_HOME/sbin/start-master.sh

# Inicio de un worker conectado al maestro
$SPARK_HOME/sbin/start-worker.sh spark://$(hostname):7077 --cores 2 --memory 2g

# Envío de un trabajo al clúster
spark-submit --master spark://$(hostname):7077 src/wordcount.py data/ejemplo/texto_bigdata.txt

# Detención de los servicios
$SPARK_HOME/sbin/stop-worker.sh
$SPARK_HOME/sbin/stop-master.sh
```

## Problemas frecuentes

| Problema | Solución |
|----------|----------|
| `JAVA_HOME is not set` | Revisar el paso 4 y ejecutar `source ~/.bashrc` |
| `Unsupported class file major version` | Se está usando Java 8 u 11; instalar JDK 17 o 21 |
| `WARN NativeCodeLoader: Unable to load native-hadoop library` | Advertencia normal; puede ignorarse |
| Puerto 4040 ocupado | Spark utiliza automáticamente los puertos 4041, 4042, etc. |

## Referencias

The Apache Software Foundation. (2026d). *Spark standalone mode* (Versión 4.3.0) [Documentación técnica]. https://spark.apache.org/docs/latest/spark-standalone.html

The Apache Software Foundation. (2026e). *PySpark documentation* (Versión 4.3.0) [Documentación técnica]. https://spark.apache.org/docs/latest/api/python/

The Apache Software Foundation. (2026f). *Download Apache Spark* [Página web]. Recuperado el 8 de noviembre de 2026, de https://spark.apache.org/downloads.html
