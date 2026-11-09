# 1. Instalación de Apache Spark en Windows 10/11

Existen dos alternativas de instalación. Para el taller se recomienda la opción A.

- **Opción A. PySpark mediante pip** (aproximadamente 10 minutos): suficiente para los cuadernos y para `spark-submit`.
- **Opción B. Distribución completa de Spark**: incluye además `spark-shell` (Scala) y los scripts de administración de clúster.
- **Alternativa**: utilizar WSL2 (Ubuntu sobre Windows) y seguir la [guía de Linux](02-instalacion-linux.md).

## Instalación automática (recomendada)

Los scripts del taller validan Java, lo reinstalan si es necesario y configuran todas las
variables de entorno sin intervención manual. Se ejecutan desde la carpeta raíz del taller en
PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\preparar_entorno_windows.ps1          # opción A: entorno del taller con PySpark
.\scripts\instalar_spark_windows.ps1            # opción B: distribución completa de Spark
```

| Paso | `preparar_entorno_windows.ps1` | `instalar_spark_windows.ps1` |
|---|---|---|
| Python 3.10+ (con winget si falta) | Sí | Sí |
| Entorno virtual, pip actualizado y dependencias | Sí | No |
| Validación, instalación o reinstalación de Java 17 | Sí | Sí |
| `JAVA_HOME` y `Path` del usuario | Sí | Sí |
| winutils, `HADOOP_HOME` y `Path` | Sí | Sí |
| Descarga de Spark, `SPARK_HOME`, `PYSPARK_PYTHON` | No | Sí |
| Verificación final | Sí | Sí |

Opciones disponibles en ambos scripts:

| Opción | Efecto |
|---|---|
| `-ReinstalarJava` | Reinstala Eclipse Temurin 17 aunque exista una versión válida |
| `-Sistema` | Con PowerShell abierto como administrador, corrige también `JAVA_HOME` y `Path` del sistema |

Al terminar, la terminal actual ya tiene las variables actualizadas, y las terminales nuevas
también las reciben. Los pasos manuales de esta guía describen lo mismo que hacen los scripts y
sirven para comprender el proceso o para resolverlo sin ellos.

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

### Validación y corrección automática de Java

Es habitual que el equipo conserve una instalación de Java 8 y que `JAVA_HOME` apunte a ella, por
ejemplo `C:\PROGRA~1\ECLIPS~1\JDK-80~1.1-H`. En ese caso Spark 4.x no funciona, aunque también
exista un JDK 17. El script `scripts\configurar_java.py` (que usan los scripts de PowerShell, el
script de verificación y los cuadernos) resuelve la situación en cinco pasos:

1. **Busca** todos los JDK instalados: `JAVA_HOME` del usuario y del sistema, `Path`,
   `C:\Program Files\*`, la carpeta de programas del usuario y `%USERPROFILE%\.jdks`.
2. **Valida** cada JDK ejecutando `java -version`. Una instalación dañada o incompleta (por
   ejemplo, una carpeta de Java 17 a la que le faltan archivos) se descarta.
3. **Instala o reinstala** Eclipse Temurin 17 si no hay uno válido: primero con `winget`
   (`--force` al reinstalar); si `winget` no existe o falla, descarga el ZIP oficial de Adoptium y lo
   instala en `%LOCALAPPDATA%\Programs\Eclipse Adoptium`, sin requerir permisos de administrador.
4. **Configura las variables del usuario** directamente en el registro (`HKCU\Environment`):
   `JAVA_HOME` apunta al JDK elegido; en el `Path` se agrega `%JAVA_HOME%\bin` al inicio y se
   retiran las rutas de versiones de Java no compatibles. El `Path` se guarda como valor expandible,
   de modo que `%JAVA_HOME%\bin` siempre sigue a `JAVA_HOME`. Luego se notifica a Windows el cambio.
5. **Revisa las variables del sistema.** Si el `Path` del sistema contiene Java 8 (por ejemplo,
   `C:\Program Files\Common Files\Oracle\Java\javapath`), Windows lo consulta antes que el `Path`
   del usuario y `java -version` puede seguir mostrando la versión antigua. Spark no se ve
   afectado, porque utiliza `JAVA_HOME`; aun así, con PowerShell como administrador, la opción
   `--sistema` corrige también `JAVA_HOME` y `Path` del sistema.

```powershell
python scripts\configurar_java.py --diagnostico  # estado actual: variables, Path y JDK válidos o dañados
python scripts\configurar_java.py                # valida, corrige y guarda las variables
python scripts\configurar_java.py --instalar     # además, instala Temurin 17 si no hay uno válido
python scripts\configurar_java.py --reinstalar   # reinstala Temurin 17 aunque exista
python scripts\configurar_java.py --sistema      # (administrador) corrige también las variables del sistema
```

Después de la corrección, las terminales nuevas usan la configuración actualizada. Para la terminal
actual, el script muestra el comando que debe copiarse. Los cuadernos del taller aplican la misma
corrección al iniciar, por lo que funcionan aunque Jupyter se haya abierto con el valor anterior.
No es necesario desinstalar Java 8.

#### Verificación manual de las variables

```powershell
# Valores guardados de forma permanente (usuario y sistema)
[Environment]::GetEnvironmentVariable("JAVA_HOME", "User")
[Environment]::GetEnvironmentVariable("JAVA_HOME", "Machine")
# Ejecutable que encuentra la terminal y su versión
(Get-Command java).Source
& "$env:JAVA_HOME\bin\java.exe" -version
```

## Paso 2. Instalación de Python 3.10 o superior

1. Se descarga Python desde <https://www.python.org/downloads/> (versiones 3.10 a 3.14; se recomienda 3.12 o 3.13).
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
python -m pip install --upgrade pip
pip install -r requirements.txt
python scripts\configurar_java.py
```

