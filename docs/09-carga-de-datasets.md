# 9. Carga de un dataset propio

El taller está diseñado para que el estudiante analice cualquier conjunto de datos. El dataset de
ejemplo (`data/ejemplo/ventas_tienda.csv`) sirve como guía inicial; una vez recorridos los
cuadernos con él, basta con configurar otro archivo en el cuaderno 01.

## 9.1 Formatos admitidos

| Formato | Extensiones | Observaciones |
|---|---|---|
| Texto delimitado | `.csv`, `.tsv`, `.txt`, `.dat` | Se detectan el separador y la codificación |
| JSON | `.json`, `.jsonl`, `.ndjson` | Un objeto por línea o un arreglo `[...]` |
| Parquet / ORC | `.parquet`, `.orc` o carpeta | Formatos columnares; conservan los tipos |
| Excel | `.xlsx`, `.xls`, `.xlsm` | Se convierte internamente a Parquet; se elige la hoja con `hoja_excel` |

Para un taller en un equipo personal se recomiendan archivos de hasta unos cientos de MB. Spark
puede procesar volúmenes mayores, pero el tiempo de ejecución en modo local crece con el tamaño.

## 9.2 Dónde obtener datos

- Portal de Datos Abiertos de Colombia (Ministerio de Tecnologías de la Información y las
  Comunicaciones, s.f.): <https://www.datos.gov.co/>. Cada conjunto puede exportarse en CSV
  (*Exportar > CSV*).
- Portales institucionales, entidades estadísticas o repositorios académicos.
- Datos propios de un proyecto de clase o de trabajo, siempre que no contengan información
  personal sensible.

Debe registrarse la fuente del dataset en formato APA (American Psychological Association, 2020):

> Autor o entidad. (Año). *Título del conjunto de datos* (Versión) [Conjunto de datos]. Editorial o portal. URL

## 9.3 Ubicación del archivo

El archivo se copia en `data/mis_datos/`:

| Entorno | Procedimiento |
|---|---|
| JupyterLab | Abrir `data/mis_datos/` en el explorador y usar el botón *Upload*, o arrastrar el archivo |
| Explorador del sistema | Copiar el archivo en `taller-apache-spark/data/mis_datos/` |
| Docker | Copiar el archivo en `data/mis_datos/` del equipo; la carpeta está montada en los contenedores |
| Google Colab | Usar la celda de carga del cuaderno 00 (`files.upload()`) o montar Google Drive |

## 9.4 Configuración en el cuaderno 01

En la celda editable del cuaderno `01_configuracion_dataset.ipynb` se ajustan las claves del
diccionario `CONFIG`:

| Clave | Ejemplo | Cuándo modificarla |
|---|---|---|
| `nombre` | `"matriculas_2025"` | Siempre |
| `ruta` | `"data/mis_datos/matriculas.csv"` | Siempre |
| `separador` | `";"` | Si la detección automática falla |
| `codificacion` | `"ISO-8859-1"` | Si aparecen caracteres como `Ã©` |
| `decimal` | `","` | Si los números usan coma decimal (`1.234,56`) |
| `encabezado` | `False` | Si el archivo no tiene fila de títulos |
| `columna_fecha` | `"Fecha de Matrícula"` | Si existe una fecha principal |
| `formato_fecha` | `"dd/MM/yyyy"` | Si la fecha no se reconoce automáticamente |
| `columna_objetivo` | `"Valor Pagado"` | Para el modelo del cuaderno 06 |
| `columnas_excluir` | `["Documento"]` | Identificadores o columnas sin valor analítico |
| `max_categorias` | `100` | Si una variable categórica tiene más de 50 valores |

Los nombres de columna se escriben como aparecen en el archivo; el taller los normaliza
automáticamente (minúsculas, sin tildes, espacios ni símbolos): `Valor Pagado ($)` se convierte en
`valor_pagado`.

Después de ejecutar el cuaderno 01 y guardar la configuración, los cuadernos 02 a 07 utilizan el
nuevo dataset sin otros cambios.

## 9.5 Archivos exportados desde Excel en español

Los archivos CSV generados por Excel con configuración regional en español suelen tener:

- punto y coma (`;`) como separador,
- coma decimal y punto como separador de miles (`1.234.567,89`),
- codificación Windows-1252 / ISO-8859-1,
- fechas en formato `dd/mm/aaaa`.

El taller detecta estos casos de forma automática: cuando el separador es `;`, convierte las
columnas numéricas con coma decimal; si el archivo no es UTF-8, usa ISO-8859-1; y reconoce las
fechas `dd/mm/aaaa`. Si algún aspecto no se detecta, se especifica en la configuración.

## 9.6 Diagnóstico de problemas de carga

La función `diagnosticar_carga()` del cuaderno 01 revisa los problemas siguientes:

| Síntoma | Causa probable | Ajuste |
|---|---|---|
| Una sola columna con todo el texto | Separador incorrecto | `separador` |
| Columnas `_c0`, `_c1`, ... | Falta de encabezado | `encabezado` |
| Caracteres `Ã`, `â€` | Codificación incorrecta | `codificacion` |
| Número leído como texto | Coma decimal o valores como `N/A` | `decimal`; limpieza en el cuaderno 04 |
| La fecha queda como texto | Formato no reconocido | `formato_fecha` |
| Textos con saltos de línea cortados | Campos multilínea | `multilinea: True` |

## 9.7 Tamaño de archivos y GitHub

GitHub rechaza archivos de más de 100 MB y advierte a partir de 50 MB (GitHub, s.f.). Para
datasets grandes se recomienda no incluirlos en el repositorio: se documentan la fuente y el
procedimiento de descarga en `data/mis_datos/README.md`, o se usa Git LFS. La carpeta
`data/procesado/`, donde los cuadernos escriben resultados, está excluida mediante `.gitignore`.

## 9.8 Uso desde la terminal

El perfil y el ETL básico también pueden ejecutarse con `spark-submit` desde la raíz del repositorio:

```bash
spark-submit src/perfil_dataset.py --ruta data/mis_datos/archivo.csv
spark-submit src/etl_generico.py
```

## Referencias

American Psychological Association. (2020). *Publication manual of the American Psychological Association* (7.ª ed.). https://doi.org/10.1037/0000165-000

GitHub. (s.f.). *About large files on GitHub* [Documentación técnica]. Recuperado el 9 de noviembre de 2026, de https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github

Ministerio de Tecnologías de la Información y las Comunicaciones. (s.f.). *Portal de datos abiertos de Colombia* [Sitio web]. Recuperado el 9 de noviembre de 2026, de https://www.datos.gov.co/
