"""
Funciones de apoyo del Taller de Apache Spark.

Este módulo permite que los cuadernos funcionen con cualquier conjunto de datos:

  iniciar_spark(app)            Crea la SparkSession (corrige Java y el intérprete de Python).
  cargar_dataset(spark, ruta)   Lee CSV, TSV, TXT, JSON, JSON Lines, Parquet, ORC o Excel,
                                detecta separador y codificación, normaliza los nombres de
                                columna, convierte fechas y números con coma decimal.
  clasificar_columnas(df)       Asigna un rol a cada columna: numérica, categórica, fecha,
                                texto o identificador.
  perfil(df)                    Resumen por columna (tipo, rol, nulos, valores distintos...).
  leer_config() / guardar_config(cfg)
                                Configuración del dataset activo (data/dataset_config.json).
  cargar_desde_config(spark)    Carga el dataset activo (versión original o limpia).

Todas las rutas relativas se interpretan desde la carpeta raíz del repositorio.
"""
from __future__ import annotations

import csv
import io
import json
import os
import re
import sys
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
RUTA_CONFIG = RAIZ / "data" / "dataset_config.json"
CARPETA_PROCESADO = RAIZ / "data" / "procesado"

CONFIG_EJEMPLO = {
    "nombre": "ventas_tienda",
    "descripcion": "Dataset de ejemplo: ventas de una tienda en ciudades de Colombia (sintético).",
    "ruta": "data/ejemplo/ventas_tienda.csv",
    "formato": "auto",
    "separador": "auto",
    "encabezado": True,
    "codificacion": "auto",
    "decimal": "auto",
    "multilinea": False,
    "hoja_excel": 0,
    "columna_fecha": "fecha",
    "formato_fecha": None,
    "columna_objetivo": "total",
    "columnas_excluir": ["id_venta"],
    "max_categorias": 50,
    "nombre_tabla": "datos",
    "ruta_limpia": None,
}

FORMATOS = {
    ".csv": "csv", ".tsv": "csv", ".txt": "csv", ".dat": "csv",
    ".json": "json", ".jsonl": "json", ".ndjson": "json",
    ".parquet": "parquet", ".pq": "parquet", ".orc": "orc",
    ".xlsx": "excel", ".xls": "excel", ".xlsm": "excel",
}

TIPOS_NUMERICOS = {"byte", "short", "integer", "int", "long", "bigint", "float", "double", "decimal"}


# =========================================================================== sesión
def iniciar_spark(app: str = "TallerSpark", memoria_driver: str = "2g", particiones_shuffle: int = 8):
    """Crea (o recupera) la SparkSession del taller.

    - Garantiza Java 17/21 aunque JAVA_HOME apunte a otra versión.
    - Usa el mismo intérprete de Python en el driver y en los executors.
    - Lee SPARK_MASTER (Docker) o usa local[*].
    """
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    try:
        from configurar_java import asegurar_java
        asegurar_java(silencioso=True)
    except ImportError:
        pass
    os.environ.setdefault("PYSPARK_PYTHON", sys.executable)
    os.environ.setdefault("PYSPARK_DRIVER_PYTHON", sys.executable)

    from pyspark.sql import SparkSession

    master = os.environ.get("SPARK_MASTER", "local[*]")
    builder = (SparkSession.builder.appName(app).master(master)
               .config("spark.driver.memory", memoria_driver)
               .config("spark.sql.shuffle.partitions", str(particiones_shuffle))
               .config("spark.sql.session.timeZone", "America/Bogota")
               .config("spark.ui.showConsoleProgress", "false"))   # salidas limpias en los cuadernos
    if os.environ.get("SPARK_DRIVER_HOST"):
        builder = builder.config("spark.driver.host", os.environ["SPARK_DRIVER_HOST"])
    spark = builder.getOrCreate()
    spark.sparkContext.setLogLevel("ERROR")
    print(f"Spark {spark.version} | master: {spark.sparkContext.master}")
    print(f"Spark UI: {spark.sparkContext.uiWebUrl}")
    return spark


# =========================================================================== rutas y configuración
def ruta_absoluta(ruta: str | os.PathLike) -> Path:
    p = Path(ruta).expanduser()
    return p if p.is_absolute() else (RAIZ / p)