El comando `python -m pip install --upgrade pip` elimina el aviso
*A new release of pip is available*; dicho aviso es informativo y no impide la instalación.

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

El procedimiento equivalente desde PowerShell se encuentra en `scripts\entorno_windows.ps1`
(funciones `Set-UserEnv` y `Add-UserPathEntry`). Se recomienda **no** modificar el `Path` con
`[Environment]::SetEnvironmentVariable("Path", ...)`: ese método guarda el `Path` como texto fijo, con lo
que entradas como `%JAVA_HOME%\bin` dejan de actualizarse. La forma segura es:

```powershell
. .\scripts\entorno_windows.ps1
Set-UserEnv "JAVA_HOME" "C:\Program Files\Eclipse Adoptium\jdk-17.0.12.7-hotspot"
Set-UserEnv "HADOOP_HOME" "C:\hadoop"
Set-UserEnv "SPARK_HOME" "C:\spark\spark-4.3.0-bin-hadoop3"
Add-UserPathEntry "%JAVA_HOME%\bin"
Add-UserPathEntry "%HADOOP_HOME%\bin"
Add-UserPathEntry "%SPARK_HOME%\bin"
Send-EnvChange
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
| `[ERROR] Java 8 detectado` o `JAVA_HOME` con ruta `JDK-80...` | Ejecutar `python scripts\configurar_java.py --instalar` y abrir una nueva terminal |
| `java -version` sigue mostrando Java 8 tras la corrección | El `Path` del sistema tiene Java 8 antes que el del usuario; ejecutar `python scripts\configurar_java.py --sistema` como administrador (Spark ya funciona con `JAVA_HOME`) |
| Java 17 instalado pero `[AVISO] ... instalación dañada` | Ejecutar `python scripts\configurar_java.py --reinstalar` |
| `winget` no disponible o sin permisos | El script instala automáticamente el ZIP oficial en la carpeta del usuario |
| `[notice] A new release of pip is available` | Aviso informativo; se elimina con `python -m pip install --upgrade pip` |
| `Did not find winutils.exe` / `HADOOP_HOME unset` | Repetir el paso 4 y definir `HADOOP_HOME` |
| `UnsatisfiedLinkError ... NativeIO$Windows.access0` al escribir | Copiar `hadoop.dll` en `C:\Windows\System32` |
| `Python worker failed to connect back` | Definir `PYSPARK_PYTHON=python` y revisar el cortafuegos o el antivirus |
| `Python was not found; run without arguments to install from the Microsoft Store` | Desactivar los alias de ejecución de aplicaciones de Python en Configuración |

Otros casos se describen en la guía de [solución de problemas](06-solucion-problemas.md).

## Referencias

Eclipse Foundation. (s.f.). *Eclipse Temurin* [Software]. Adoptium. Recuperado el 8 de noviembre de 2026, de https://adoptium.net/

The Apache Software Foundation. (2026a). *Spark overview* (Versión 4.3.0) [Documentación técnica]. https://spark.apache.org/docs/latest/

The Apache Software Foundation. (2026f). *Download Apache Spark* [Página web]. Recuperado el 8 de noviembre de 2026, de https://spark.apache.org/downloads.html
