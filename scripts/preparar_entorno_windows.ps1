<#
=============================================================================
 Preparación del entorno del taller - Windows (PowerShell)

 Realiza en un solo paso:
   1. Verifica Python 3.10+ (lo instala con winget si no existe).
   2. Crea el entorno virtual .venv y actualiza pip.
   3. Instala las dependencias de requirements.txt.
   4. Valida Java: si JAVA_HOME apunta a una versión no compatible (p. ej. Java 8)
      o a una instalación dañada, busca un JDK 17/21 que funcione; si no existe,
      instala Eclipse Temurin 17 (winget o, si falla, el ZIP oficial en la carpeta
      del usuario). Configura JAVA_HOME y el Path del usuario.
   5. Instala winutils.exe/hadoop.dll y configura HADOOP_HOME.
   6. Ejecuta la verificación completa del entorno.

 Uso, desde la carpeta raíz del taller:
   Set-ExecutionPolicy -Scope Process Bypass
   .\scripts\preparar_entorno_windows.ps1
   .\scripts\preparar_entorno_windows.ps1 -ReinstalarJava   # fuerza la reinstalación de Java 17
   .\scripts\preparar_entorno_windows.ps1 -Sistema          # (como administrador) corrige también
                                                            # las variables del sistema
=============================================================================
#>
param(
    [switch]$ReinstalarJava,
    [switch]$Sistema,
    [string]$HadoopDir    = "C:\hadoop",
    [string]$WinutilsBase = "https://raw.githubusercontent.com/cdarlint/winutils/master/hadoop-3.3.6/bin"
)

$ErrorActionPreference = "Stop"
$ProgressPreference    = "SilentlyContinue"
. "$PSScriptRoot\entorno_windows.ps1"

$raiz = Split-Path -Parent $PSScriptRoot
Set-Location $raiz

# 1. Python
$pythonBase = Install-PythonIfMissing

# 2. Entorno virtual y pip
if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Ok "==> Creando entorno virtual .venv"
    & $pythonBase -m venv .venv
    if ($LASTEXITCODE -ne 0) { Err "No se pudo crear el entorno virtual."; exit 1 }
}
$py = Join-Path $raiz ".venv\Scripts\python.exe"
Ok "==> Actualizando pip"
& $py -m pip install --upgrade pip --quiet --disable-pip-version-check

# 3. Dependencias
Ok "==> Instalando dependencias"
& $py -m pip install -r requirements.txt --quiet --disable-pip-version-check
if ($LASTEXITCODE -ne 0) { Err "Falló la instalación de dependencias."; exit 1 }

# 4. Java 17/21
Ok "==> Validando y configurando Java"
Invoke-ConfigurarJava -Python $py -Reinstalar:$ReinstalarJava -Sistema:$Sistema

# 5. winutils y HADOOP_HOME
Ok "==> Configurando winutils y HADOOP_HOME"
Install-Winutils -HadoopDir $HadoopDir -Base $WinutilsBase | Out-Null
Send-EnvChange
Update-SessionEnv

# 6. Verificación
Ok "==> Verificando el entorno"
& $py scripts\verificar_instalacion.py
$resultado = $LASTEXITCODE
Show-EnvSummary
if ($resultado -ne 0) { exit 1 }

Ok ""
Ok "[OK] Entorno listo. Esta terminal ya tiene las variables actualizadas; las terminales nuevas también."
Write-Host "   .venv\Scripts\Activate.ps1"
Write-Host "   jupyter lab"
