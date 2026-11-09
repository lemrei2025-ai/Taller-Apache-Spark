<#
=============================================================================
 Instalación de la distribución completa de Apache Spark - Windows 10/11
 (opción B de la guía docs/01-instalacion-windows.md)

 Pasos automáticos:
   1. Verifica Python 3.10+ (lo instala con winget si no existe).
   2. Valida Java: corrige JAVA_HOME si apunta a Java 8 o a una instalación dañada,
      y si no hay un JDK 17/21 válido instala Eclipse Temurin 17 (winget o ZIP oficial).
      Configura JAVA_HOME y el Path del usuario.
   3. Descarga y descomprime Spark en C:\spark.
   4. Instala winutils.exe y hadoop.dll y configura HADOOP_HOME.
   5. Configura SPARK_HOME, PYSPARK_PYTHON y el Path del usuario.
   6. Prueba spark-submit.

 Uso (PowerShell; no requiere administrador, salvo para -Sistema y para copiar hadoop.dll):
   Set-ExecutionPolicy -Scope Process Bypass
   .\scripts\instalar_spark_windows.ps1
   .\scripts\instalar_spark_windows.ps1 -SparkVersion 4.2.1
   .\scripts\instalar_spark_windows.ps1 -ReinstalarJava
=============================================================================
#>
param(
    [string]$SparkVersion = "4.3.0",
    [string]$SparkDir     = "C:\spark",
    [string]$HadoopDir    = "C:\hadoop",
    [string]$WinutilsBase = "https://raw.githubusercontent.com/cdarlint/winutils/master/hadoop-3.3.6/bin",
    [switch]$ReinstalarJava,
    [switch]$Sistema
)

$ErrorActionPreference = "Stop"
$ProgressPreference    = "SilentlyContinue"   # acelera Invoke-WebRequest
. "$PSScriptRoot\entorno_windows.ps1"

# ------------------------------------------------------------- 1. Python
$python = Install-PythonIfMissing

# ------------------------------------------------------------- 2. Java 17/21
Ok "==> Validando y configurando Java"
Invoke-ConfigurarJava -Python $python -Reinstalar:$ReinstalarJava -Sistema:$Sistema

# ------------------------------------------------------------- 3. Spark
$pkg       = "spark-$SparkVersion-bin-hadoop3"
$sparkHome = Join-Path $SparkDir $pkg
if (Test-Path "$sparkHome\bin\spark-submit.cmd") {
    Ok "==> Spark ya existe en $sparkHome"
} else {
    try { New-Item -ItemType Directory -Force -Path $SparkDir -ErrorAction Stop | Out-Null }
    catch {
        $SparkDir = Join-Path $env:LOCALAPPDATA "spark"
        $sparkHome = Join-Path $SparkDir $pkg
        Warn "    Sin permisos para crear la carpeta indicada; se usará $SparkDir"
        New-Item -ItemType Directory -Force -Path $SparkDir | Out-Null
    }
    $tgz = Join-Path $env:TEMP "$pkg.tgz"
    $urls = @(
        "https://dlcdn.apache.org/spark/spark-$SparkVersion/$pkg.tgz",
        "https://archive.apache.org/dist/spark/spark-$SparkVersion/$pkg.tgz"
    )
    $descargado = $false
    foreach ($u in $urls) {
        try { Ok "==> Descargando $u"; Invoke-WebRequest -Uri $u -OutFile $tgz -UseBasicParsing; $descargado = $true; break }
        catch { Warn "    Falló, probando el siguiente servidor..." }
    }
    if (-not $descargado) { Err "No se pudo descargar Spark."; exit 1 }
    Ok "==> Descomprimiendo en $SparkDir"
    tar -xzf $tgz -C $SparkDir
    Remove-Item $tgz
}

# ------------------------------------------------------------- 4. winutils y HADOOP_HOME
Install-Winutils -HadoopDir $HadoopDir -Base $WinutilsBase | Out-Null

# ------------------------------------------------------------- 5. SPARK_HOME, PYSPARK_PYTHON y Path
Set-UserEnv "SPARK_HOME" $sparkHome
Set-UserEnv "PYSPARK_PYTHON" $python
if (Add-UserPathEntry "%SPARK_HOME%\bin") { Ok "==> Path (usuario): %SPARK_HOME%\bin agregado" }
Ok "==> SPARK_HOME = $sparkHome"
Ok "==> PYSPARK_PYTHON = $python"
Send-EnvChange
Update-SessionEnv

# ------------------------------------------------------------- 6. Prueba
Ok "==> Probando spark-submit..."
$ErrorActionPreference = "Continue"
& "$sparkHome\bin\spark-submit.cmd" --version 2>&1 | ForEach-Object { "$_" } | Select-String "version" | Select-Object -First 2
Show-EnvSummary

Ok ""
Ok "[OK] Instalación completada. Esta terminal y las terminales nuevas ya tienen las variables actualizadas."
Write-Host "   pyspark"
Write-Host "   python scripts\verificar_instalacion.py"
