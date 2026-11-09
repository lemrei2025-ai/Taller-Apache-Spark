#!/usr/bin/env python3
"""
Validación, instalación (o reinstalación) y configuración automática de Java para Spark 4.x.

Spark 4.x requiere Java 17 o 21. Este módulo:

  1. Busca todos los JDK instalados (Windows, Linux y macOS) y los VALIDA ejecutando
     'java -version'; una instalación dañada o incompleta se descarta.
  2. Selecciona un JDK compatible (se prefiere 17; luego 21).
  3. Si no existe ninguno válido, o si se pide --reinstalar, instala Eclipse Temurin 17:
       - Windows: winget; si winget no existe o falla, descarga el ZIP oficial de Adoptium
         y lo instala en la carpeta del usuario (no requiere permisos de administrador).
       - Linux: apt; si no es posible, descarga el .tar.gz oficial en ~/.local/share/jdk.
       - macOS: Homebrew; si no es posible, descarga el .tar.gz oficial en ~/.local/share/jdk.
  4. Configura las variables de entorno de forma permanente:
       - Windows: JAVA_HOME del usuario y Path del usuario (agrega %JAVA_HOME%\\bin al inicio
         y retira las rutas de versiones de Java no compatibles). Con --sistema y permisos de
         administrador, corrige también JAVA_HOME y Path del sistema.
       - Linux/macOS: bloque en ~/.bashrc o ~/.zshrc.
  5. Activa el JDK en el proceso actual, de modo que PySpark lo use de inmediato.

Uso:
    python scripts/configurar_java.py                 # valida, corrige y guarda
    python scripts/configurar_java.py --instalar      # instala Java 17 si no hay uno válido
    python scripts/configurar_java.py --reinstalar    # reinstala Java 17 aunque exista
    python scripts/configurar_java.py --sistema       # Windows, como administrador: corrige también
                                                      # las variables del sistema
    python scripts/configurar_java.py --diagnostico   # solo muestra el estado actual
    python scripts/configurar_java.py --listar        # lista los JDK encontrados
    python scripts/configurar_java.py --solo-sesion   # no modifica la configuración permanente

Desde Python (cuadernos):
    from configurar_java import asegurar_java
    asegurar_java()
"""
from __future__ import annotations

import argparse
import glob
import os
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import zipfile
from pathlib import Path

VERSIONES_COMPATIBLES = (17, 21)
VERSION_A_INSTALAR = 17
SISTEMA = platform.system()          # "Windows", "Linux", "Darwin"
EXE = "java.exe" if SISTEMA == "Windows" else "java"
MARCA = "# ---- JAVA_HOME para Apache Spark ----"
URL_ADOPTIUM = ("https://api.adoptium.net/v3/binary/latest/{version}/ga/{so}/{arq}"
                "/jdk/hotspot/normal/eclipse?project=jdk")
ID_WINGET = "EclipseAdoptium.Temurin.17.JDK"


def _carpeta_portable() -> Path:
    if SISTEMA == "Windows":
        return Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "Programs" / "Eclipse Adoptium"
    return Path.home() / ".local" / "share" / "jdk"


# =========================================================================== versión y validación
def _version_mayor(texto: str) -> int:
    partes = texto.split(".")
    mayor = int(re.sub(r"\D.*", "", partes[0]) or 0)
    if mayor == 1 and len(partes) > 1:          # formato antiguo: 1.8.0_xxx
        mayor = int(re.sub(r"\D.*", "", partes[1]) or 0)
    return mayor


