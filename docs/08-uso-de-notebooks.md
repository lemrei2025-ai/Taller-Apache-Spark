# 8. Uso de los cuadernos (notebooks) del taller

Esta guía explica cómo abrir, ejecutar y adaptar los cuadernos del taller. El cuaderno
`notebooks/00_guia_uso_notebooks.ipynb` contiene la misma información con ejercicios prácticos.

## 8.1 Qué es un cuaderno de Jupyter

Un cuaderno de Jupyter es un documento (`.ipynb`) que combina texto explicativo, código ejecutable
y los resultados de ese código. Kluyver et al. (2016) lo describen como un formato de publicación
para flujos de trabajo computacionales reproducibles: el lector puede seguir el razonamiento y
volver a ejecutar cada paso.

| Componente | Función |
|---|---|
| Celda de código | Instrucciones de Python; su resultado aparece debajo |
| Celda Markdown | Texto con formato: títulos, listas, tablas, enlaces |
| Kernel | Proceso de Python que ejecuta el código y conserva las variables |
| Contador `[n]` | Orden en que se ejecutó cada celda |

## 8.2 Apertura de los cuadernos

| Entorno | Procedimiento |
|---|---|
| Local (Windows, Linux, macOS) | Activar el entorno virtual y ejecutar `jupyter lab` desde la raíz del repositorio. En el explorador de la izquierda, abrir `notebooks/`. |
| Docker | Abrir <http://localhost:8888> (token `bigdata`) y entrar a `notebooks/`. |
| Google Colab | *Archivo > Abrir cuaderno > GitHub*, pegar la URL del repositorio y elegir el cuaderno. En la celda de preparación, reemplazar `<usuario>` en `REPO_URL` (véase la sección 8.6). |
| Visual Studio Code | Abrir la carpeta del repositorio, abrir el `.ipynb` y seleccionar como *kernel* el intérprete de `.venv`. |

## 8.3 Ejecución y atajos de teclado

Las celdas se ejecutan en orden, de arriba hacia abajo, con `Shift + Enter`. JupyterLab tiene un
**modo edición** (se escribe dentro de la celda) y un **modo comando** (se activa con `Esc` y
permite manipular celdas completas) (Project Jupyter, s.f.).

| Acción | Atajo | Modo |
|---|---|---|
| Ejecutar y pasar a la siguiente | `Shift + Enter` | ambos |
| Ejecutar y permanecer en la celda | `Ctrl + Enter` | ambos |
| Ejecutar e insertar una celda debajo | `Alt + Enter` | ambos |
| Modo edición / modo comando | `Enter` / `Esc` | — |
| Insertar celda arriba / abajo | `A` / `B` | comando |
| Eliminar celda / deshacer eliminación | `D`, `D` / `Z` | comando |
| Convertir en Markdown / en código | `M` / `Y` | comando |
| Autocompletar / ver documentación | `Tab` / `Shift + Tab` | edición |
| Guardar | `Ctrl + S` | ambos |

## 8.4 Estado del kernel y orden de ejecución

El kernel conserva en memoria todas las variables creadas. Una variable está disponible en
cualquier celda que se ejecute **después** de la celda que la creó. Por eso:

- Los cuadernos deben ejecutarse en orden.
- Si aparece `NameError: name '...' is not defined`, falta ejecutar una celda anterior.
- Cuando el estado se vuelve confuso, se usa *Kernel > Restart Kernel and Run All Cells*.
- Una celda que tarda demasiado se detiene con *Kernel > Interrupt Kernel* (botón ■).
- Al reiniciar el kernel se cierra la sesión de Spark; la celda de preparación la vuelve a crear.

## 8.5 Estructura común de los cuadernos

Todos los cuadernos (excepto el 00) siguen la misma estructura:

1. **Encabezado**: objetivos, duración, requisito previo, entrada y salida.
2. **Cómo utilizar este cuaderno**: instrucciones breves.
3. **Preparación del entorno**: ubica la carpeta del taller, importa el módulo de apoyo y crea la `SparkSession`.
4. **Carga del dataset activo**: lee la configuración guardada y clasifica las columnas por rol.
5. **Secciones temáticas**, cada una con fundamento, código, interpretación y adaptación.
6. **Ejercicios propuestos** y **referencias**.

### Celdas editables

Las celdas que comienzan con `# >>> CELDA EDITABLE` son las únicas que deben modificarse para
adaptar el análisis a otro dataset. El resto del código usa las listas de columnas detectadas
automáticamente:

| Variable | Contenido |
|---|---|
| `df` | DataFrame del dataset activo |
| `cfg` | Configuración del dataset (diccionario) |
| `NUM`, `CAT`, `FEC`, `TXT` | Columnas numéricas, categóricas, de fecha y de texto |
| `objetivo` | Variable objetivo definida en la configuración |

## 8.6 La celda de preparación

La primera celda de código de cada cuaderno:

1. **Ubica la carpeta del taller** con `ubicar_taller()`, que busca `scripts/taller_spark.py`
   desde la carpeta actual hacia arriba. Así el cuaderno funciona aunque se abra desde otra
   ubicación, y se evitan errores como `Input path does not exist: file:/data/...`.
