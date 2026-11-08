# 0. Conceptos fundamentales de Apache Spark

## Definición

Apache Spark es un motor de procesamiento distribuido, de código abierto, orientado al análisis de
grandes volúmenes de datos. Su principal diferencia frente a Hadoop MapReduce (Dean & Ghemawat, 2008)
es que mantiene los datos intermedios en memoria, lo que reduce el acceso a disco entre etapas.
Zaharia et al. (2012) reportaron que este enfoque supera a Hadoop hasta en 20 veces en aplicaciones
iterativas, como los algoritmos de aprendizaje automático.

Spark ofrece interfaces de programación para Python (PySpark), Scala, Java, R y SQL
(The Apache Software Foundation [ASF], 2026a).

## Relevancia en Big Data

El término *Big Data* suele describirse a partir de las dimensiones de volumen, velocidad y variedad
(Laney, 2001), a las que con frecuencia se agregan veracidad y valor. Spark aborda estas dimensiones
con un único motor que integra procesamiento por lotes, consultas SQL, flujos en tiempo real y
aprendizaje automático (Zaharia et al., 2016).

| Característica | Hadoop MapReduce | Apache Spark |
|----------------|------------------|--------------|
| Procesamiento | En disco entre etapas | En memoria |
| Desempeño en tareas iterativas | Bajo | Alto (Zaharia et al., 2012) |
| Interfaz de programación | Funciones *map* y *reduce* de bajo nivel | RDD, DataFrame, SQL, ML, Streaming |
| Uso interactivo | No | Sí (consola y cuadernos) |
| Procesamiento de flujos | No nativo | Structured Streaming (Armbrust et al., 2018) |

## Componentes del ecosistema

```
+------------+--------------+------------+--------------+
| Spark SQL  |  Structured  |   MLlib    |   GraphX /   |
| DataFrames |  Streaming   | (Machine   |  GraphFrames |
|            |              |  Learning) |              |
+------------+--------------+------------+--------------+
|                    Spark Core (RDD)                   |
+-------------------------------------------------------+
| Gestor de clúster: Standalone | YARN | Kubernetes | local |
+-------------------------------------------------------+
| Almacenamiento: local, HDFS, S3, ADLS, GCS, Hive, ...  |
+-------------------------------------------------------+
```

- **Spark SQL**: módulo para datos estructurados que incorpora el optimizador Catalyst (Armbrust et al., 2015).
- **Structured Streaming**: procesamiento de flujos con la misma API de DataFrames (Armbrust et al., 2018).
- **MLlib**: biblioteca de aprendizaje automático distribuido (Meng et al., 2016).

## Arquitectura

```
                 +---------------------+
                 |   Driver Program    |
                 |   (SparkSession)    |
                 +----------+----------+
                            |
                 +----------v----------+
                 |  Gestor de clúster  |
                 | (Standalone/YARN/K8s)|
                 +----+-----------+----+
                      |           |
           +----------v--+   +----v--------+
           |  Worker 1   |   |  Worker 2   |
           | +---------+ |   | +---------+ |
           | |Executor | |   | |Executor | |
           | | Task    | |   | | Task    | |
           | | Task    | |   | | Task    | |
           | +---------+ |   | +---------+ |
           +-------------+   +-------------+
```

De acuerdo con la documentación oficial (ASF, 2026a):

- **Driver**: proceso que ejecuta el programa principal, crea la `SparkSession`, construye el plan de ejecución y distribuye las tareas.
- **Gestor de clúster**: asigna los recursos de CPU y memoria. En el taller se emplean el modo `local[*]` y un clúster *Standalone* sobre Docker (ASF, 2026d).
- **Executors**: procesos que se ejecutan en los nodos *worker*, realizan las tareas y almacenan datos en caché.
- **Task**: unidad mínima de trabajo; se crea una por cada partición de datos.

## Conceptos clave

### RDD (Resilient Distributed Dataset)

Colección inmutable de objetos distribuida en particiones. Constituye la abstracción de bajo nivel
de Spark. Su tolerancia a fallos proviene del **linaje** (*lineage*): si se pierde una partición,
Spark la reconstruye a partir de las transformaciones que la originaron (Zaharia et al., 2012).

### DataFrame

Colección distribuida organizada en columnas con nombre, equivalente a una tabla relacional.
Las consultas sobre DataFrames pasan por el optimizador Catalyst, razón por la cual constituyen la
interfaz recomendada para la mayoría de los casos (Armbrust et al., 2015; ASF, 2026b).

### Transformaciones y acciones

| Transformaciones (perezosas) | Acciones (desencadenan la ejecución) |
|------------------------------|--------------------------------------|
| `map`, `filter`, `flatMap` | `collect`, `count`, `take` |
| `select`, `where`, `groupBy` | `show`, `first` |
| `join`, `union`, `distinct` | `write`, `save`, `foreach` |

**Evaluación perezosa** (*lazy evaluation*): las transformaciones únicamente construyen un plan de
ejecución en forma de grafo acíclico dirigido (DAG). El cómputo ocurre solo cuando se invoca una
acción, lo que permite a Spark optimizar el plan completo antes de ejecutarlo (Zaharia et al., 2012).