def version_de_ejecutable(java: str | os.PathLike) -> int | None:
    """Ejecuta 'java -version' y devuelve la versión mayor, o None si el ejecutable no funciona."""
    try:
        r = subprocess.run([str(java), "-version"], capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    m = re.search(r'version "([^"]+)"', r.stderr + r.stdout)
    return _version_mayor(m.group(1)) if (m and r.returncode == 0) else None


def version_de_jdk(home: str | os.PathLike) -> int | None:
    """Versión declarada por el JDK (archivo 'release'; si no existe, ejecuta java)."""
    home = Path(home)
    java = home / "bin" / EXE
    if not java.exists():
        return None
    release = home / "release"
    if release.exists():
        m = re.search(r'JAVA_VERSION="([^"]+)"', release.read_text(errors="ignore"))
        if m:
            return _version_mayor(m.group(1))
    return version_de_ejecutable(java)


def validar_jdk(home: str | os.PathLike) -> int | None:
    """Comprueba que el JDK realmente funcione: ejecuta java -version y verifica la versión."""
    home = Path(home)
    java = home / "bin" / EXE
    if not java.exists():
        return None
    v = version_de_ejecutable(java)
    return v if v in VERSIONES_COMPATIBLES else None


# =========================================================================== búsqueda
def _home_desde_ejecutable(ruta_java: str) -> Path:
    return Path(os.path.realpath(ruta_java)).parent.parent


def _candidatos() -> list[Path]:
    rutas: list[Path] = []
    if os.environ.get("JAVA_HOME"):
        rutas.append(Path(os.environ["JAVA_HOME"]))
    if SISTEMA == "Windows":
        for alcance in ("usuario", "sistema"):
            valor = leer_variable("JAVA_HOME", alcance)
            if valor:
                rutas.append(Path(os.path.expandvars(valor)))
    en_path = shutil.which("java")
    if en_path:
        rutas.append(_home_desde_ejecutable(en_path))

    patrones: list[str] = []
    portable = str(_carpeta_portable())
    if SISTEMA == "Windows":
        bases = {os.environ.get(v) for v in ("ProgramFiles", "ProgramW6432", "ProgramFiles(x86)")}
        bases.add(os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs"))
        for b in filter(None, bases):
            patrones += [os.path.join(b, "*", "bin", EXE), os.path.join(b, "*", "*", "bin", EXE)]
        patrones += [r"C:\jdk*\bin\java.exe", r"C:\Java\*\bin\java.exe",
                     os.path.join(os.path.expanduser("~"), ".jdks", "*", "bin", EXE),
                     os.path.join(portable, "*", "bin", EXE)]
    elif SISTEMA == "Darwin":
        patrones += ["/Library/Java/JavaVirtualMachines/*/Contents/Home/bin/java",
                     os.path.expanduser("~/Library/Java/JavaVirtualMachines/*/Contents/Home/bin/java"),
                     "/opt/homebrew/opt/openjdk*/libexec/openjdk.jdk/Contents/Home/bin/java",
                     "/usr/local/opt/openjdk*/libexec/openjdk.jdk/Contents/Home/bin/java",
                     os.path.join(portable, "*", "Contents", "Home", "bin", "java")]
    else:
        patrones += ["/usr/lib/jvm/*/bin/java", "/opt/*jdk*/bin/java", "/opt/java/*/bin/java",
                     os.path.expanduser("~/.sdkman/candidates/java/*/bin/java"),
                     os.path.expanduser("~/.jdks/*/bin/java"),
                     os.path.join(portable, "*", "bin", "java")]
    for patron in patrones:
        rutas += [_home_desde_ejecutable(p) for p in glob.glob(patron)]

    vistos, unicos = set(), []
    for r in rutas:
        clave = os.path.normcase(os.path.realpath(r))
        if clave not in vistos:
            vistos.add(clave)
            unicos.append(Path(os.path.realpath(r)))
    return unicos


def buscar_jdks() -> list[tuple[int, Path]]:
    """Lista de (versión declarada, ruta) de todos los JDK encontrados."""
    return [(v, h) for h in _candidatos() if (v := version_de_jdk(h))]


def elegir_jdk(jdks: list[tuple[int, Path]], verbose: bool = True) -> tuple[int, Path] | None:
    """Devuelve el primer JDK compatible que funcione (prefiere 17, luego 21)."""
    compatibles = sorted([j for j in jdks if j[0] in VERSIONES_COMPATIBLES],
                         key=lambda j: (VERSIONES_COMPATIBLES.index(j[0]), str(j[1])), reverse=False)
    for v, home in compatibles:
        if validar_jdk(home):
            return v, home
        if verbose:
            print(f"[AVISO] Java {v} en {home} no funciona correctamente (instalación dañada o incompleta).")
    return None


# =========================================================================== variables en Windows
def _clave_windows(alcance: str):
    import winreg
    if alcance == "usuario":
        return winreg.HKEY_CURRENT_USER, r"Environment"
    return winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"


def leer_variable(nombre: str, alcance: str = "usuario") -> str | None:
    """Lee una variable de entorno permanente de Windows (registro), sin expandir."""
    if SISTEMA != "Windows":
        return None
    import winreg
    raiz, ruta = _clave_windows(alcance)
    try:
        with winreg.OpenKey(raiz, ruta) as k:
            return winreg.QueryValueEx(k, nombre)[0]
    except OSError:
        return None


def escribir_variable(nombre: str, valor: str, alcance: str = "usuario", expandible: bool = False) -> None:
    """Escribe una variable de entorno permanente de Windows en el registro."""
    import winreg
    raiz, ruta = _clave_windows(alcance)
    tipo = winreg.REG_EXPAND_SZ if expandible else winreg.REG_SZ
    with winreg.OpenKey(raiz, ruta, 0, winreg.KEY_SET_VALUE) as k:
        winreg.SetValueEx(k, nombre, 0, tipo, valor)


def notificar_cambio_entorno() -> None:
    """Avisa a Windows (Explorador y aplicaciones nuevas) que cambiaron las variables de entorno."""
    try:
        import ctypes
        from ctypes import wintypes
        resultado = wintypes.DWORD()
        ctypes.windll.user32.SendMessageTimeoutW(0xFFFF, 0x001A, 0, "Environment", 0x0002, 5000,
                                                 ctypes.byref(resultado))
    except Exception:  # noqa: BLE001
        pass


def es_administrador() -> bool:
    if SISTEMA != "Windows":
        return os.geteuid() == 0 if hasattr(os, "geteuid") else False
    try:
        import ctypes
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:  # noqa: BLE001
        return False


def _es_entrada_java(entrada: str) -> Path | None:
    """Si la entrada del Path contiene un java.exe, devuelve la ruta del ejecutable."""
    ruta = Path(os.path.expandvars(entrada.strip().strip('"')))
    java = ruta / EXE
    return java if java.exists() else None


def limpiar_path(valor: str, agregar_java_home: bool = True) -> tuple[str, list[str]]:
    """Devuelve (nuevo_path, entradas_retiradas).

    - Retira las rutas cuyo java.exe no es compatible (p. ej. Java 8 o el 'javapath' de Oracle).
    - Retira duplicados de %JAVA_HOME%\\bin y lo agrega al inicio.
    - Conserva el resto de las entradas en su orden original.
    """
    nuevas, retiradas, vistas = [], [], set()
    for entrada in [e for e in (valor or "").split(";") if e.strip()]:
        normal = entrada.strip().rstrip("\\/").lower()
        if normal in ("%java_home%\\bin", "%java_home%/bin"):
            continue
        java = _es_entrada_java(entrada)
        if java is not None and version_de_ejecutable(java) not in VERSIONES_COMPATIBLES:
            retiradas.append(entrada)
            continue
        if normal not in vistas:
            vistas.add(normal)
            nuevas.append(entrada)
    if agregar_java_home:
        nuevas.insert(0, r"%JAVA_HOME%\bin")
    return ";".join(nuevas), retiradas


def configurar_variables_windows(home: Path, sistema: bool = False) -> list[str]:
    """Configura JAVA_HOME y Path de forma permanente en Windows. Devuelve un registro de acciones."""
    acciones = []
    escribir_variable("JAVA_HOME", str(home), "usuario")
    acciones.append(f"JAVA_HOME (usuario) = {home}")

    path_usuario = leer_variable("Path", "usuario") or ""
    nuevo, retiradas = limpiar_path(path_usuario)
    if nuevo != path_usuario:
        escribir_variable("Path", nuevo, "usuario", expandible=True)
        acciones.append(r"Path (usuario): %JAVA_HOME%\bin agregado al inicio")
    for r in retiradas:
        acciones.append(f"Path (usuario): retirada la ruta de Java no compatible {r}")

    path_sistema = leer_variable("Path", "sistema") or ""
    _, conflictos = limpiar_path(path_sistema, agregar_java_home=False)
    java_home_sis = leer_variable("JAVA_HOME", "sistema")
    jh_sis_malo = bool(java_home_sis) and validar_jdk(os.path.expandvars(java_home_sis)) is None

    if sistema:
        if not es_administrador():
            acciones.append("[AVISO] --sistema requiere ejecutar la terminal como administrador; "
                            "no se modificaron las variables del sistema.")
        else:
            escribir_variable("JAVA_HOME", str(home), "sistema")
            acciones.append(f"JAVA_HOME (sistema) = {home}")
            nuevo_sis, retiradas_sis = limpiar_path(path_sistema)
            escribir_variable("Path", nuevo_sis, "sistema", expandible=True)
            acciones.append(r"Path (sistema): %JAVA_HOME%\bin agregado al inicio")
            acciones += [f"Path (sistema): retirada {r}" for r in retiradas_sis]
            conflictos, jh_sis_malo = [], False
    if conflictos or jh_sis_malo:
        acciones.append("[AVISO] Las variables del SISTEMA aún apuntan a una versión de Java no compatible "
                        f"({', '.join(conflictos) or java_home_sis}). Spark funciona igualmente, porque usa "
                        "JAVA_HOME del usuario, pero 'java -version' puede mostrar la versión antigua. Para "
                        "corregirlo: abrir PowerShell como administrador y ejecutar "
                        "'python scripts\\configurar_java.py --sistema'.")
    notificar_cambio_entorno()
    return acciones


def configurar_variables_unix(home: Path) -> list[str]:
    rc = Path.home() / (".zshrc" if SISTEMA == "Darwin" else ".bashrc")
    bloque = f'{MARCA}\nexport JAVA_HOME="{home}"\nexport PATH="$JAVA_HOME/bin:$PATH"\n'
    contenido = rc.read_text() if rc.exists() else ""
    if MARCA in contenido:
        contenido = re.sub(re.escape(MARCA) + r"\n(?:export .*\n){1,2}", bloque, contenido)
    else:
        contenido += "\n" + bloque
    rc.write_text(contenido)
    return [f"JAVA_HOME y PATH guardados en {rc} (aplica en terminales nuevas o tras 'source {rc}')"]


def persistir_java_home(home: Path, sistema: bool = False) -> list[str]:
    if SISTEMA == "Windows":
        return configurar_variables_windows(home, sistema=sistema)
    return configurar_variables_unix(home)


def activar_en_proceso(home: Path) -> None:
    """JAVA_HOME y PATH del proceso actual (y de sus hijos, como la JVM de Spark)."""
    os.environ["JAVA_HOME"] = str(home)
    bin_dir = str(home / "bin")
    partes = [p for p in os.environ.get("PATH", "").split(os.pathsep) if p and os.path.normcase(p) != os.path.normcase(bin_dir)]
    os.environ["PATH"] = os.pathsep.join([bin_dir] + partes)


# =========================================================================== instalación
def _arquitectura() -> str:
    m = platform.machine().lower()
    return "aarch64" if m in ("arm64", "aarch64") else "x64"


def _descargar(url: str, destino: Path) -> None:
    print(f"[INFO]  Descargando {url}")
    with urllib.request.urlopen(url, timeout=120) as r, open(destino, "wb") as f:
        total = int(r.headers.get("Content-Length") or 0)
        leido = 0
        while bloque := r.read(1024 * 1024):
            f.write(bloque)
            leido += len(bloque)
            if total:
                print(f"\r        {leido / 1024**2:6.1f} / {total / 1024**2:.1f} MB", end="", flush=True)
    print()


def instalar_portable(version: int = VERSION_A_INSTALAR) -> Path | None:
    """Descarga el JDK oficial de Adoptium y lo extrae en la carpeta del usuario (sin administrador)."""
    so = {"Windows": "windows", "Darwin": "mac"}.get(SISTEMA, "linux")
    url = URL_ADOPTIUM.format(version=version, so=so, arq=_arquitectura())
    destino = _carpeta_portable()
    destino.mkdir(parents=True, exist_ok=True)
    try:
        with tempfile.TemporaryDirectory() as tmp:
            archivo = Path(tmp) / ("jdk.zip" if so == "windows" else "jdk.tar.gz")
            _descargar(url, archivo)
            antes = {p.name for p in destino.iterdir()}
            if so == "windows":
                with zipfile.ZipFile(archivo) as z:
                    z.extractall(destino)
            else:
                with tarfile.open(archivo) as t:
                    if hasattr(tarfile, "data_filter"):
                        t.extractall(destino, filter="data")
                    else:
                        t.extractall(destino)
            nuevos = [destino / n for n in {p.name for p in destino.iterdir()} - antes] or list(destino.iterdir())
    except Exception as e:  # noqa: BLE001
        print(f"[ERROR] Falló la descarga o extracción del JDK: {e}")
        return None
    for carpeta in nuevos:
        for home in (carpeta, carpeta / "Contents" / "Home"):
            if validar_jdk(home):
                print(f"[OK]    JDK instalado en {home}")
                return home
    print("[ERROR] El JDK descargado no pudo validarse.")
    return None


def instalar_con_gestor(reinstalar: bool = False) -> bool:
    if SISTEMA == "Windows" and shutil.which("winget"):
        cmd = ["winget", "install", "--id", ID_WINGET, "-e", "--silent",
               "--accept-source-agreements", "--accept-package-agreements"]
        if reinstalar:
            cmd.append("--force")
    elif SISTEMA == "Darwin" and shutil.which("brew"):
        cmd = ["brew", "reinstall" if reinstalar else "install", "openjdk@17"]
    elif SISTEMA == "Linux" and shutil.which("apt-get"):
        cmd = ["sudo", "apt-get", "install", "-y"] + (["--reinstall"] if reinstalar else []) + ["openjdk-17-jdk"]
    else:
        return False
    print("[INFO]  Instalando Java 17:", " ".join(cmd))
    try:
        return subprocess.run(cmd).returncode == 0
    except OSError as e:
        print("[AVISO]", e)
        return False


def instalar_java(reinstalar: bool = False) -> Path | None:
    """Instala Java 17 con el gestor de paquetes; si falla, con el paquete oficial portable."""
    if instalar_con_gestor(reinstalar):
        elegido = elegir_jdk(buscar_jdks(), verbose=False)
        if elegido:
            return elegido[1]
        print("[AVISO] El gestor de paquetes terminó, pero no se encontró un JDK válido.")
    print("[INFO]  Se intentará la instalación portable (sin permisos de administrador).")
    return instalar_portable()


# =========================================================================== diagnóstico
def diagnostico() -> None:
    print("=" * 66)
    print(" Diagnóstico de Java")
    print("=" * 66)
    print(f"Sistema operativo        : {SISTEMA} ({platform.machine()})")
    print(f"JAVA_HOME (proceso)      : {os.environ.get('JAVA_HOME', '(no definido)')}")
    if SISTEMA == "Windows":
        print(f"JAVA_HOME (usuario)      : {leer_variable('JAVA_HOME', 'usuario') or '(no definido)'}")
        print(f"JAVA_HOME (sistema)      : {leer_variable('JAVA_HOME', 'sistema') or '(no definido)'}")
        print(f"Permisos de administrador: {'sí' if es_administrador() else 'no'}")
        print("Ejecutables java en el Path (orden de búsqueda: sistema y luego usuario):")
        for alcance in ("sistema", "usuario"):
            for e in (leer_variable("Path", alcance) or "").split(";"):
                java = _es_entrada_java(e) if e.strip() else None
                if java:
                    print(f"   [{alcance:<7}] Java {version_de_ejecutable(java) or '?':<4} {e}")
    primero = shutil.which("java")
    print(f"'java' en esta terminal  : {primero or '(no encontrado)'}"
          + (f"  -> Java {version_de_ejecutable(primero)}" if primero else ""))
    print("JDK encontrados:")
    for v, h in sorted(buscar_jdks()):
        estado = "válido" if validar_jdk(h) else ("no compatible" if v not in VERSIONES_COMPATIBLES else "DAÑADO")
        print(f"   Java {v:<3} {estado:<14} {h}")


# =========================================================================== función principal
def asegurar_java(persistir: bool = False, instalar: bool = False, preguntar: bool = False,
                  silencioso: bool = False, reinstalar: bool = False, sistema: bool = False) -> Path | None:
    """
    Garantiza que el proceso actual use un Java 17 o 21 que funcione.

    persistir : guarda las variables de entorno de forma permanente si fue necesario corregirlas.
    instalar  : instala Java 17 si no se encuentra uno válido.
    preguntar : pide confirmación antes de instalar (modo interactivo).
    silencioso: no imprime mensajes cuando Java ya es correcto.
    reinstalar: reinstala Java 17 aunque exista una versión válida.
    sistema   : (Windows, administrador) corrige también las variables del sistema.
    """
    actual = os.environ.get("JAVA_HOME")
    if not reinstalar and actual and validar_jdk(actual):
        activar_en_proceso(Path(actual))
        if not silencioso:
            print(f"[OK]    Java {validar_jdk(actual)} en JAVA_HOME ({actual})")
        if persistir and (sistema or (SISTEMA == "Windows" and (_path_usuario_desactualizado()
                or leer_variable("JAVA_HOME", "usuario") != actual))):
            for a in persistir_java_home(Path(actual), sistema=sistema):
                print("        " + a if not a.startswith("[") else a)
        return Path(actual)

    if actual and not reinstalar:
        v_actual = version_de_jdk(actual)
        motivo = (f"Java {v_actual}, no compatible" if v_actual and v_actual not in VERSIONES_COMPATIBLES
                  else "una instalación que no existe o no funciona")
        print(f"[AVISO] JAVA_HOME apunta a {motivo}: {actual}")

    elegido = None if reinstalar else elegir_jdk(buscar_jdks())
    home = elegido[1] if elegido else None

    if home is None:
        if not reinstalar:
            print("[AVISO] No se encontró un Java 17/21 válido en el equipo.")
        if preguntar and not (instalar or reinstalar) and sys.stdin.isatty():
            instalar = input("        ¿Instalar Eclipse Temurin 17 ahora? [s/N]: ").strip().lower() in ("s", "si", "sí", "y")
        if instalar or reinstalar:
            home = instalar_java(reinstalar=reinstalar)
        if home is None:
            print("[ERROR] No fue posible configurar Java 17/21. Opciones:")
            print("        python scripts/configurar_java.py --instalar")
            print("        Instalación manual: https://adoptium.net/ (Temurin 17, JDK)")
            return None

    version = validar_jdk(home)
    print(f"[OK]    Se utilizará Java {version}: {home}")
    activar_en_proceso(home)

    if persistir:
        try:
            for a in persistir_java_home(home, sistema=sistema):
                print(a if a.startswith("[") else "[OK]    " + a)
        except Exception as e:  # noqa: BLE001
            print(f"[AVISO] No fue posible guardar las variables de forma permanente: {e}")
        if SISTEMA == "Windows":
            print("        Las terminales nuevas ya usan esta configuración. En la terminal actual de PowerShell:")
            print(f'        $env:JAVA_HOME = "{home}"; $env:Path = "$env:JAVA_HOME\\bin;$env:Path"')
        else:
            print(f'        En la terminal actual: export JAVA_HOME="{home}"; export PATH="$JAVA_HOME/bin:$PATH"')
    return home


def _path_usuario_desactualizado() -> bool:
    """True si el Path del usuario no tiene %JAVA_HOME%\\bin al inicio o contiene Java no compatible."""
    actual = leer_variable("Path", "usuario") or ""
    nuevo, _ = limpiar_path(actual)
    return nuevo != actual


def main() -> int:
    ap = argparse.ArgumentParser(description="Valida, instala y configura Java 17/21 para Apache Spark.")
    ap.add_argument("--instalar", action="store_true", help="instala Java 17 si no hay uno válido")
    ap.add_argument("--reinstalar", action="store_true", help="reinstala Java 17 aunque exista")
    ap.add_argument("--sistema", action="store_true", help="Windows (administrador): corrige variables del sistema")
    ap.add_argument("--solo-sesion", action="store_true", help="no guarda cambios permanentes")
    ap.add_argument("--diagnostico", action="store_true", help="muestra el estado actual y termina")
    ap.add_argument("--listar", action="store_true", help="lista los JDK encontrados y termina")
    args = ap.parse_args()

    if args.listar:
        for v, h in sorted(buscar_jdks()):
            estado = "válido" if validar_jdk(h) else ("no compatible" if v not in VERSIONES_COMPATIBLES else "DAÑADO")
            print(f"Java {v:<3} {estado:<14} {h}")
        return 0
    if args.diagnostico:
        diagnostico()
        return 0
    home = asegurar_java(persistir=not args.solo_sesion, instalar=args.instalar, preguntar=True,
                         reinstalar=args.reinstalar, sistema=args.sistema)
    if home:
        v = version_de_ejecutable(Path(home) / "bin" / EXE)
        print(f"[OK]    Verificación final: {Path(home) / 'bin' / EXE} -> Java {v}")
    return 0 if home else 1


if __name__ == "__main__":
    sys.exit(main())
