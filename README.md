# Taller guía: instalación y uso de Apache Spark con un dataset propio

Curso de Big Data. Taller práctico. Versión de referencia: Apache Spark 4.3.0 (PySpark).

El taller conduce al estudiante desde la instalación de Spark hasta el análisis completo de un
conjunto de datos de su elección. Incluye un **dataset de ejemplo** que guía todos los cuadernos;
después, el estudiante configura **su propio dataset** (CSV, JSON, Parquet o Excel) y repite el
recorrido sin modificar el código, salvo las celdas marcadas como editables.

---

## Objetivos de aprendizaje

Al finalizar el taller, el estudiante estará en capacidad de:

1. Instalar y configurar Spark de forma manual en Windows, Linux o macOS, o utilizarlo mediante Docker o Google Colab.
2. Utilizar cuadernos de Jupyter para documentar y ejecutar un análisis reproducible (Kluyver et al., 2016).
3. Explicar la arquitectura de Spark y su modelo de evaluación perezosa (Zaharia et al., 2012, 2016).
4. Cargar, validar y perfilar un dataset arbitrario con PySpark.
5. Limpiar y transformar datos, y almacenarlos en formato Parquet.
6. Responder preguntas de análisis con DataFrames y Spark SQL (Armbrust et al., 2015).
7. Entrenar y evaluar modelos con MLlib (Meng et al., 2016).

## Requisitos previos

| Requisito | Versión recomendada | Observaciones |
|-----------|--------------------|---------------|
| Java (JDK) | 17 o 21 | Spark 4.x no admite Java 8 ni 11 (The Apache Software Foundation [ASF], 2026a); los scripts lo corrigen automáticamente |
| Python | 3.10 a 3.14 | Se recomienda un entorno virtual |
| Memoria RAM | 8 GB (mínimo 4 GB) | |
| Espacio en disco | 2 GB libres | |
| Git | Cualquier versión reciente | Para clonar el repositorio |

## Instalación

La instalación manual paso a paso se describe en las guías de la carpeta `docs/`. Como
alternativa, los scripts de preparación crean el entorno virtual, actualizan pip, instalan las
dependencias, validan Java (lo instalan o reinstalan cuando no hay un JDK 17/21 que funcione) y
configuran automáticamente `JAVA_HOME`, `HADOOP_HOME` y el `Path`:

```powershell
# Windows (PowerShell), desde la raíz del repositorio
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\preparar_entorno_windows.ps1
# Opciones: -ReinstalarJava (fuerza la reinstalación) | -Sistema (como administrador, corrige
# también las variables del sistema)
```

```bash
# Linux / macOS
bash scripts/preparar_entorno.sh
```

Procedimiento manual equivalente:

```bash
git clone https://github.com/<usuario>/taller-apache-spark.git
cd taller-apache-spark
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python scripts/verificar_instalacion.py
jupyter lab
```

Si el script de verificación finaliza con `[OK] Spark funciona correctamente`, el entorno está listo.

## Guías

| N.º | Guía | Contenido |
|-----|------|-----------|
| 0 | [Conceptos de Spark](docs/00-conceptos.md) | Arquitectura, RDD, DataFrame, transformaciones y acciones |
| 1 | [Instalación manual en Windows](docs/01-instalacion-windows.md) | Java, Python, Spark, winutils, variables de entorno |
| 2 | [Instalación manual en Linux](docs/02-instalacion-linux.md) | Ubuntu/Debian, WSL2, clúster *Standalone* local |
| 3 | [Instalación manual en macOS](docs/03-instalacion-macos.md) | Homebrew o descarga manual |
| 4 | [Instalación con Docker](docs/04-instalacion-docker.md) | Clúster con maestro, dos *workers* y JupyterLab |
| 5 | [Uso en Google Colab](docs/05-google-colab.md) | Sin instalación local |
| 6 | [Solución de problemas](docs/06-solucion-problemas.md) | Diagnóstico de errores frecuentes |
| 7 | [Publicación en GitHub](docs/07-subir-a-github.md) | Subida del repositorio |
| 8 | [Uso de los cuadernos](docs/08-uso-de-notebooks.md) | Jupyter, estructura de los cuadernos, celdas editables, Spark UI |
| 9 | [Carga de un dataset propio](docs/09-carga-de-datasets.md) | Formatos, configuración, archivos de Excel en español, diagnóstico |
| — | [Referencias](docs/referencias.md) | Fuentes en formato APA 7 |