def leer_config() -> dict:
    """Lee data/dataset_config.json; si no existe, devuelve la configuración del ejemplo."""
    cfg = dict(CONFIG_EJEMPLO)
    if RUTA_CONFIG.exists():
        cfg.update(json.loads(RUTA_CONFIG.read_text(encoding="utf-8")))
    return cfg


def guardar_config(cfg: dict) -> Path:
    completo = dict(CONFIG_EJEMPLO)
    completo.update(cfg)
    RUTA_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    RUTA_CONFIG.write_text(json.dumps(completo, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Configuración guardada en {RUTA_CONFIG.relative_to(RAIZ)}")
    return RUTA_CONFIG


def listar_datasets(carpeta: str = "data") -> list[str]:
    """Lista los archivos de datos disponibles en data/ (excepto la carpeta procesado)."""
    base = ruta_absoluta(carpeta)
    archivos = []
    for p in sorted(base.rglob("*")):
        if p.is_file() and p.suffix.lower() in FORMATOS and "procesado" not in p.parts:
            archivos.append(str(p.relative_to(RAIZ)).replace("\\", "/"))
        elif p.is_dir() and p.suffix.lower() in (".parquet", ".orc") and "procesado" not in p.parts:
            archivos.append(str(p.relative_to(RAIZ)).replace("\\", "/"))
    return archivos


# =========================================================================== detección
def detectar_formato(ruta: Path) -> str:
    if ruta.is_dir():
        if any(ruta.rglob("*.parquet")):
            return "parquet"
        if any(ruta.rglob("*.orc")):
            return "orc"
        if any(ruta.rglob("*.json")):
            return "json"
        return "csv"
    fmt = FORMATOS.get(ruta.suffix.lower())
    if not fmt:
        raise ValueError(f"Extensión no reconocida: '{ruta.suffix}'. Formatos admitidos: "
                         + ", ".join(sorted(FORMATOS)))
    return fmt


def _muestra_texto(ruta: Path, n_bytes: int = 200_000) -> bytes:
    archivo = ruta
    if ruta.is_dir():
        candidatos = [p for p in ruta.rglob("*") if p.is_file() and not p.name.startswith(("_", "."))]
        if not candidatos:
            return b""
        archivo = candidatos[0]
    with open(archivo, "rb") as f:
        return f.read(n_bytes)


def detectar_codificacion(muestra: bytes) -> str:
    if muestra.startswith(b"\xef\xbb\xbf"):
        return "UTF-8"
    try:
        muestra.decode("utf-8")
        return "UTF-8"
    except UnicodeDecodeError as e:
        # Si el error está solo al final (carácter cortado por la muestra), sigue siendo UTF-8
        if e.start >= len(muestra) - 4:
            return "UTF-8"
        return "ISO-8859-1"     # típico de archivos exportados desde Excel en Windows (Latin-1)


def detectar_separador(texto: str) -> str:
    lineas = [l for l in texto.splitlines()[:50] if l.strip()]
    if not lineas:
        return ","
    try:
        return csv.Sniffer().sniff("\n".join(lineas), delimiters=",;\t|").delimiter
    except csv.Error:
        conteos = {s: sum(l.count(s) for l in lineas) for s in [",", ";", "\t", "|"]}
        return max(conteos, key=conteos.get)


# =========================================================================== nombres de columna
def normalizar_nombre(nombre: str) -> str:
    """'Fecha de Venta (COP)' -> 'fecha_de_venta_cop'"""
    n = unicodedata.normalize("NFKD", str(nombre).replace("﻿", ""))
    n = "".join(c for c in n if not unicodedata.combining(c))
    n = re.sub(r"[^0-9a-zA-Z]+", "_", n).strip("_").lower()
    if not n:
        n = "columna"
    if n[0].isdigit():
        n = "c_" + n
    return n


def normalizar_columnas(df):
    """Renombra todas las columnas con nombres seguros para SQL (sin tildes, espacios ni símbolos)."""
    nuevos, usados = [], {}
    for c in df.columns:
        base = normalizar_nombre(c)
        k = usados.get(base, 0)
        usados[base] = k + 1
        nuevos.append(base if k == 0 else f"{base}_{k + 1}")
    return df.toDF(*nuevos)


# =========================================================================== conversiones
_PATRONES_FECHA = [
    (r"^\d{4}-\d{1,2}-\d{1,2}$", "yyyy-M-d"),
    (r"^\d{4}/\d{1,2}/\d{1,2}$", "yyyy/M/d"),
    (r"^\d{1,2}/\d{1,2}/\d{4}$", "d/M/yyyy"),
    (r"^\d{1,2}-\d{1,2}-\d{4}$", "d-M-yyyy"),
    (r"^\d{1,2}\.\d{1,2}\.\d{4}$", "d.M.yyyy"),
    (r"^\d{4}-\d{1,2}-\d{1,2}[ T]\d{1,2}:\d{2}(:\d{2})?(\.\d+)?$", "timestamp"),
    (r"^\d{1,2}/\d{1,2}/\d{4} \d{1,2}:\d{2}(:\d{2})?$", "d/M/yyyy H:mm[:ss]"),
]


def _valores_muestra(df, col: str, n: int = 300) -> list[str]:
    from pyspark.sql import functions as F
    filas = df.select(F.col(col).cast("string").alias("v")).where(F.col(col).isNotNull()).limit(n).collect()
    return [r.v.strip() for r in filas if r.v and r.v.strip()]


def detectar_formato_fecha(valores: list[str]) -> str | None:
    if not valores:
        return None
    for patron, fmt in _PATRONES_FECHA:
        coincide = [v for v in valores if re.match(patron, v)]
        if len(coincide) >= 0.9 * len(valores):
            if fmt.startswith("d/M/yyyy") or fmt in ("d-M-yyyy", "d.M.yyyy"):
                sep = re.split(r"\d+", coincide[0])[1]
                partes = [v.split(" ")[0].split(sep) for v in coincide]
                # Si el segundo número supera 12, el formato es mes/día (estilo EE. UU.)
                if any(int(p[1]) > 12 for p in partes) and not any(int(p[0]) > 12 for p in partes):
                    fmt = fmt.replace("d" + sep + "M", "M" + sep + "d", 1)
            return fmt
    return None


def convertir_fecha(df, col: str, formato: str | None = None):
    """Convierte una columna de texto a fecha/timestamp. Los valores que no coinciden quedan nulos."""
    from pyspark.sql import functions as F
    tipo = dict(df.dtypes)[col]
    if tipo in ("date", "timestamp", "timestamp_ntz"):
        return df, tipo
    formato = formato or detectar_formato_fecha(_valores_muestra(df, col))
    if not formato:
        return df, None
    texto = F.trim(F.col(col).cast("string"))
    if formato == "timestamp":
        nueva = F.try_to_timestamp(texto)
        return df.withColumn(col, nueva), "timestamp"
    tiene_hora = "H" in formato
    nueva = F.try_to_timestamp(texto, F.lit(formato))
    return df.withColumn(col, nueva if tiene_hora else nueva.cast("date")), formato


_NUM_COMA = re.compile(r"^-?(\d{1,3}(\.\d{3})+|\d+)(,\d+)?$")


def convertir_decimal_coma(df, columnas: list[str] | None = None, umbral: float = 0.95):
    """Convierte columnas de texto con números en formato '1.234,56' a tipo double.
    Devuelve (df, lista_de_columnas_convertidas)."""
    from pyspark.sql import functions as F
    convertidas = []
    candidatas = columnas or [c for c, t in df.dtypes if t == "string"]
    for c in candidatas:
        vals = _valores_muestra(df, c, 200)
        if not vals:
            continue
        ok = [v for v in vals if _NUM_COMA.match(v)]
        if len(ok) >= umbral * len(vals) and any("," in v for v in ok):
            limpio = F.regexp_replace(F.regexp_replace(F.trim(F.col(c)), r"\.", ""), ",", ".")
            df = df.withColumn(c, limpio.try_cast("double"))
            convertidas.append(c)
    return df, convertidas


# =========================================================================== carga
def cargar_dataset(spark, ruta: str, formato: str = "auto", separador: str = "auto",
                   encabezado: bool = True, codificacion: str = "auto", decimal: str = "auto",
                   multilinea: bool = False, hoja_excel=0, columna_fecha: str | None = None,
                   formato_fecha: str | None = None, normalizar: bool = True, verbose: bool = True,
                   **opciones_extra):
    """Lee un archivo (o carpeta) de datos y devuelve un DataFrame listo para analizar.

    Devuelve (df, info) donde info describe lo que se detectó y aplicó.
    """
    from pyspark.sql import functions as F

    p = ruta_absoluta(ruta)
    if not p.exists():
        raise FileNotFoundError(f"No existe el archivo: {p}\n"
                                f"Archivos disponibles: {listar_datasets()}")
    fmt = detectar_formato(p) if formato in (None, "", "auto") else formato.lower()
    info = {"ruta": str(p), "formato": fmt}

    if fmt == "csv":
        muestra = _muestra_texto(p)
        cod = detectar_codificacion(muestra) if codificacion in (None, "", "auto") else codificacion
        texto = muestra.decode("utf-8" if cod.upper().startswith("UTF") else "cp1252", errors="ignore")
        sep = detectar_separador(texto) if separador in (None, "", "auto") else separador
        if p.suffix.lower() == ".tsv" and separador in (None, "", "auto"):
            sep = "\t"
        lector = (spark.read.option("header", encabezado).option("inferSchema", True)
                  .option("sep", sep).option("encoding", cod).option("multiLine", multilinea)
                  .option("quote", '"').option("escape", '"').option("mode", "PERMISSIVE"))
        for k, v in opciones_extra.items():
            lector = lector.option(k, v)
        df = lector.csv(str(p))
        info.update({"separador": sep, "codificacion": cod})
    elif fmt == "json":
        muestra = _muestra_texto(p, 2000).lstrip()
        es_arreglo = muestra.startswith(b"[")
        df = spark.read.option("multiLine", multilinea or es_arreglo).json(str(p))
        info["multilinea"] = multilinea or es_arreglo
    elif fmt in ("parquet", "orc"):
        df = spark.read.format(fmt).load(str(p))
    elif fmt == "excel":
        import pandas as pd
        pdf = pd.read_excel(p, sheet_name=hoja_excel)
        for c in pdf.columns:
            if pdf[c].dtype == object:
                pdf[c] = pdf[c].astype("string")
        destino = CARPETA_PROCESADO / "_desde_excel" / (p.stem + ".parquet")
        destino.parent.mkdir(parents=True, exist_ok=True)
        pdf.columns = [str(c) for c in pdf.columns]
        pdf.to_parquet(destino, index=False, coerce_timestamps="us", allow_truncated_timestamps=True)
        df = spark.read.parquet(str(destino))
        info["convertido_a"] = str(destino.relative_to(RAIZ))
    else:
        df = spark.read.format(fmt).load(str(p))

    if normalizar:
        originales = df.columns
        df = normalizar_columnas(df)
        info["renombradas"] = {o: n for o, n in zip(originales, df.columns) if o != n}

    # Números con coma decimal (habitual en archivos en español con separador ';')
    usar_coma = decimal == "," or (decimal in (None, "", "auto") and info.get("separador") == ";")
    if usar_coma:
        df, conv = convertir_decimal_coma(df)
        info["decimal_coma"] = conv

    # Fechas: la columna indicada y cualquier otra columna de texto que parezca fecha
    fechas = {}
    cols_fecha = [normalizar_nombre(columna_fecha)] if columna_fecha else []
    cols_fecha += [c for c, t in df.dtypes if t == "string" and c not in cols_fecha]
    for c in cols_fecha:
        if c not in df.columns:
            if verbose and columna_fecha and c == normalizar_nombre(columna_fecha):
                print(f"[AVISO] La columna de fecha '{columna_fecha}' no existe en el dataset.")
            continue
        fmt_c = formato_fecha if (columna_fecha and c == normalizar_nombre(columna_fecha)) else None
        df, aplicado = convertir_fecha(df, c, fmt_c)
        if aplicado and aplicado not in ("date",):
            fechas[c] = aplicado
    info["fechas"] = fechas

    if verbose:
        print(f"Archivo     : {Path(info['ruta']).name}  (formato {fmt})")
        if "separador" in info:
            print(f"Separador   : {info['separador']!r} | Codificación: {info['codificacion']}")
        if info.get("renombradas"):
            print(f"Columnas renombradas: {len(info['renombradas'])} (ver info['renombradas'])")
        if info.get("decimal_coma"):
            print(f"Coma decimal convertida en: {info['decimal_coma']}")
        if fechas:
            print(f"Fechas convertidas: {fechas}")
        print(f"Columnas    : {len(df.columns)}")
    return df, info


def cargar_desde_config(spark, version: str = "auto", cfg: dict | None = None, verbose: bool = True):
    """Carga el dataset activo definido en data/dataset_config.json.

    version = "original" -> archivo original
              "limpia"   -> versión Parquet generada en el cuaderno 04
              "auto"     -> limpia si existe; si no, original
    """
    cfg = cfg or leer_config()
    limpia = cfg.get("ruta_limpia")
    if version in ("limpia", "auto") and limpia and ruta_absoluta(limpia).exists():
        df = spark.read.parquet(str(ruta_absoluta(limpia)))
        if verbose:
            print(f"Dataset '{cfg['nombre']}' (versión limpia): {limpia}")
        return df, cfg
    if version == "limpia":
        print("[AVISO] Aún no existe la versión limpia (cuaderno 04). Se carga la versión original.")
    df, _ = cargar_dataset(
        spark, cfg["ruta"], formato=cfg.get("formato", "auto"), separador=cfg.get("separador", "auto"),
        encabezado=cfg.get("encabezado", True), codificacion=cfg.get("codificacion", "auto"),
        decimal=cfg.get("decimal", "auto"), multilinea=cfg.get("multilinea", False),
        hoja_excel=cfg.get("hoja_excel", 0), columna_fecha=cfg.get("columna_fecha"),
        formato_fecha=cfg.get("formato_fecha"), verbose=verbose)
    if verbose:
        print(f"Dataset '{cfg['nombre']}' (versión original)")
    return df, cfg


# =========================================================================== perfil
def clasificar_columnas(df, excluir: list[str] | None = None, max_categorias: int = 50,
                        total: int | None = None) -> dict:
    """Clasifica las columnas según su rol analítico.

    numericas      : tipos numéricos que no son identificadores
    categoricas    : texto o booleano con pocos valores distintos (<= max_categorias)
    fechas         : date / timestamp
    texto          : texto con muchos valores distintos
    identificadores: columnas excluidas, nombres tipo 'id' o valores casi únicos
    """
    from pyspark.sql import functions as F
    excluir = {normalizar_nombre(c) for c in (excluir or [])}
    tipos = dict(df.dtypes)
    total = total if total is not None else df.count()
    distintos = df.agg(*[F.approx_count_distinct(F.col(c), 0.05).alias(c) for c in df.columns]).first().asDict() \
        if df.columns else {}

    roles = {"numericas": [], "categoricas": [], "fechas": [], "texto": [], "identificadores": [], "otras": []}
    for c in df.columns:
        t = tipos[c].split("(")[0]
        d = distintos.get(c) or 0
        nombre_id = c == "id" or c.startswith("id_") or c.endswith("_id") or c.startswith("cod_") or c.startswith("codigo")
        casi_unico = total > 50 and d >= 0.95 * total
        if c in excluir or (nombre_id and (casi_unico or t == "string")):
            roles["identificadores"].append(c)
        elif t in ("date", "timestamp", "timestamp_ntz"):
            roles["fechas"].append(c)
        elif t in TIPOS_NUMERICOS:
            if casi_unico and t in ("integer", "long", "bigint", "int") and nombre_id:
                roles["identificadores"].append(c)
            elif d <= 2 and t in ("integer", "int", "long", "bigint"):
                roles["categoricas"].append(c)          # variables 0/1
            else:
                roles["numericas"].append(c)
        elif t in ("string", "boolean"):
            if d <= max_categorias:
                roles["categoricas"].append(c)
            elif casi_unico:
                roles["identificadores"].append(c)
            else:
                roles["texto"].append(c)
        else:
            roles["otras"].append(c)                    # arreglos, estructuras, mapas
    return roles


def perfil(df, roles: dict | None = None):
    """Devuelve un DataFrame de pandas con el perfil de cada columna."""
    import pandas as pd
    from pyspark.sql import functions as F

    total = df.count()
    roles = roles or clasificar_columnas(df, total=total)
    rol_de = {c: r for r, cols in roles.items() for c in cols}
    tipos = dict(df.dtypes)
    simples = [c for c in df.columns if not tipos[c].startswith(("array", "struct", "map"))]
    exprs = []
    for c in df.columns:
        exprs.append(F.sum(F.col(c).isNull().cast("int")).alias(f"{c}__nulos"))
        exprs.append(F.approx_count_distinct(F.col(c), 0.05).alias(f"{c}__dist"))
        if c in simples:
            exprs.append(F.min(F.col(c)).cast("string").alias(f"{c}__min"))
            exprs.append(F.max(F.col(c)).cast("string").alias(f"{c}__max"))
    r = df.agg(*exprs).first().asDict()
    filas = []
    for c in df.columns:
        nulos = r[f"{c}__nulos"] or 0
        filas.append({
            "columna": c, "tipo_spark": tipos[c], "rol": rol_de.get(c, "otras"),
            "nulos": nulos, "pct_nulos": round(100 * nulos / total, 2) if total else 0,
            "distintos_aprox": r[f"{c}__dist"],
            "minimo": (r.get(f"{c}__min") or "")[:30], "maximo": (r.get(f"{c}__max") or "")[:30],
        })
    return pd.DataFrame(filas)


def resumen_roles(roles: dict) -> None:
    for rol, cols in roles.items():
        if cols:
            print(f"{rol:<16}: {', '.join(cols)}")


def columna_objetivo(cfg: dict, df) -> str | None:
    obj = cfg.get("columna_objetivo")
    if not obj:
        return None
    obj = normalizar_nombre(obj)
    return obj if obj in df.columns else None


# =========================================================================== utilidades para los cuadernos
CLAVES_CARGA = ["ruta", "formato", "separador", "encabezado", "codificacion", "decimal",
                "multilinea", "hoja_excel", "columna_fecha", "formato_fecha"]


def parametros_carga(cfg: dict) -> dict:
    """Extrae de la configuración solo los parámetros que usa cargar_dataset()."""
    return {k: cfg[k] for k in CLAVES_CARGA if k in cfg}


def diagnosticar_carga(df, cfg: dict) -> list[str]:
    """Revisa problemas frecuentes de carga y devuelve una lista de avisos (vacía si todo está bien)."""
    avisos = []
    n = df.count()
    if n == 0:
        avisos.append("El dataset no tiene filas. Revisar la ruta, el separador o el encabezado.")
    if len(df.columns) == 1:
        avisos.append(f"Solo se detectó una columna ('{df.columns[0]}'): probablemente el separador "
                      "no es el correcto. Probar con 'separador': ';' o '\\t'.")
    genericas = [c for c in df.columns if re.fullmatch(r"_?c_?\d+", c)]
    if genericas and len(genericas) == len(df.columns):
        avisos.append("Las columnas tienen nombres genéricos (_c0, _c1...): el archivo no tiene "
                      "encabezado o 'encabezado' debe ser True.")
    if any(ch in "".join(map(str, df.limit(50).toPandas().astype(str).values.flatten())) for ch in "Ãâ€"):
        avisos.append("Se observan caracteres extraños (Ã, â€): la codificación no es la correcta. "
                      "Probar con 'codificacion': 'ISO-8859-1' o 'UTF-8'.")
    tipos = dict(df.dtypes)
    for c in [c for c, t in tipos.items() if t == "string"]:
        vals = _valores_muestra(df, c, 100)
        if vals and sum(bool(re.fullmatch(r"-?[\d.,]+", v)) for v in vals) >= 0.95 * len(vals):
            avisos.append(f"La columna '{c}' parece numérica pero quedó como texto: revisar 'decimal' "
                          "(',' si usa coma decimal) o la presencia de valores no numéricos.")
    for clave in ("columna_fecha", "columna_objetivo"):
        v = cfg.get(clave)
        if v and normalizar_nombre(v) not in df.columns:
            avisos.append(f"'{clave}' = '{v}' no existe. Columnas disponibles: {df.columns}")
    fecha = cfg.get("columna_fecha")
    if fecha and normalizar_nombre(fecha) in tipos and tipos[normalizar_nombre(fecha)] == "string":
        avisos.append(f"La columna de fecha '{fecha}' no pudo convertirse: indicar 'formato_fecha', "
                      "por ejemplo 'dd/MM/yyyy' o 'yyyy-MM-dd HH:mm:ss'.")
    for c in cfg.get("columnas_excluir") or []:
        if normalizar_nombre(c) not in df.columns:
            avisos.append(f"La columna a excluir '{c}' no existe en el dataset.")
    return avisos


def tamano_mb(ruta) -> float:
    """Tamaño en MB de un archivo o carpeta (sin archivos de control de Spark)."""
    p = ruta_absoluta(ruta)
    if p.is_file():
        return p.stat().st_size / 1024 ** 2
    return sum(f.stat().st_size for f in p.rglob("*")
               if f.is_file() and not f.name.endswith(".crc") and not f.name.startswith("_")) / 1024 ** 2
