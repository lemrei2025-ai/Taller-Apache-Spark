# Ejercicios del taller

Los ejercicios se resuelven en un cuaderno propio, `ejercicios/mi_solucion.ipynb`, a partir de los
datos de la carpeta `data/`. Las soluciones de referencia se encuentran en
[`soluciones/soluciones.py`](soluciones/soluciones.py); se recomienda consultarlas únicamente
después de intentar cada ejercicio.

---

## Parte 1. Instalación (evidencias) — 20 %

1. Captura de pantalla de la ejecución de `python scripts/verificar_instalacion.py`, con todas las verificaciones en estado `[OK]`.
2. Captura de la Spark UI (http://localhost:4040) en la pestaña *Jobs*, con al menos un job completado.
3. (Opcional, 5 % adicional) Captura de la interfaz del maestro en Docker (http://localhost:8080) con dos *workers* en estado ALIVE y una aplicación en ejecución.

Las capturas se almacenan en `ejercicios/evidencias/`.

## Parte 2. RDD — 15 %

**E1.** A partir de `data/texto_bigdata.txt`, y empleando únicamente la API de RDD:

- a) Contar el número total de palabras y el número de palabras distintas.
- b) Obtener las cinco letras iniciales más frecuentes.

## Parte 3. DataFrames — 25 %

**E2.** Calcular el ingreso total por mes y canal, y presentarlo como tabla dinámica (meses en filas
y canales en columnas). Sugerencia: `groupBy("mes").pivot("canal")`.

**E3.** Identificar los diez clientes con mayor gasto, con su nombre, ciudad, segmento, número de
compras y gasto total.

**E4.** Elaborar un reporte de calidad de datos que indique cuántos registros presentan cantidad
nula, cantidad negativa o canal nulo.

## Parte 4. Spark SQL — 20 %

**E5.** Determinar, para cada región, la categoría con mayores ingresos mediante `ROW_NUMBER()`.

**E6.** Calcular el crecimiento porcentual de los ingresos de cada mes respecto al anterior mediante `LAG()`.

## Parte 5. ETL y rendimiento — 20 %

**E7.** Generar un conjunto de datos de mayor tamaño y comparar formatos de almacenamiento:

```bash
python scripts/generar_datos.py --ventas 2000000
```

- a) Medir el tiempo de una agregación leyendo los datos en CSV y en Parquet.
- b) Reportar el tamaño en disco de cada formato.
- c) Explicar, en un párrafo de tres a cinco líneas y con apoyo en al menos una fuente citada en formato APA, por qué Parquet resulta más eficiente para consultas analíticas (véase [docs/referencias.md](../docs/referencias.md)).

Al finalizar se regeneran los datos originales con `python scripts/generar_datos.py`.

---

## Rúbrica de evaluación

| Criterio | Excelente (100 %) | Aceptable (60 %) | Insuficiente (0 %) |
|----------|-------------------|------------------|--------------------|
| Instalación | Evidencias completas y legibles | Falta una evidencia | Sin evidencias |
| Correctitud | Resultados correctos en todos los ejercicios | Errores menores | Resultados incorrectos o ausentes |
| Uso de Spark | Emplea transformaciones nativas y evita `collect()` innecesarios | Uso ocasional e injustificado de `collect()` o de UDF | Procesa los datos con pandas o Python puro |
| Calidad del código | Código limpio, comentado y con celdas en orden | Código funcional pero desordenado | El código no se ejecuta |
| Análisis | Interpreta los resultados con argumentos y fuentes citadas en APA | Interpretación superficial o sin fuentes | Sin interpretación |

## Entrega

1. Realizar un *fork* del repositorio.
2. Agregar `ejercicios/mi_solucion.ipynb` y la carpeta `ejercicios/evidencias/`.
3. Ejecutar `git add . && git commit -m "Solución taller Spark - <nombre>" && git push`.
4. Enviar el enlace del *fork* al docente.