## Cuadernos

| Cuaderno | Contenido |
|---|---|
| `00_guia_uso_notebooks` | Uso de Jupyter, atajos, kernel, errores, carga de archivos, prueba de Spark |
| `01_configuracion_dataset` | Selección del dataset, opciones de lectura, diagnóstico, roles de columnas |
| `02_fundamentos_spark_rdd` | SparkSession, RDD, particiones, evaluación perezosa, *shuffle*, cache, WordCount |
| `03_exploracion_dataframes` | Perfil de calidad, estadísticas, frecuencias, histogramas, correlación, series de tiempo |
| `04_limpieza_etl_parquet` | Duplicados, estandarización de textos, faltantes, inválidos, atípicos, *join*, Parquet |
| `05_spark_sql` | Vistas, agregaciones, `HAVING`, `CASE WHEN`, funciones de ventana, UDF |
| `06_mllib_modelos` | Regresión o clasificación automática, línea base, fuga de datos, K-Means |
| `07_proyecto_final` | Plantilla del informe final |

## Uso con un dataset propio

1. Recorrer los cuadernos 00 a 06 con el dataset de ejemplo.
2. Copiar el archivo propio en `data/mis_datos/`.
3. En `01_configuracion_dataset`, modificar la celda editable (ruta, fecha, variable objetivo,
   columnas a excluir), revisar el diagnóstico y guardar la configuración.
4. Volver a ejecutar los cuadernos 02 a 06; las celdas `# >>> CELDA EDITABLE` permiten afinar el análisis.
5. Elaborar el informe en `07_proyecto_final`.

## Estructura del repositorio

```
taller-apache-spark/
├── README.md
├── requirements.txt
├── docs/                         Guías de instalación manual, uso y referencias
├── scripts/
│   ├── taller_spark.py               Módulo de apoyo: carga genérica, perfil, configuración
│   ├── configurar_java.py            Validación, (re)instalación y variables de Java 17/21
│   ├── entorno_windows.ps1           Funciones de variables de entorno en Windows
│   ├── verificar_instalacion.py      Verificación del entorno
│   ├── preparar_entorno_windows.ps1  Preparación completa (Windows)
│   ├── preparar_entorno.sh           Preparación completa (Linux/macOS)
│   ├── instalar_spark_windows.ps1    Instalación de la distribución de Spark (Windows)
│   ├── instalar_spark_linux.sh       Instalación de la distribución de Spark (Linux/macOS)
│   └── generar_datos.py              Generación del dataset de ejemplo
├── docker/                       Dockerfile y docker-compose.yml
├── notebooks/                    Cuadernos 00 a 07
├── src/
│   ├── perfil_dataset.py             Perfil de cualquier dataset (spark-submit)
│   ├── etl_generico.py               ETL básico del dataset configurado (spark-submit)
│   ├── wordcount.py                  Conteo de palabras con RDD
│   └── streaming_wordcount.py        Structured Streaming
├── data/
│   ├── dataset_config.json           Configuración del dataset activo
│   ├── ejemplo/                      Dataset de ejemplo y texto para WordCount
│   └── mis_datos/                    Ubicación de los datasets del estudiante
└── ejercicios/
    ├── README.md                     Enunciados y rúbrica
    └── soluciones/soluciones.py      Soluciones genéricas de referencia
```

## Agenda sugerida (6 horas en dos sesiones)

