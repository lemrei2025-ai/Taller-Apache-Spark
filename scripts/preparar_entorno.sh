#!/usr/bin/env bash
# =============================================================================
#  Preparación del entorno del taller - Linux y macOS
#
#  1. Crea el entorno virtual .venv   2. Actualiza pip   3. Instala dependencias
#  4. Detecta Java 17/21 y corrige JAVA_HOME (instala Java 17 si no existe)
#  5. Ejecuta la verificación completa
#
#  Uso, desde la carpeta raíz del taller:   bash scripts/preparar_entorno.sh
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")/.."

PY=python3
command -v python3 >/dev/null || PY=python

[ -x .venv/bin/python ] || { echo "==> Creando entorno virtual .venv"; "$PY" -m venv .venv; }
echo "==> Actualizando pip";        .venv/bin/python -m pip install --upgrade pip --quiet
echo "==> Instalando dependencias"; .venv/bin/python -m pip install -r requirements.txt --quiet --disable-pip-version-check
echo "==> Configurando Java";       .venv/bin/python scripts/configurar_java.py --instalar

# Aplicar en este proceso el JAVA_HOME elegido
JH="$(.venv/bin/python -c 'import sys; sys.path.insert(0,"scripts"); import configurar_java as c; h=c.asegurar_java(silencioso=True); print(h or "")' | tail -n 1)"
[ -n "$JH" ] && export JAVA_HOME="$JH"

echo "==> Verificando el entorno";  .venv/bin/python scripts/verificar_instalacion.py --solo-sesion

echo
echo "Entorno listo. Para trabajar:"
echo "   source .venv/bin/activate"
echo "   jupyter lab"
