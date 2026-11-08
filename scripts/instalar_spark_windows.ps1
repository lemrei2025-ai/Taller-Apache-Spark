<#
=============================================================================
 Instalación automática de Apache Spark - Windows 10/11 (PowerShell)
 Taller de Big Data

 Uso (PowerShell, NO requiere administrador salvo para copiar hadoop.dll):
   Set-ExecutionPolicy -Scope Process Bypass
   .\scripts\instalar_spark_windows.ps1
   .\scripts\instalar_spark_windows.ps1 -SparkVersion 4.2.1

 Requisito previo: tener instalado Java 17/21 (Temurin) y Python 3.10+.
   winget install EclipseAdoptium.Temurin.17.JDK
   winget install Python.Python.3.12
=============================================================================
#>
param(
    [string]$SparkVersion = "4.3.0",
    [string]$SparkDir     = "C:\spark",
    [string]$HadoopDir    = "C:\hadoop",
    [string]$WinutilsBase = "https://raw.githubusercontent.com/cdarlint/winutils/master/hadoop-3.3.6/bin"
)

$ErrorActionPreference = "Stop"
$ProgressPreference    = "SilentlyContinue"   # acelera Invoke-WebRequest

function Ok($m)   { Write-Host $m -ForegroundColor Green }
function Warn($m) { Write-Host $m -ForegroundColor Yellow }
function Err($m)  { Write-Host $m -ForegroundColor Red }

# ------------------------------------------------------------- 1. Java
try {
    $jv = (& java -version 2>&1 | Select-Object -First 1).ToString()
    Ok "==> Java detectado: $jv"
} catch {
    Err "No se encontró Java. Puede instalarse con: winget install EclipseAdoptium.Temurin.17.JDK"
    exit 1
}
if (-not $env:JAVA_HOME) {
    $javaExe  = (Get-Command java).Source
    $javaHome = Split-Path (Split-Path $javaExe -Parent) -Parent
    [Environment]::SetEnvironmentVariable("JAVA_HOME", $javaHome, "User")
    $env:JAVA_HOME = $javaHome
    Ok "==> JAVA_HOME = $javaHome"
}

# ------------------------------------------------------------- 2. Python
try { Ok ("==> " + (& python --version 2>&1)) }
catch { Err "No se encontró Python. Debe instalarse desde python.org con la opción 'Add to PATH'."; exit 1 }

# ------------------------------------------------------------- 3. Spark
$pkg      = "spark-$SparkVersion-bin-hadoop3"
$sparkHome = Join-Path $SparkDir $pkg
if (Test-Path "$sparkHome\bin\spark-submit.cmd") {
    Ok "==> Spark ya existe en $sparkHome"
} else {
    New-Item -ItemType Directory -Force -Path $SparkDir | Out-Null
    $tgz = Join-Path $env:TEMP "$pkg.tgz"
    $urls = @(
        "https://dlcdn.apache.org/spark/spark-$SparkVersion/$pkg.tgz",
        "https://archive.apache.org/dist/spark/spark-$SparkVersion/$pkg.tgz"
    )
    $ok = $false
    foreach ($u in $urls) {
        try { Ok "==> Descargando $u"; Invoke-WebRequest -Uri $u -OutFile $tgz; $ok = $true; break }
        catch { Warn "    Falló, probando siguiente mirror..." }
    }
    if (-not $ok) { Err "No se pudo descargar Spark."; exit 1 }
    Ok "==> Descomprimiendo en $SparkDir"
    tar -xzf $tgz -C $SparkDir
    Remove-Item $tgz
}

# ------------------------------------------------------------- 4. winutils
New-Item -ItemType Directory -Force -Path "$HadoopDir\bin" | Out-Null
foreach ($f in @("winutils.exe", "hadoop.dll")) {
    $dest = "$HadoopDir\bin\$f"
    if (-not (Test-Path $dest)) {
        Ok "==> Descargando $f"
        Invoke-WebRequest -Uri "$WinutilsBase/$f" -OutFile $dest
    }
}
try {
    Copy-Item "$HadoopDir\bin\hadoop.dll" "C:\Windows\System32\" -Force
    Ok "==> hadoop.dll copiado a System32"
} catch {
    Warn "    No se pudo copiar hadoop.dll a System32 (si aparecen errores al escribir archivos, ejecutar como administrador)."
}

# ------------------------------------------------------------- 5. Variables
[Environment]::SetEnvironmentVariable("SPARK_HOME",     $sparkHome, "User")
[Environment]::SetEnvironmentVariable("HADOOP_HOME",    $HadoopDir, "User")
[Environment]::SetEnvironmentVariable("PYSPARK_PYTHON", "python",   "User")

$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
foreach ($p in @("$sparkHome\bin", "$HadoopDir\bin")) {
    if ($userPath -notlike "*$p*") { $userPath = "$userPath;$p" }
}
[Environment]::SetEnvironmentVariable("Path", $userPath, "User")

$env:SPARK_HOME = $sparkHome; $env:HADOOP_HOME = $HadoopDir
$env:Path = "$env:Path;$sparkHome\bin;$HadoopDir\bin"

# ------------------------------------------------------------- 6. Prueba
Ok "==> Probando instalación..."
& "$sparkHome\bin\spark-submit.cmd" --version 2>&1 | Select-String "version" | Select-Object -First 2

Ok ""
Ok "[OK] Instalacion completada. Cerrar y abrir nuevamente PowerShell; luego ejecutar:"
Write-Host "   pyspark"
Write-Host "   python scripts\verificar_instalacion.py"
