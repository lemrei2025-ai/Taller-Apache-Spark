# Taller guía: instalación y uso de Apache Spark

Curso de Big Data. Taller práctico. Versión de referencia: Apache Spark 4.3.0 (PySpark).

Este repositorio reúne el material del taller: guías de instalación para Windows, Linux, macOS,
Docker y Google Colab; cuadernos (*notebooks*) guiados; programas de ejemplo; conjuntos de datos
de práctica y ejercicios con soluciones de referencia.

---

## Objetivos de aprendizaje

Al finalizar el taller, el estudiante estará en capacidad de:

1. Explicar la arquitectura de Apache Spark (*driver*, *executors* y gestor de clúster) y su modelo de evaluación perezosa (Zaharia et al., 2016).
2. Instalar y configurar Spark en un equipo local o utilizarlo mediante Docker o Google Colab.
3. Manipular datos mediante RDD, DataFrames y Spark SQL (Armbrust et al., 2015; Zaharia et al., 2012).
4. Construir un flujo ETL que lea archivos CSV y escriba en formato Parquet.
5. Entrenar un modelo básico con MLlib (Meng et al., 2016).
6. Ejecutar trabajos con `spark-submit` y monitorearlos en la interfaz web de Spark (Spark UI).

## Requisitos previos

| Requisito | Versión recomendada | Observaciones |
|-----------|--------------------|---------------|
| Java (JDK) | 17 o 21 | Spark 4.x no admite Java 8 ni 11 (The Apache Software Foundation [ASF], 2026a) |
| Python | 3.10 a 3.13 | Se recomienda un entorno virtual |
| Memoria RAM | 8 GB (mínimo 4 GB) | |
| Espacio en disco | 2 GB libres | |
| Git | Cualquier versión reciente | Para clonar el repositorio |

Cuando el estudiante no cuenta con permisos de administrador o el tiempo es limitado, se recomienda
la opción con Docker o con Google Colab.

## Inicio rápido

```bash
git clone https://github.com/<usuario>/taller-apache-spark.git
cd taller-apache-spark

python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows (PowerShell)
# .venv\Scripts\Activate.ps1

pip install -r requirements.txt
python scripts/verificar_instalacion.py
jupyter lab
```

Si el script de verificación finaliza con el mensaje `[OK] Spark funciona correctamente`, el
entorno queda listo para trabajar con los cuadernos.

## Guías de instalación y uso

| N.º | Guía | Público |
|-----|------|---------|
| 0 | [Conceptos de Spark](docs/00-conceptos.md) | Todos (lectura previa) |
| 1 | [Instalación en Windows](docs/01-instalacion-windows.md) | Windows 10/11 |
| 2 | [Instalación en Linux (Ubuntu/Debian)](docs/02-instalacion-linux.md) | Linux |
| 3 | [Instalación en macOS](docs/03-instalacion-macos.md) | Mac Intel o Apple Silicon |
| 4 | [Instalación con Docker (clúster local)](docs/04-instalacion-docker.md) | Cualquier sistema con Docker |
| 5 | [Uso en Google Colab](docs/05-google-colab.md) | Sin instalación local |
| 6 | [Solución de problemas](docs/06-solucion-problemas.md) | Diagnóstico de errores |
| 7 | [Publicación del repositorio en GitHub](docs/07-subir-a-github.md) | Docente y estudiantes |
| — | [Referencias bibliográficas](docs/referencias.md) | Todos |

## Estructura del repositorio

