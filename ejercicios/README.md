# Ejercicios del taller

Los ejercicios se resuelven sobre el **dataset propio** configurado en el cuaderno 01. Para
practicar antes, pueden resolverse con el dataset de ejemplo. Cada cuaderno incluye además
ejercicios propuestos al final.

Las soluciones de referencia ([`soluciones/soluciones.py`](soluciones/soluciones.py)) son
genéricas: se ejecutan sobre el dataset activo y eligen las columnas según su rol. Se recomienda
consultarlas solo después de intentar cada ejercicio.

```bash
python ejercicios/soluciones/soluciones.py
```

En los enunciados, `CAT1` y `CAT2` designan columnas categóricas del dataset, `NUM1` la variable
numérica principal y `FECHA` la fecha principal, tal como se definen en el cuaderno 05.

---

## Parte 1. Instalación y entorno (evidencias) — 15 %

1. Captura de la ejecución de `python scripts/verificar_instalacion.py` con todas las verificaciones en `[OK]`.
2. Captura de la Spark UI (pestaña *Jobs*) con al menos un trabajo completado.
3. (Opcional, 5 % adicional) Captura de la interfaz del maestro en Docker (http://localhost:8080) con dos *workers* en estado ALIVE.

Las capturas se guardan en `ejercicios/evidencias/`.

## Parte 2. Dataset propio y configuración — 15 %

**E0.** Seleccionar un dataset de al menos 5 000 filas y 6 columnas, con variables numéricas y
categóricas. Configurarlo en el cuaderno 01, documentar las opciones de lectura ajustadas y citar
su fuente en formato APA.

## Parte 3. RDD — 10 %

**E1.** Con la API de RDD:

- a) Contar los valores distintos de `CAT1`.
- b) Si el dataset tiene una columna de texto, aplicar WordCount sobre ella; en caso contrario, sobre `data/ejemplo/texto_bigdata.txt`. Obtener las cinco letras iniciales más frecuentes.

## Parte 4. DataFrames — 20 %

**E2.** Construir una tabla dinámica de la suma de `NUM1` con los meses (o los valores de `CAT2`) en filas y los valores de `CAT1` en columnas. Sugerencia: `groupBy(...).pivot(...)`.

**E3.** Identificar los diez grupos (`CAT1`, `CAT2`) con mayor suma de `NUM1`.

**E4.** Elaborar un reporte de calidad: nulos por columna, valores negativos en columnas numéricas y filas duplicadas.

## Parte 5. Spark SQL — 20 %

**E5.** Para cada valor de `CAT1`, determinar el valor de `CAT2` con mayor suma de `NUM1` con `ROW_NUMBER()`.

**E6.** Si el dataset tiene fecha, calcular la variación porcentual mensual de `NUM1` con `LAG()`. Si no la tiene, calcular la participación porcentual de cada valor de `CAT1` con `SUM() OVER ()`.

## Parte 6. ETL y rendimiento — 20 %

**E7.** Comparar CSV y Parquet con el dataset propio:

- a) Tiempo de una agregación en cada formato.
- b) Tamaño en disco de cada formato.
- c) Explicar, en un párrafo de tres a cinco líneas y con al menos una fuente citada en formato APA, por qué Parquet resulta más eficiente para consultas analíticas (véase [docs/referencias.md](../docs/referencias.md)).

---

## Rúbrica de evaluación

| Criterio | Excelente (100 %) | Aceptable (60 %) | Insuficiente (0 %) |
|----------|-------------------|------------------|--------------------|
| Instalación | Evidencias completas y legibles | Falta una evidencia | Sin evidencias |
| Dataset y configuración | Dataset pertinente, carga validada y fuente citada en APA | Carga correcta sin justificación o sin cita | Se usa solo el dataset de ejemplo |
| Correctitud | Resultados correctos en todos los ejercicios | Errores menores | Resultados incorrectos o ausentes |
| Uso de Spark | Transformaciones nativas; sin `collect()` innecesarios | Uso ocasional e injustificado de `collect()` o UDF | Procesamiento en pandas o Python puro |
| Calidad del código | Cuaderno ejecutable de principio a fin, ordenado y comentado | Funcional pero desordenado | No se ejecuta |
| Análisis | Interpretación argumentada con fuentes en APA | Interpretación superficial | Sin interpretación |

## Entrega

1. Realizar un *fork* del repositorio.
2. Completar `notebooks/07_proyecto_final.ipynb` con el dataset propio y agregar `ejercicios/evidencias/`.
3. Ejecutar `git add . && git commit -m "Proyecto taller Spark - <nombre>" && git push`.
4. Enviar el enlace del *fork* al docente.
