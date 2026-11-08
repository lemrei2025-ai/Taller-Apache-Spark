# 6. Solución de problemas

Antes de solicitar asistencia, se recomienda ejecutar el script de verificación y adjuntar su salida
completa a la consulta:

```bash
python scripts/verificar_instalacion.py
```

## Java

| Síntoma | Causa | Solución |
|---------|-------|----------|
| `JAVA_HOME is not set` / `java: command not found` | Java no está instalado o no se encuentra en el PATH | Instalar JDK 17 o 21 y configurar `JAVA_HOME` |
| `UnsupportedClassVersionError` / `Unsupported class file major version` | Versión de Java anterior a la requerida | Spark 4.x requiere Java 17 o 21 (The Apache Software Foundation [ASF], 2026a) |
| `IllegalAccessError ... module java.base does not export` | Versión de Java no soportada | Utilizar JDK 17 o 21 |

## Python y PySpark

| Síntoma | Solución |
|---------|----------|
| `ModuleNotFoundError: No module named 'pyspark'` | Activar el entorno virtual: `source .venv/bin/activate` o `.venv\Scripts\Activate.ps1` |
| `Python in worker has different version than that in driver` | Definir `PYSPARK_PYTHON` y `PYSPARK_DRIVER_PYTHON` con el mismo intérprete |
| `Python worker failed to connect back` (Windows) | Definir `PYSPARK_PYTHON=python` y revisar el cortafuegos o el antivirus |
| La versión de `pyspark` no coincide con la de `SPARK_HOME` | Igualar ambas versiones o eliminar `SPARK_HOME` para usar la copia instalada con pip |

## Windows

| Síntoma | Solución |
|---------|----------|
| `Could not locate executable null\bin\winutils.exe` | Configurar `HADOOP_HOME` y copiar `winutils.exe` (guía de Windows, paso 4) |
| `NativeIO$Windows.access0` al ejecutar `.write` | Copiar `hadoop.dll` en `C:\Windows\System32` |
| Fallos en rutas con espacios | Instalar en `C:\spark` y `C:\hadoop` |

## Memoria y rendimiento

| Síntoma | Solución |
|---------|----------|
| `java.lang.OutOfMemoryError: Java heap space` | Aumentar la memoria del *driver*: `.config("spark.driver.memory", "4g")` |
| Lentitud con conjuntos de datos pequeños | Reducir las particiones de *shuffle*: `.config("spark.sql.shuffle.partitions", "8")` |
| `collect()` no responde | No trasladar millones de filas al *driver*; utilizar `show()`, `take()` o `limit()` |

Las propiedades de configuración disponibles se describen en la documentación oficial (ASF, 2026a).

## Red y puertos

| Síntoma | Solución |
|---------|----------|
| `Service 'sparkDriver' could not bind on a random free port` | `export SPARK_LOCAL_IP=127.0.0.1` (Windows: `set SPARK_LOCAL_IP=127.0.0.1`) |
| No se abre `localhost:4040` | La Spark UI existe solo mientras la `SparkSession` está activa |

## Reducción de mensajes de registro

```python
spark.sparkContext.setLogLevel("WARN")
```

De forma permanente, se copia `$SPARK_HOME/conf/log4j2.properties.template` como
`log4j2.properties` y se cambia el valor `rootLogger.level = warn`.

## Referencias

The Apache Software Foundation. (2026a). *Spark overview* (Versión 4.3.0) [Documentación técnica]. https://spark.apache.org/docs/latest/