| Sesión | Bloque | Duración | Contenido | Material |
|---|---|---|---|---|
| 1 | 1 | 30 min | Conceptos de Spark | `docs/00` |
| 1 | 2 | 60 min | Instalación manual y verificación | `docs/01` a `docs/05` |
| 1 | 3 | 30 min | Uso de los cuadernos | `notebooks/00`, `docs/08` |
| 1 | 4 | 25 min | Configuración del dataset de ejemplo | `notebooks/01` |
| 1 | 5 | 35 min | Fundamentos: RDD y evaluación perezosa | `notebooks/02` |
| 2 | 6 | 40 min | Análisis exploratorio | `notebooks/03` |
| 2 | 7 | 45 min | Limpieza y Parquet | `notebooks/04` |
| 2 | 8 | 35 min | Spark SQL | `notebooks/05` |
| 2 | 9 | 45 min | MLlib | `notebooks/06` |
| 2 | 10 | 15 min | Presentación del proyecto con dataset propio | `notebooks/07`, `docs/09` |

## Entrega

1. Realizar un *fork* del repositorio.
2. Agregar el dataset propio en `data/mis_datos/` (o documentar su fuente si supera 50 MB).
3. Completar `notebooks/07_proyecto_final.ipynb` y las evidencias en `ejercicios/evidencias/`.
4. Publicar los cambios y compartir el enlace con el docente.

## Referencias

Armbrust, M., Xin, R. S., Lian, C., Huai, Y., Liu, D., Bradley, J. K., Meng, X., Kaftan, T., Franklin, M. J., Ghodsi, A., & Zaharia, M. (2015). Spark SQL: Relational data processing in Spark. En *Proceedings of the 2015 ACM SIGMOD International Conference on Management of Data* (pp. 1383–1394). ACM. https://doi.org/10.1145/2723372.2742797

Kluyver, T., Ragan-Kelley, B., Pérez, F., Granger, B., Bussonnier, M., Frederic, J., Kelley, K., Hamrick, J., Grout, J., Corlay, S., Ivanov, P., Avila, D., Abdalla, S., Willing, C., & Jupyter Development Team. (2016). Jupyter Notebooks: A publishing format for reproducible computational workflows. En F. Loizides & B. Schmidt (Eds.), *Positioning and power in academic publishing: Players, agents and agendas* (pp. 87–90). IOS Press. https://doi.org/10.3233/978-1-61499-649-1-87

Meng, X., Bradley, J., Yavuz, B., Sparks, E., Venkataraman, S., Liu, D., Freeman, J., Tsai, D. B., Amde, M., Owen, S., Xin, D., Xin, R., Franklin, M. J., Zadeh, R., Zaharia, M., & Talwalkar, A. (2016). MLlib: Machine learning in Apache Spark. *Journal of Machine Learning Research, 17*(34), 1–7. https://jmlr.org/papers/v17/15-237.html

The Apache Software Foundation. (2026a). *Spark overview* (Versión 4.3.0) [Documentación técnica]. https://spark.apache.org/docs/latest/

Zaharia, M., Chowdhury, M., Das, T., Dave, A., Ma, J., McCauley, M., Franklin, M. J., Shenker, S., & Stoica, I. (2012). Resilient distributed datasets: A fault-tolerant abstraction for in-memory cluster computing. En *Proceedings of the 9th USENIX Symposium on Networked Systems Design and Implementation* (pp. 15–28). USENIX Association.

Zaharia, M., Xin, R. S., Wendell, P., Das, T., Armbrust, M., Dave, A., Meng, X., Rosen, J., Venkataraman, S., Franklin, M. J., Ghodsi, A., Gonzalez, J., Shenker, S., & Stoica, I. (2016). Apache Spark: A unified engine for big data processing. *Communications of the ACM, 59*(11), 56–65. https://doi.org/10.1145/2934664

La lista completa de fuentes se encuentra en [docs/referencias.md](docs/referencias.md).

## Licencia

Material educativo distribuido bajo la licencia [MIT](LICENSE). Puede reutilizarse y adaptarse citando la fuente.