### Transformaciones estrechas y amplias

- **Estrechas** (*narrow*; por ejemplo, `map` y `filter`): cada partición de salida depende de una sola partición de entrada y no hay movimiento de datos entre nodos.
- **Amplias** (*wide*; por ejemplo, `groupBy`, `join` y `reduceByKey`): requieren un **shuffle**, es decir, un intercambio de datos entre nodos. Son más costosas y delimitan nuevas etapas (*stages*).

### Job, stage y task

- Cada **acción** genera un **job**.
- Un job se divide en **stages**, separadas por operaciones de *shuffle*.
- Cada stage contiene una **task** por partición.

Esta jerarquía puede observarse en la Spark UI, disponible en <http://localhost:4040> mientras la
sesión permanece activa.

### SparkSession

Desde la versión 2.0, la `SparkSession` es el punto de entrada único a la funcionalidad de Spark:

```python
from pyspark.sql import SparkSession

spark = (SparkSession.builder
         .appName("MiAplicacion")
         .master("local[*]")      # usa todos los núcleos locales
         .getOrCreate())
```

### Modos de despliegue

| Valor de `master` | Significado |
|-------------------|-------------|
| `local` | Un solo hilo |
| `local[4]` | Cuatro hilos |
| `local[*]` | Tantos hilos como núcleos disponibles |
| `spark://host:7077` | Clúster *Standalone* |
| `yarn` | Clúster Hadoop YARN |
| `k8s://https://...` | Kubernetes |

## Preguntas de repaso

1. ¿Qué diferencia existe entre una transformación y una acción? Proponga dos ejemplos de cada una.
2. ¿Por qué un `groupBy` resulta más costoso que un `filter`?
3. ¿Qué es el linaje de un RDD y qué función cumple?
4. ¿Por qué se recomienda el uso de DataFrames sobre RDD?
5. ¿Qué información presenta la pestaña *Stages* de la Spark UI?

## Referencias

Armbrust, M., Das, T., Torres, J., Yavuz, B., Zhu, S., Xin, R., Ghodsi, A., Stoica, I., & Zaharia, M. (2018). Structured streaming: A declarative API for real-time applications in Apache Spark. En *Proceedings of the 2018 International Conference on Management of Data* (pp. 601–613). ACM. https://doi.org/10.1145/3183713.3190664

Armbrust, M., Xin, R. S., Lian, C., Huai, Y., Liu, D., Bradley, J. K., Meng, X., Kaftan, T., Franklin, M. J., Ghodsi, A., & Zaharia, M. (2015). Spark SQL: Relational data processing in Spark. En *Proceedings of the 2015 ACM SIGMOD International Conference on Management of Data* (pp. 1383–1394). ACM. https://doi.org/10.1145/2723372.2742797

Dean, J., & Ghemawat, S. (2008). MapReduce: Simplified data processing on large clusters. *Communications of the ACM, 51*(1), 107–113. https://doi.org/10.1145/1327452.1327492

Laney, D. (2001). *3D data management: Controlling data volume, velocity, and variety* (Application Delivery Strategies, File 949). META Group.

Meng, X., Bradley, J., Yavuz, B., Sparks, E., Venkataraman, S., Liu, D., Freeman, J., Tsai, D. B., Amde, M., Owen, S., Xin, D., Xin, R., Franklin, M. J., Zadeh, R., Zaharia, M., & Talwalkar, A. (2016). MLlib: Machine learning in Apache Spark. *Journal of Machine Learning Research, 17*(34), 1–7. https://jmlr.org/papers/v17/15-237.html

The Apache Software Foundation. (2026a). *Spark overview* (Versión 4.3.0) [Documentación técnica]. https://spark.apache.org/docs/latest/

The Apache Software Foundation. (2026b). *Spark SQL, DataFrames and Datasets guide* (Versión 4.3.0) [Documentación técnica]. https://spark.apache.org/docs/latest/sql-programming-guide.html

The Apache Software Foundation. (2026d). *Spark standalone mode* (Versión 4.3.0) [Documentación técnica]. https://spark.apache.org/docs/latest/spark-standalone.html

Zaharia, M., Chowdhury, M., Das, T., Dave, A., Ma, J., McCauley, M., Franklin, M. J., Shenker, S., & Stoica, I. (2012). Resilient distributed datasets: A fault-tolerant abstraction for in-memory cluster computing. En *Proceedings of the 9th USENIX Symposium on Networked Systems Design and Implementation* (pp. 15–28). USENIX Association.

Zaharia, M., Xin, R. S., Wendell, P., Das, T., Armbrust, M., Dave, A., Meng, X., Rosen, J., Venkataraman, S., Franklin, M. J., Ghodsi, A., Gonzalez, J., Shenker, S., & Stoica, I. (2016). Apache Spark: A unified engine for big data processing. *Communications of the ACM, 59*(11), 56–65. https://doi.org/10.1145/2934664
