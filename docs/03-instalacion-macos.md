# 3. Instalación de Apache Spark en macOS

El procedimiento aplica a equipos Mac con procesador Intel y Apple Silicon (M1 a M4).

## Paso 1. Instalación de Homebrew

Si el gestor de paquetes Homebrew no está instalado, se instala con:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

## Paso 2. Instalación de Java 17 y Python

```bash
brew install openjdk@17 python@3.12
sudo ln -sfn $(brew --prefix)/opt/openjdk@17/libexec/openjdk.jdk \
     /Library/Java/JavaVirtualMachines/openjdk-17.jdk
```

Verificación:

```bash
java -version
python3 --version
```

## Paso 3. Instalación de Spark

### Opción A. Homebrew

```bash
brew install apache-spark
```

Homebrew instala la versión más reciente disponible en su repositorio. Esta se comprueba con
`spark-submit --version`; si no corresponde a la 4.3.0, debe ajustarse la versión de `pyspark` en
`requirements.txt` para que ambas coincidan, o bien seguirse la opción B.

### Opción B. Descarga manual (versión exacta)

```bash
SPARK_VERSION=4.3.0
curl -O https://dlcdn.apache.org/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop3.tgz
tar -xzf spark-${SPARK_VERSION}-bin-hadoop3.tgz
sudo mv spark-${SPARK_VERSION}-bin-hadoop3 /opt/spark
```

El script `bash scripts/instalar_spark_linux.sh` también es compatible con macOS.

## Paso 4. Variables de entorno (zsh)

```bash
cat >> ~/.zshrc <<'EOF'

# ---- Apache Spark ----
export JAVA_HOME=$(/usr/libexec/java_home -v 17)
export SPARK_HOME=/opt/spark          # con Homebrew: $(brew --prefix apache-spark)/libexec
export PATH=$PATH:$SPARK_HOME/bin:$SPARK_HOME/sbin
export PYSPARK_PYTHON=python3
EOF
source ~/.zshrc
```

## Paso 5. Verificación y preparación del taller

```bash
spark-submit --version
git clone https://github.com/<usuario>/taller-apache-spark.git
cd taller-apache-spark
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/verificar_instalacion.py
```

## Problemas frecuentes

| Problema | Solución |
|----------|----------|
| `Unable to locate a Java Runtime` | Repetir el enlace simbólico del paso 2 |
| `Service 'sparkDriver' could not bind` | Ejecutar `export SPARK_LOCAL_IP=127.0.0.1` |
| Aviso del cortafuegos al iniciar Spark | Permitir las conexiones entrantes para Java |

## Referencias

The Apache Software Foundation. (2026a). *Spark overview* (Versión 4.3.0) [Documentación técnica]. https://spark.apache.org/docs/latest/
