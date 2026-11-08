# 1. Instalación de Apache Spark en Windows 10/11

Existen dos alternativas de instalación. Para el taller se recomienda la opción A.

- **Opción A. PySpark mediante pip** (aproximadamente 10 minutos): suficiente para los cuadernos y para `spark-submit`.
- **Opción B. Distribución completa de Spark**: incluye además `spark-shell` (Scala) y los scripts de administración de clúster.
- **Alternativa**: utilizar WSL2 (Ubuntu sobre Windows) y seguir la [guía de Linux](02-instalacion-linux.md).

El script [`scripts/instalar_spark_windows.ps1`](../scripts/instalar_spark_windows.ps1) automatiza
los pasos 1 a 5 de la opción B.

---

## Paso 1. Instalación de Java (JDK 17 o 21)

Spark 4.x requiere Java 17 o 21 (The Apache Software Foundation [ASF], 2026a). Se sugiere la
distribución Eclipse Temurin (Eclipse Foundation, s.f.).

1. Se descarga Eclipse Temurin JDK 17 (LTS) desde <https://adoptium.net/>.
2. Durante la ejecución del instalador `.msi` se marcan las opciones *Set JAVA_HOME variable* y *Add to PATH*.
3. En una nueva terminal de PowerShell se verifica la instalación:

```powershell
java -version
echo $env:JAVA_HOME
```

La salida esperada contiene `openjdk version "17..."`.

Como alternativa, la instalación puede realizarse con winget:

```powershell
winget install EclipseAdoptium.Temurin.17.JDK
```

## Paso 2. Instalación de Python 3.10 o superior

1. Se descarga Python desde <https://www.python.org/downloads/> (se recomienda la versión 3.12).
2. En el instalador se marca la opción *Add python.exe to PATH*.
3. Se verifica la instalación:

```powershell
python --version
pip --version
```

---

## Opción A. PySpark mediante pip (recomendada)

```powershell
cd C:\Users\<usuario>\Documents
git clone https://github.com/<usuario>/taller-apache-spark.git
cd taller-apache-spark

python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Si PowerShell bloquea la activación del entorno virtual, se ejecuta
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

A continuación se realizan el paso 4 (winutils) y el paso 6 (verificación).

---

## Opción B. Distribución completa

### Paso 3. Descarga de Spark

1. En <https://spark.apache.org/downloads.html> (ASF, 2026f) se selecciona Spark 4.3.0, paquete *Pre-built for Apache Hadoop 3.4 and later*.
2. Se descarga el archivo `spark-4.3.0-bin-hadoop3.tgz`.
3. Se descomprime en `C:\spark` (con 7-Zip o con el comando `tar` de PowerShell):

```powershell
mkdir C:\spark
tar -xzf $HOME\Downloads\spark-4.3.0-bin-hadoop3.tgz -C C:\spark
```

La estructura resultante es `C:\spark\spark-4.3.0-bin-hadoop3\bin\...`.

Se deben evitar rutas con espacios, como `C:\Program Files`.

## Paso 4. Instalación de `winutils.exe`

Spark utiliza bibliotecas de Hadoop que, en Windows, requieren los archivos `winutils.exe` y `hadoop.dll`.

1. Se crea la carpeta `C:\hadoop\bin`.
2. Se descargan `winutils.exe` y `hadoop.dll` de una versión Hadoop 3.3.x o superior desde el repositorio comunitario <https://github.com/cdarlint/winutils> (carpeta `hadoop-3.3.x/bin`).
3. Ambos archivos se copian en `C:\hadoop\bin`.
4. El archivo `hadoop.dll` se copia también en `C:\Windows\System32`, lo que evita errores al escribir archivos.

## Paso 5. Variables de entorno

En **Configuración > Sistema > Acerca de > Configuración avanzada del sistema > Variables de entorno**
se crean las siguientes variables de usuario:

| Variable | Valor |
|----------|-------|
| `JAVA_HOME` | `C:\Program Files\Eclipse Adoptium\jdk-17...` |
| `HADOOP_HOME` | `C:\hadoop` |
| `SPARK_HOME` | `C:\spark\spark-4.3.0-bin-hadoop3` (solo opción B) |
| `PYSPARK_PYTHON` | `python` |

En la variable **Path** se agregan las rutas:

- `%JAVA_HOME%\bin`
- `%HADOOP_HOME%\bin`
- `%SPARK_HOME%\bin` (solo opción B)

El procedimiento equivalente desde PowerShell es:

```powershell
[Environment]::SetEnvironmentVariable("HADOOP_HOME", "C:\hadoop", "User")
[Environment]::SetEnvironmentVariable("SPARK_HOME", "C:\spark\spark-4.3.0-bin-hadoop3", "User")
[Environment]::SetEnvironmentVariable("PYSPARK_PYTHON", "python", "User")
$p = [Environment]::GetEnvironmentVariable("Path", "User")
[Environment]::SetEnvironmentVariable("Path", "$p;C:\hadoop\bin;C:\spark\spark-4.3.0-bin-hadoop3\bin", "User")
```

Para que los cambios surtan efecto, es necesario cerrar y abrir nuevamente la terminal.

## Paso 6. Verificación

```powershell
python scripts\verificar_instalacion.py
```

Con la opción B también pueden probarse los siguientes comandos:

```powershell
spark-submit --version
pyspark          # consola interactiva de Python
spark-shell      # consola interactiva de Scala
```

Ejemplo de uso dentro de `pyspark`:

```python
>>> spark.range(1, 1_000_001).selectExpr("sum(id)").show()
+------------+
|     sum(id)|
+------------+
|500000500000|
+------------+
>>> exit()
```

Mientras la consola permanece abierta, la Spark UI está disponible en <http://localhost:4040>.

## Problemas frecuentes en Windows

| Error | Solución |
|-------|----------|
| `'java' no se reconoce como un comando` | Revisar `JAVA_HOME` y `Path`; abrir una nueva terminal |
| `Did not find winutils.exe` / `HADOOP_HOME unset` | Repetir el paso 4 y definir `HADOOP_HOME` |
| `UnsatisfiedLinkError ... NativeIO$Windows.access0` al escribir | Copiar `hadoop.dll` en `C:\Windows\System32` |
| `Python worker failed to connect back` | Definir `PYSPARK_PYTHON=python` y revisar el cortafuegos o el antivirus |
| `Python was not found; run without arguments to install from the Microsoft Store` | Desactivar los alias de ejecución de aplicaciones de Python en Configuración |

Otros casos se describen en la guía de [solución de problemas](06-solucion-problemas.md).

## Referencias

Eclipse Foundation. (s.f.). *Eclipse Temurin* [Software]. Adoptium. Recuperado el 8 de noviembre de 2026, de https://adoptium.net/

The Apache Software Foundation. (2026a). *Spark overview* (Versión 4.3.0) [Documentación técnica]. https://spark.apache.org/docs/latest/

The Apache Software Foundation. (2026f). *Download Apache Spark* [Página web]. Recuperado el 8 de noviembre de 2026, de https://spark.apache.org/downloads.html
