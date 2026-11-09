#!/usr/bin/env python3
"""
Perfil de calidad de cualquier dataset, ejecutable con spark-submit.

Ejecutar desde la raíz del repositorio:
  spark-submit src/perfil_dataset.py                                  # dataset configurado
  spark-submit src/perfil_dataset.py --ruta data/mis_datos/archivo.csv
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
from taller_spark import (cargar_dataset, clasificar_columnas, iniciar_spark, leer_config,  # noqa: E402
                          parametros_carga, perfil, resumen_roles)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ruta", help="archivo de entrada (por defecto, el de la configuración)")
    args = ap.parse_args()
    cfg = leer_config()
    if args.ruta:
        cfg.update({"ruta": args.ruta, "columna_fecha": None, "columnas_excluir": []})

    spark = iniciar_spark("Perfil_Dataset")
    df, _ = cargar_dataset(spark, **parametros_carga(cfg))
    roles = clasificar_columnas(df, excluir=cfg.get("columnas_excluir"), max_categorias=cfg.get("max_categorias", 50))
    print(f"\nFilas: {df.count():,} | Columnas: {len(df.columns)}\n")
    resumen_roles(roles)
    print()
    print(perfil(df, roles).to_string(index=False))
    spark.stop()


if __name__ == "__main__":
    main()
