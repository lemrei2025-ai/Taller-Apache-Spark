#!/usr/bin/env bash
# =============================================================================
#  Instalación automática de Apache Spark - Linux (Ubuntu/Debian) y macOS
#  Taller de Big Data
#
#  Uso:
#     bash scripts/instalar_spark_linux.sh            # instala Spark 4.3.0
#     SPARK_VERSION=4.2.1 bash scripts/instalar_spark_linux.sh
# =============================================================================
set -euo pipefail

SPARK_VERSION="${SPARK_VERSION:-4.3.0}"
INSTALL_DIR="${INSTALL_DIR:-/opt/spark}"
PKG="spark-${SPARK_VERSION}-bin-hadoop3"
URL_MAIN="https://dlcdn.apache.org/spark/spark-${SPARK_VERSION}/${PKG}.tgz"
URL_ARCHIVE="https://archive.apache.org/dist/spark/spark-${SPARK_VERSION}/${PKG}.tgz"

verde() { printf "\033[32m%s\033[0m\n" "$*"; }
amarillo() { printf "\033[33m%s\033[0m\n" "$*"; }
rojo() { printf "\033[31m%s\033[0m\n" "$*"; }

OS="$(uname -s)"
verde "==> Sistema detectado: ${OS}"

# ---------------------------------------------------------------- 1. Java
java_major() { java -version 2>&1 | awk -F[\".] '/version/ {print ($2=="1")?$3:$2}'; }

if ! command -v java >/dev/null 2>&1 || [ "$(java_major)" -lt 17 ]; then
  amarillo "==> Instalando Java 17..."
  if [ "$OS" = "Linux" ]; then
    sudo apt-get update -y
    sudo apt-get install -y openjdk-17-jdk
  elif [ "$OS" = "Darwin" ]; then
    command -v brew >/dev/null || { rojo "Se requiere Homebrew: https://brew.sh"; exit 1; }
    brew install openjdk@17
    sudo ln -sfn "$(brew --prefix)/opt/openjdk@17/libexec/openjdk.jdk" \
      /Library/Java/JavaVirtualMachines/openjdk-17.jdk
  fi
else
  verde "==> Java $(java_major) ya instalado"
fi

# ---------------------------------------------------------------- 2. Python
if [ "$OS" = "Linux" ]; then
  sudo apt-get install -y python3 python3-pip python3-venv wget curl
fi

# ---------------------------------------------------------------- 3. Spark
if [ -x "${INSTALL_DIR}/bin/spark-submit" ]; then
  verde "==> Spark ya existe en ${INSTALL_DIR} (se omite la descarga)"
else
  TMP="$(mktemp -d)"
  verde "==> Descargando ${PKG}..."
  if ! curl -fL --progress-bar -o "${TMP}/${PKG}.tgz" "${URL_MAIN}"; then
    amarillo "    Mirror principal no disponible, usando archive.apache.org"
    curl -fL --progress-bar -o "${TMP}/${PKG}.tgz" "${URL_ARCHIVE}"
  fi
  verde "==> Descomprimiendo en ${INSTALL_DIR}"
  tar -xzf "${TMP}/${PKG}.tgz" -C "${TMP}"
  sudo rm -rf "${INSTALL_DIR}"
  sudo mv "${TMP}/${PKG}" "${INSTALL_DIR}"
  sudo chown -R "$(id -un)" "${INSTALL_DIR}"
  rm -rf "${TMP}"
fi

# ---------------------------------------------------------------- 4. Variables
if [ "$OS" = "Darwin" ]; then RC="$HOME/.zshrc"; else RC="$HOME/.bashrc"; fi

if ! grep -q "# ---- Apache Spark ----" "$RC" 2>/dev/null; then
  verde "==> Agregando variables de entorno a ${RC}"
  if [ "$OS" = "Darwin" ]; then
    JH='$(/usr/libexec/java_home -v 17)'
  else
    JH='$(dirname $(dirname $(readlink -f $(which java))))'
  fi
  cat >> "$RC" <<EOF

# ---- Apache Spark ----
export JAVA_HOME=${JH}
export SPARK_HOME=${INSTALL_DIR}
export PATH=\$PATH:\$SPARK_HOME/bin:\$SPARK_HOME/sbin
export PYSPARK_PYTHON=python3
EOF
fi

# ---------------------------------------------------------------- 5. Prueba
export SPARK_HOME="${INSTALL_DIR}"
export PATH="$PATH:$SPARK_HOME/bin"
verde "==> Probando instalación..."
spark-submit --version 2>&1 | grep -i "version" | head -n 2

verde ""
verde "[OK] Instalación completada."
echo "   Ejecutar: source ${RC}"
echo "   Después:  pyspark   (shell)   |   spark-submit \$SPARK_HOME/examples/src/main/python/pi.py 10"