```
taller-apache-spark/
├── README.md                  Descripción general del taller
├── requirements.txt           Dependencias de Python
├── docs/                      Guías de instalación, teoría y referencias
├── scripts/
│   ├── instalar_spark_linux.sh       Instalación automática (Linux/macOS)
│   ├── instalar_spark_windows.ps1    Instalación automática (Windows)
│   ├── verificar_instalacion.py      Verificación del entorno
│   └── generar_datos.py              Generación de los datos de práctica
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml     Maestro, dos workers y JupyterLab
├── notebooks/
│   ├── 01_primeros_pasos_rdd.ipynb
│   ├── 02_dataframes.ipynb
│   ├── 03_spark_sql.ipynb
│   ├── 04_etl_parquet.ipynb
│   └── 05_mllib.ipynb
├── src/                       Programas para spark-submit
│   ├── wordcount.py
│   ├── etl_ventas.py
│   └── streaming_wordcount.py
├── data/                      Conjuntos de datos sintéticos
│   ├── ventas.csv
│   ├── clientes.csv
│   ├── productos.json
│   └── texto_bigdata.txt
└── ejercicios/
    ├── README.md              Enunciados y rúbrica
    └── soluciones/soluciones.py
```

## Agenda sugerida (4 horas)

| Bloque | Duración | Contenido | Material |
|--------|----------|-----------|----------|
| 1 | 30 min | Qué es Spark: arquitectura y conceptos | `docs/00-conceptos.md` |
| 2 | 45 min | Instalación y verificación | `docs/01` a `docs/05`, `scripts/` |
| 3 | 30 min | RDD, transformaciones y acciones | `notebooks/01` |
| 4 | 45 min | DataFrames y Spark SQL | `notebooks/02`, `notebooks/03` |
| — | 15 min | Receso | |
| 5 | 30 min | ETL de CSV a Parquet, `spark-submit` y Spark UI | `notebooks/04`, `src/` |
| 6 | 30 min | Aprendizaje automático con MLlib | `notebooks/05` |
| 7 | 15 min | Ejercicios y entrega | `ejercicios/` |

## Entrega del taller

1. El estudiante realiza un *fork* de este repositorio.
2. Resuelve los ejercicios de `ejercicios/` en el cuaderno `ejercicios/mi_solucion.ipynb`.
3. Incluye las capturas de la Spark UI en `ejercicios/evidencias/`.
4. Publica los cambios y comparte el enlace del *fork* con el docente.

## Referencias

Armbrust, M., Xin, R. S., Lian, C., Huai, Y., Liu, D., Bradley, J. K., Meng, X., Kaftan, T., Franklin, M. J., Ghodsi, A., & Zaharia, M. (2015). Spark SQL: Relational data processing in Spark. En *Proceedings of the 2015 ACM SIGMOD International Conference on Management of Data* (pp. 1383–1394). ACM. https://doi.org/10.1145/2723372.2742797

Meng, X., Bradley, J., Yavuz, B., Sparks, E., Venkataraman, S., Liu, D., Freeman, J., Tsai, D. B., Amde, M., Owen, S., Xin, D., Xin, R., Franklin, M. J., Zadeh, R., Zaharia, M., & Talwalkar, A. (2016). MLlib: Machine learning in Apache Spark. *Journal of Machine Learning Research, 17*(34), 1–7. https://jmlr.org/papers/v17/15-237.html

The Apache Software Foundation. (2026a). *Spark overview* (Versión 4.3.0) [Documentación técnica]. https://spark.apache.org/docs/latest/

Zaharia, M., Chowdhury, M., Das, T., Dave, A., Ma, J., McCauley, M., Franklin, M. J., Shenker, S., & Stoica, I. (2012). Resilient distributed datasets: A fault-tolerant abstraction for in-memory cluster computing. En *Proceedings of the 9th USENIX Symposium on Networked Systems Design and Implementation* (pp. 15–28). USENIX Association.

Zaharia, M., Xin, R. S., Wendell, P., Das, T., Armbrust, M., Dave, A., Meng, X., Rosen, J., Venkataraman, S., Franklin, M. J., Ghodsi, A., Gonzalez, J., Shenker, S., & Stoica, I. (2016). Apache Spark: A unified engine for big data processing. *Communications of the ACM, 59*(11), 56–65. https://doi.org/10.1145/2934664

La lista completa de fuentes se encuentra en [docs/referencias.md](docs/referencias.md).

## Licencia

Material educativo distribuido bajo la licencia [MIT](LICENSE). Puede reutilizarse y adaptarse citando la fuente.
