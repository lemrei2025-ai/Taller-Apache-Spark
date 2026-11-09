# 7. Publicación del repositorio en GitHub

## Opción 1. Desde la terminal (recomendada)

1. Se crea un repositorio vacío en <https://github.com/new> con el nombre `taller-apache-spark`, sin README, sin `.gitignore` y sin licencia, puesto que estos archivos ya están incluidos.
2. En la carpeta del taller se ejecutan los siguientes comandos:

```bash
cd taller-apache-spark
git init
git add .
git commit -m "Taller guía: instalación y uso de Apache Spark"
git branch -M main
git remote add origin https://github.com/<usuario>/taller-apache-spark.git
git push -u origin main
```

GitHub solicita un token personal de acceso en lugar de la contraseña
(*Settings > Developer settings > Personal access tokens*). También es posible autenticarse con
GitHub CLI mediante `gh auth login`.

Con GitHub CLI, la creación y publicación pueden realizarse en un solo paso:

```bash
gh repo create taller-apache-spark --public --source=. --remote=origin --push
```

## Opción 2. Desde el navegador

1. Se crea el repositorio vacío en GitHub.
2. Se selecciona la opción *uploading an existing file*.
3. Se arrastra el contenido de la carpeta `taller-apache-spark` (no la carpeta en sí).
4. Se escribe un mensaje de confirmación y se pulsa *Commit changes*.

Los archivos cuyo nombre comienza por punto (como `.gitignore`) pueden no mostrarse en el
explorador de archivos. Para visualizarlos se activa *Ver > Elementos ocultos* en Windows o se
presiona `Cmd+Shift+.` en macOS.

## Actualización de un repositorio publicado con una versión anterior

Si el repositorio ya contiene una versión anterior del taller, deben **eliminarse los archivos
antiguos**, no solo agregarse los nuevos. Los cuadernos de la versión anterior
(`01_primeros_pasos_rdd.ipynb`, `02_dataframes.ipynb`, `03_spark_sql.ipynb`, `04_etl_parquet.ipynb`,
`05_mllib.ipynb`) usaban la ruta relativa `os.path.abspath("../data")`, que en Google Colab apunta a
`/data` y produce el error `Input path does not exist: file:/data/...`.

Desde la terminal, dentro de la copia local del repositorio:

```bash
git rm -r --quiet notebooks data src docs scripts ejercicios   # elimina la versión anterior
# copiar aquí el contenido de la nueva versión del taller
git add -A                                                     # registra archivos nuevos y eliminados
git commit -m "Actualización del taller: dataset configurable"
git push
```

Desde el navegador: en GitHub se abre cada cuaderno antiguo de la carpeta `notebooks/`, se elige
*Delete file* (menú de tres puntos) y luego se cargan los archivos nuevos con *Add file > Upload files*.

Después de actualizar, en Colab debe abrirse nuevamente el cuaderno desde GitHub
(*Archivo > Abrir cuaderno > GitHub*); una copia guardada antes en Google Drive conserva el código anterior.

## Ajustes posteriores

- Reemplazar `<usuario>` en `README.md` y en las guías por el nombre de usuario real. En Linux:
  ```bash
  grep -rl "<usuario>" . | xargs sed -i 's/<usuario>/NOMBRE_USUARIO/g'
  ```
- Activar *Settings > General > Template repository* para que los estudiantes generen su propia copia con un clic.
- Los cuadernos se visualizan directamente en GitHub y pueden abrirse en Colab mediante una URL con el formato
  `https://colab.research.google.com/github/<usuario>/taller-apache-spark/blob/main/notebooks/00_guia_uso_notebooks.ipynb`
