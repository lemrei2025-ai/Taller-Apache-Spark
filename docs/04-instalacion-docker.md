# 4. Spark con Docker: clúster local (maestro, dos workers y JupyterLab)

Esta opción no requiere instalar Java ni Spark en el equipo y, además, permite observar el
funcionamiento de un clúster *Standalone* con varios nodos *worker* (The Apache Software Foundation
[ASF], 2026d). La orquestación de los contenedores se realiza con Docker Compose (Docker Inc., s.f.).

## Requisitos

- Docker Desktop (Windows/macOS) o Docker Engine con el complemento Compose (Linux): <https://docs.docker.com/get-docker/>
- Al menos 6 GB de memoria asignados a Docker (Docker Desktop > Settings > Resources).

## Arquitectura

```
+------------------------ red: spark-net ------------------------+
|                                                                |
|  +--------------+    +---------------+    +---------------+    |
|  | spark-master |<---+ spark-worker-1|    | spark-worker-2|    |
|  |  :7077 :8080 |<---+  :8081        |    |  :8082        |    |
|  +------^-------+    +---------------+    +---------------+    |
|         |                                                      |
|  +------+-------+                                              |
|  |   jupyter    |  notebooks/, data/ y src/ montados           |
|  | :8888 :4040  |                                              |
|  +--------------+                                              |
+----------------------------------------------------------------+
```

## Paso 1. Construcción e inicio de los contenedores

Desde la raíz del repositorio:

```bash
cd docker
docker compose up -d --build
docker compose ps
```

La primera ejecución tarda algunos minutos, pues se descarga la imagen base y se instala PySpark.

## Paso 2. Interfaces web

| Servicio | URL |
|----------|-----|
| JupyterLab | <http://localhost:8888> (token: `bigdata`) |
| Interfaz del maestro | <http://localhost:8080> |
| Interfaz del worker 1 | <http://localhost:8081> |
| Interfaz del worker 2 | <http://localhost:8082> |
| Interfaz de la aplicación (Spark UI) | <http://localhost:4040> (con una sesión activa) |

En la interfaz del maestro deben aparecer dos *workers* en estado ALIVE.

## Paso 3. Conexión al clúster desde un cuaderno

En JupyterLab se crea la sesión apuntando al maestro:

```python
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("TallerDocker")
         .master("spark://spark-master:7077")
         .config("spark.executor.memory", "1g")
         .getOrCreate())

spark.range(0, 10_000_000).selectExpr("sum(id)").show()
```

Los cuadernos del taller leen la variable de entorno `SPARK_MASTER`. Dentro del contenedor esta
variable tiene el valor `spark://spark-master:7077`, por lo que los cuadernos se conectan al clúster
de forma automática; fuera de Docker utilizan `local[*]`.

En <http://localhost:8080> puede comprobarse que la aplicación TallerDocker figura en la sección
*Running Applications*.

## Paso 4. Ejecución de `spark-submit` sobre el clúster

```bash
docker compose exec jupyter spark-submit \
  --master spark://spark-master:7077 \
  /home/jovyan/work/src/wordcount.py /home/jovyan/work/data/texto_bigdata.txt
```

## Paso 5. Escalamiento de workers

```bash
docker compose up -d --scale spark-worker-2=3   # tres réplicas del worker 2
```

Para escalar es necesario retirar el mapeo de puerto fijo del servicio, a fin de evitar conflictos.

## Paso 6. Detención

```bash
docker compose down        # detiene y elimina los contenedores
docker compose down -v     # además elimina los volúmenes
```

## Problemas frecuentes

| Problema | Solución |
|----------|----------|
| Los workers no aparecen en el maestro | Revisar `docker compose logs spark-worker-1` y esperar entre 10 y 20 segundos |
| `port is already allocated` | Otro servicio ocupa el puerto 8080 u 8888; modificarlo en `docker-compose.yml` |
| Contenedores reiniciados o `OOMKilled` | Aumentar la memoria asignada a Docker o reducir `SPARK_WORKER_MEMORY` |
| Archivos no encontrados en el clúster | Utilizar rutas `/home/jovyan/work/data/...`; el volumen está montado en todos los nodos |

## Referencias

Docker Inc. (s.f.). *Docker Compose overview* [Documentación técnica]. Recuperado el 8 de noviembre de 2026, de https://docs.docker.com/compose/

The Apache Software Foundation. (2026d). *Spark standalone mode* (Versión 4.3.0) [Documentación técnica]. https://spark.apache.org/docs/latest/spark-standalone.html