2. **En Google Colab**, busca el taller en `/content` y en Google Drive; si no está, lo clona con
   `git clone` desde la dirección de `REPO_URL` (por eso, en Colab, debe reemplazarse `<usuario>`
   por el usuario de GitHub donde está publicado el taller) e instala las dependencias que falten.
3. Fija `notebooks/` como carpeta de trabajo y agrega `scripts/` a la ruta de Python.
4. Crea la `SparkSession` con `iniciar_spark()`, que además verifica Java 17/21 y se conecta al
   clúster de Docker cuando corresponde.

## 8.7 Secuencia de trabajo

```
00 guía de uso ─► 01 configuración del dataset ─► 02 fundamentos ─► 03 exploración
                                                                         │
            07 proyecto final ◄── 06 MLlib ◄── 05 Spark SQL ◄── 04 limpieza (Parquet)
```

| Cuaderno | Contenido | Salida |
|---|---|---|
| `00_guia_uso_notebooks` | Uso de Jupyter, carga de archivos, prueba de Spark | — |
| `01_configuracion_dataset` | Selección, carga, diagnóstico y roles de columnas | `data/dataset_config.json` |
| `02_fundamentos_spark_rdd` | SparkSession, RDD, particiones, evaluación perezosa, *shuffle*, cache, WordCount | — |
| `03_exploracion_dataframes` | Perfil, estadísticas, frecuencias, histogramas, correlación, series de tiempo | Hallazgos |
| `04_limpieza_etl_parquet` | Duplicados, textos, faltantes, inválidos, atípicos, fechas, *join*, Parquet | `data/procesado/<nombre>_limpio/` |
| `05_spark_sql` | Vistas, agregaciones, `HAVING`, `CASE WHEN`, funciones de ventana, UDF | Respuestas a preguntas |
| `06_mllib_modelos` | Pipeline de regresión o clasificación, línea base, importancia, K-Means | `data/procesado/modelos/` |
| `07_proyecto_final` | Plantilla del informe | Informe del estudiante |

Se recomienda recorrer primero todos los cuadernos con el dataset de ejemplo y, después,
configurar un dataset propio en el cuaderno 01 y repetir los cuadernos 02 a 07.

## 8.8 Spark UI

Mientras una `SparkSession` está activa, la interfaz web de Spark (normalmente
<http://localhost:4040>; la dirección exacta aparece al crear la sesión) muestra:

| Pestaña | Información |
|---|---|
| Jobs | Trabajos generados por cada acción y su duración |
| Stages | Etapas de cada trabajo, separadas por *shuffle*, y sus tareas |
| Storage | DataFrames o RDD almacenados en cache |
| SQL / DataFrame | Plan de ejecución de las consultas |
| Executors | Memoria y tareas de cada *executor* |

## 8.9 Buenas prácticas

1. Guardar con frecuencia (`Ctrl + S`).
2. No modificar los cuadernos originales para la entrega: duplicarlos o trabajar en `07_proyecto_final`.
3. Limpiar las salidas antes de subir a GitHub (*Edit > Clear Outputs of All Cells*).
4. No usar `collect()` ni `toPandas()` sobre datos grandes; para observar datos se usan `show()`, `limit()` o `take()`.
5. Cerrar la sesión con `spark.stop()` al terminar.

## 8.10 Errores frecuentes en los cuadernos

| Mensaje | Causa | Solución |
|---|---|---|
| `NameError: name 'df' is not defined` | No se ejecutó la celda de carga | Ejecutar las celdas en orden |
| `FileNotFoundError: No se encontró la carpeta del taller` | El cuaderno se abrió fuera del repositorio | Abrirlo desde `notebooks/`; en Colab, completar `REPO_URL` |
| `Input path does not exist: file:/data/...` | Versión anterior de los cuadernos, con `DATA = os.path.abspath("../data")` | Actualizar el repositorio en GitHub eliminando los cuadernos antiguos (guía 07) y abrir de nuevo el cuaderno |
| `RuntimeError: En Google Colab debe escribirse en REPO_URL...` | Falta la dirección del repositorio | Reemplazar `<usuario>` en `REPO_URL` de la celda de preparación |
| `[UNRESOLVED_COLUMN]` | Nombre de columna inexistente | Revisar `df.columns`: los nombres están normalizados |
| `Java gateway process exited` | Java no compatible | `python scripts/configurar_java.py --instalar` |
| `OutOfMemoryError` | Dataset muy grande para la memoria del *driver* | `iniciar_spark("app", memoria_driver="4g")` |

## Referencias

Kluyver, T., Ragan-Kelley, B., Pérez, F., Granger, B., Bussonnier, M., Frederic, J., Kelley, K., Hamrick, J., Grout, J., Corlay, S., Ivanov, P., Avila, D., Abdalla, S., Willing, C., & Jupyter Development Team. (2016). Jupyter Notebooks: A publishing format for reproducible computational workflows. En F. Loizides & B. Schmidt (Eds.), *Positioning and power in academic publishing: Players, agents and agendas* (pp. 87–90). IOS Press. https://doi.org/10.3233/978-1-61499-649-1-87

Project Jupyter. (s.f.). *JupyterLab documentation* [Documentación técnica]. Recuperado el 9 de noviembre de 2026, de https://jupyterlab.readthedocs.io/
