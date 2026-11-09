<#
=============================================================================
 Funciones compartidas para configurar el entorno del taller en Windows.
 Las utilizan preparar_entorno_windows.ps1 e instalar_spark_windows.ps1
 (se cargan con: . "$PSScriptRoot\entorno_windows.ps1").

 Las variables se leen y escriben directamente en el registro del usuario
 (HKCU\Environment) SIN expandir, para conservar entradas dinámicas como
 %JAVA_HOME%\bin y el tipo REG_EXPAND_SZ del Path.
=============================================================================
#>

function Ok($m)   { Write-Host $m -ForegroundColor Green }
function Warn($m) { Write-Host $m -ForegroundColor Yellow }
function Err($m)  { Write-Host $m -ForegroundColor Red }

function Test-Admin {
    $id = [Security.Principal.WindowsIdentity]::GetCurrent()
    return ([Security.Principal.WindowsPrincipal]$id).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Get-RawEnv([string]$Nombre, [string]$Alcance = "User") {
    # Lee una variable permanente tal como está guardada (sin expandir %VARIABLES%)
    if ($Alcance -eq "User") {
        $k = [Microsoft.Win32.Registry]::CurrentUser.OpenSubKey("Environment")
    } else {
        $k = [Microsoft.Win32.Registry]::LocalMachine.OpenSubKey("SYSTEM\CurrentControlSet\Control\Session Manager\Environment")
    }
    if (-not $k) { return "" }
    $v = $k.GetValue($Nombre, "", [Microsoft.Win32.RegistryValueOptions]::DoNotExpandEnvironmentNames)
    $k.Close()
    return [string]$v
}

function Set-UserEnv([string]$Nombre, [string]$Valor, [switch]$Expandible) {
    # Guarda una variable permanente del usuario y la aplica en la sesión actual
    $k = [Microsoft.Win32.Registry]::CurrentUser.CreateSubKey("Environment")
    if ($Expandible) { $tipo = [Microsoft.Win32.RegistryValueKind]::ExpandString }
    else             { $tipo = [Microsoft.Win32.RegistryValueKind]::String }
    $k.SetValue($Nombre, $Valor, $tipo)
    $k.Close()
    if ($Nombre -ne "Path") { Set-Item -Path "Env:$Nombre" -Value ([Environment]::ExpandEnvironmentVariables($Valor)) }
}

function Add-UserPathEntry([string]$Entrada) {
    # Agrega una entrada al Path del usuario si no existe (comparación sin distinguir mayúsculas)
    $partes = @((Get-RawEnv "Path" "User") -split ';' | Where-Object { $_.Trim() })
    foreach ($p in $partes) { if ($p.TrimEnd('\') -ieq $Entrada.TrimEnd('\')) { return $false } }
    Set-UserEnv "Path" (($partes + $Entrada) -join ';') -Expandible
    return $true
}

function Send-EnvChange {
    # Notifica a Windows que cambiaron las variables (las terminales nuevas las verán)
    [Environment]::SetEnvironmentVariable("TALLER_SPARK_TMP", "1", "User")
    [Environment]::SetEnvironmentVariable("TALLER_SPARK_TMP", $null, "User")
}

function Update-SessionEnv {
    # Recarga en la sesión actual las variables permanentes (usuario sobre sistema)
    foreach ($n in @("JAVA_HOME", "HADOOP_HOME", "SPARK_HOME", "PYSPARK_PYTHON")) {
        $v = Get-RawEnv $n "User"
        if (-not $v) { $v = Get-RawEnv $n "Machine" }
        if ($v) { Set-Item -Path "Env:$n" -Value ([Environment]::ExpandEnvironmentVariables($v)) }
    }
    $p = (Get-RawEnv "Path" "Machine") + ";" + (Get-RawEnv "Path" "User")
    # Spark usa JAVA_HOME; además se antepone su bin para que 'java -version' muestre la versión correcta
    if ($env:JAVA_HOME) { $p = "$env:JAVA_HOME\bin;" + $p }
    $env:Path = [Environment]::ExpandEnvironmentVariables($p)
}

function Find-Python {
    # Devuelve la ruta completa de un Python 3.10+ que funcione (ignora el acceso directo de Microsoft Store)
    $ErrorActionPreference = "Continue"   # en PowerShell 5.1, stderr redirigido no debe detener el script
    foreach ($cand in @("python", "py")) {
        if (-not (Get-Command $cand -ErrorAction SilentlyContinue)) { continue }
        $extra = @()
        if ($cand -eq "py") { $extra = @("-3") }
        $out = & $cand @extra -c "import sys; print(sys.executable); print('%d.%d' % sys.version_info[:2])" 2>$null
        if ($LASTEXITCODE -eq 0 -and @($out).Count -ge 2) {
            if ([version]$out[1] -ge [version]"3.10") { return $out[0] }
        }
    }
    return $null
}

function Install-PythonIfMissing {
    $py = Find-Python
    if ($py) { Ok "==> Python: $py"; return $py }
    Warn "==> No se encontró Python 3.10 o superior."
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        Ok "==> Instalando Python 3.12 con winget..."
        winget install --id Python.Python.3.12 -e --silent --accept-source-agreements --accept-package-agreements
        Update-SessionEnv
        $py = Find-Python
    }
    if (-not $py) {
        Err "No fue posible instalar Python. Descargarlo de https://www.python.org/downloads/ (marcar 'Add python.exe to PATH') y repetir."
        Err "Si aparece un mensaje de Microsoft Store, desactivar los alias de Python en Configuración > Aplicaciones > Alias de ejecución."
        exit 1
    }
    Ok "==> Python: $py"
    return $py
}

function Invoke-ConfigurarJava([string]$Python, [switch]$Reinstalar, [switch]$Sistema) {
    # Valida Java; si no hay 17/21 válido lo instala (winget o ZIP portable) y configura JAVA_HOME y Path
    $argumentos = @("$PSScriptRoot\configurar_java.py", "--instalar")
    if ($Reinstalar) { $argumentos += "--reinstalar" }
    if ($Sistema) {
        if (Test-Admin) { $argumentos += "--sistema" }
        else { Warn "    -Sistema requiere PowerShell como administrador; solo se configurarán las variables del usuario." }
    }
    & $Python @argumentos
    if ($LASTEXITCODE -ne 0) { Err "No fue posible configurar Java."; exit 1 }
    Update-SessionEnv
    Send-EnvChange
}

function Install-Winutils([string]$HadoopDir, [string]$Base) {
    # winutils.exe y hadoop.dll: necesarios para que Spark escriba archivos en Windows
    try {
        New-Item -ItemType Directory -Force -Path "$HadoopDir\bin" -ErrorAction Stop | Out-Null
    } catch {
        $HadoopDir = Join-Path $env:LOCALAPPDATA "hadoop"
        Warn "    Sin permisos para crear la carpeta indicada; se usará $HadoopDir"
        New-Item -ItemType Directory -Force -Path "$HadoopDir\bin" | Out-Null
    }
    foreach ($f in @("winutils.exe", "hadoop.dll")) {
        $dest = "$HadoopDir\bin\$f"
        if (-not (Test-Path $dest) -or (Get-Item $dest).Length -eq 0) {
            Ok "==> Descargando $f"
            Invoke-WebRequest -Uri "$Base/$f" -OutFile $dest -UseBasicParsing
        }
    }
    Set-UserEnv "HADOOP_HOME" $HadoopDir
    if (Add-UserPathEntry "%HADOOP_HOME%\bin") { Ok "==> Path (usuario): %HADOOP_HOME%\bin agregado" }
    if (Test-Admin) {
        Copy-Item "$HadoopDir\bin\hadoop.dll" "$env:WINDIR\System32\" -Force
        Ok "==> hadoop.dll copiado a System32"
    } else {
        Warn "    hadoop.dll no se copió a System32 (requiere administrador). Solo es necesario si aparece el error NativeIO`$Windows.access0."
    }
    Ok "==> HADOOP_HOME = $HadoopDir"
    return $HadoopDir
}

function Show-EnvSummary {
    $ErrorActionPreference = "Continue"
    Ok ""
    Ok "Variables de entorno del usuario (permanentes):"
    foreach ($n in @("JAVA_HOME", "HADOOP_HOME", "SPARK_HOME", "PYSPARK_PYTHON")) {
        $v = Get-RawEnv $n "User"
        if ($v) { Write-Host ("   {0,-15}= {1}" -f $n, $v) }
    }
    $javaPath = (Get-Command java -ErrorAction SilentlyContinue).Source
    if ($javaPath) {
        $ver = (& $javaPath -version 2>&1 | Select-Object -First 1)
        Write-Host "   java (sesión)  = $javaPath"
        Write-Host "                    $ver"
    }
}
