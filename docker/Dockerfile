# Imagen del Taller de Apache Spark
# Una sola imagen sirve para: master, workers y JupyterLab.
FROM python:3.12-slim-bookworm

ARG SPARK_VERSION=4.3.0

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    JAVA_HOME=/usr/lib/jvm/default-java \
    PYSPARK_PYTHON=python3 \
    PYSPARK_DRIVER_PYTHON=python3

# Java 17 (requerido por Spark 4.x) + utilidades.
# default-jre-headless en Debian 12 = OpenJDK 17 y crea /usr/lib/jvm/default-java
# (funciona igual en amd64 y en ARM / Apple Silicon).
RUN apt-get update \
 && apt-get install -y --no-install-recommends default-jre-headless procps curl tini \
 && rm -rf /var/lib/apt/lists/*

# PySpark (incluye los binarios de Spark) + librerías del taller
RUN pip install --no-cache-dir \
      "pyspark==${SPARK_VERSION}" "pandas<3" pyarrow numpy matplotlib jupyterlab findspark

# SPARK_HOME apunta a la instalación de PySpark
ENV SPARK_HOME=/usr/local/lib/python3.12/site-packages/pyspark
ENV PATH="${SPARK_HOME}/bin:${PATH}"

# Usuario sin privilegios (mismo nombre que las imágenes de Jupyter)
RUN useradd -m -s /bin/bash jovyan && mkdir -p /home/jovyan/work && chown -R jovyan /home/jovyan
USER jovyan
WORKDIR /home/jovyan/work

EXPOSE 8888 4040 7077 8080 8081
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--ServerApp.token=bigdata"]
