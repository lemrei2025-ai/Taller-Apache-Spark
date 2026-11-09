# Carpeta para el dataset propio

En esta carpeta se ubican los archivos de datos que el estudiante desea analizar.

Formatos admitidos: CSV, TSV, TXT delimitado, JSON, JSON Lines, Parquet, ORC y Excel (.xlsx, .xls).

Procedimiento:

1. Copiar el archivo en esta carpeta (o cargarlo con el botón *Upload* de JupyterLab).
2. Abrir `notebooks/01_configuracion_dataset.ipynb` y escribir la ruta, por ejemplo
   `data/mis_datos/mi_archivo.csv`.
3. Ejecutar el cuaderno completo para validar la carga y guardar la configuración.

La guía [docs/09-carga-de-datasets.md](../../docs/09-carga-de-datasets.md) describe cada opción.

GitHub rechaza archivos de más de 100 MB (GitHub, s.f.). Los archivos de mayor tamaño no deben
incluirse en el repositorio; en su lugar se documenta la fuente y la forma de descargarlos.
