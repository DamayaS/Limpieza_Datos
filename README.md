# Limpieza, Normalización y Modelado JSON de Datos Heterogéneos

Proyecto de diagnóstico de calidad, saneamiento y transformación de datos desarrollado con **Python** y **Pandas**. El objetivo es convertir tres conjuntos de datos heterogéneos (`XLS` y `CSV`) en estructuras **JSON** limpias, normalizadas y sin redundancias, aplicando un marco teórico riguroso y una metodología replicable.

---

## Conjuntos de Datos (Datasets)

Se han procesado tres fuentes de datos con distintos niveles de complejidad estructural:

| ID | Nombre del Dataset | Fuente | Formato | Registros | Variables | Cobertura |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: |
| **DS1** | Sistema de Información Municipal de Andalucía (SIMA) | Open Data Junta de Andalucía | `XLS` | 785 | 124 | 2017–2025 |
| **DS2** | Declaraciones de Interés Turístico de Andalucía | Open Data Junta de Andalucía | `XLS` | 184 | 10 | 1965–2025 |
| **DS3** | Incidencias Policiales – San Francisco (CA) | Dataset académico | `CSV` | 10.051 | 12 | 2016 |

---

## Diagnóstico y Tratamiento de Calidad

Los problemas detectados se clasificaron según las dimensiones de calidad de datos de **Jarke et al. (1998)** y se resolvieron mediante reglas programáticas:

* **Valores enmascarados en variables numéricas (`DS1`):** Detección de 5.543 celdas con caracteres `'-'` (no disponible) y `'*'` (secreto estadístico). Se imputaron a `0` y `null` respectivamente para habilitar el tipado numérico (`int`/`float`).
* **Violación de atomicidad (`DS1`):** Separación de coordenadas geográficas almacenadas como texto compuesto (`"37.141, -2.78"`) en dos variables numéricas independientes: `latitud` y `longitud`.
* **Inconsistencia por espacios en blanco (`DS2`, `DS1`):** Eliminación de espacios iniciales y finales (`.strip()`) en 309 registros y cabeceras (ej. `'Internacional '` vs `'Internacional'`) que fragmentaban las agrupaciones categóricas.
* **Nombres de variables no normalizados (`DS1`, `DS2`):** Estandarización de cabeceras largas y con caracteres especiales a formato **`snake_case`** limpio, conservando los sufijos anuales.
* **Redundancia temporal (`DS3`):** Consolidación de `OffenseDate` y `CallTime` en un único campo `call_datetime` bajo el estándar **ISO 8601** (`YYYY-MM-DDTHH:MM:SS`), reduciendo variables sin pérdida de información.
* **Duplicidad de clave primaria (`DS3`):** Identificación y depuración de 4 `CrimeId` duplicados (6 registros afectados) para garantizar la integridad referencial.

---

## Metodología Replicable

El proceso se estructura en una secuencia de **5 fases** automatizables con `pandas`:

1. **Inspección inicial:** Detección de *encoding*, delimitadores, dimensiones (`shape`), tipos de dato (`dtypes`) y porcentaje de completitud.
2. **Limpieza estructural:** Normalización de columnas a `snake_case`, limpieza de espacios en cadenas de texto y eliminación de variables 100% nulas o redundantes.
3. **Normalización de tipos:** Reemplazo de valores centinela, conversión numérica controlada (`errors='coerce'`) y estandarización de fechas a **ISO 8601**.
4. **Validación de consistencia:** Deduplicación de claves primarias y descomposición de atributos compuestos/multivaluados en estructuras atómicas.
5. **Modelado y exportación JSON:** Diseño de documentos embebidos (arrays para campos multivaluados y objetos anidados para métricas compuestas) con validación de sintaxis (`json.load()`).

---

## Estructura del Repositorio

```text
├── data/
│   ├── raw/            # Datasets originales (o muestras reducidas)
│   └── processed/      # Ficheros JSON limpios y validados
├── notebooks/          # Análisis exploratorio y pruebas de limpieza
├── src/                # Scripts de Python con las funciones de transformación
├── docs/               # Informe técnico completo (PDF)
└── README.md
```

---

## Tecnologías Utilizadas

* **Python 3**
* **Pandas** (manipulación, limpieza y transformación de DataFrames)
* **Regex / Unidecode** (normalización de texto y cabeceras)
* **JSON** (validación y serialización estándar RFC 7159)
