import json
import re
import unicodedata
from pathlib import Path
import numpy as np
import pandas as pd


def limpiar_texto(valor):
    if pd.isna(valor):
        return None
    if not isinstance(valor, str):
        valor = str(valor)
    texto = re.sub(r"[\r\n\t]+", " ", valor)
    texto = re.sub(r"\s{2,}", " ", texto).strip()
    return texto if texto else None


def normalizar_nombre_columna(col):
    col = limpiar_texto(col) or ""
    col = unicodedata.normalize("NFKD", col).encode("ascii", "ignore").decode("utf-8")
    col = col.lower()
    col = re.sub(r"[^a-z0-9]+", "_", col)
    col = re.sub(r"_+", "_", col).strip("_")
    return col


def parsear_numero(serie):
    limpia = (
        serie.astype(str)
        .str.replace("\xa0", "", regex=False)
        .str.strip()
        .str.replace(",", ".", regex=False)
        .replace({"": np.nan, "nan": np.nan, "None": np.nan, "-": np.nan, "..": np.nan})
    )
    num = pd.to_numeric(limpia, errors="coerce")
    no_nulos = num.dropna()
    if len(no_nulos) > 0 and no_nulos.apply(lambda x: float(x).is_integer()).all():
        return num.astype("Int64")
    return num.astype(float)


def exportar_y_validar_json(df, ruta_json):
    registros = df.where(pd.notna(df), None).to_dict(orient="records")
    ruta = Path(ruta_json)
    with ruta.open("w", encoding="utf-8") as f:
        json.dump(registros, f, ensure_ascii=False, indent=2)

    with ruta.open("r", encoding="utf-8") as f:
        cargado = json.load(f)

    assert isinstance(cargado, list) and len(cargado) == len(df)


def limpiar_smex99(ruta_xls="data/smex99.xls"):
    xls = pd.ExcelFile(ruta_xls)
    df_raw = pd.read_excel(xls, sheet_name="Datos", header=9)

    cabecera_real = [limpiar_texto(c) or f"col_{i}" for i, c in enumerate(df_raw.iloc[0])]
    df = df_raw.iloc[1:].copy()
    df.columns = cabecera_real
    df = df.dropna(how="all").copy()
    df.columns = [normalizar_nombre_columna(c) for c in df.columns]

    df = df[df["codmun"].notna()].copy()
    df["cod_mun"] = (
        df["codmun"]
        .astype(str)
        .str.replace(r"\.0$", "", regex=True)
        .str.strip()
        .str.zfill(5)
    )
    df["provincia"] = df["provincia"].apply(limpiar_texto)
    df["municipio"] = df["municipio"].apply(limpiar_texto)

    col_coord = "coordenadas_del_nucleo_principal_grados_2022"
    if col_coord in df.columns:
        coords = df[col_coord].astype(str).str.extract(
            r"^\s*([-+]?\d+(?:[.,]\d+)?)\s*,\s*([-+]?\d+(?:[.,]\d+)?)\s*$"
        )
        df["latitud_nucleo_2022"] = parsear_numero(coords[0])
        df["longitud_nucleo_2022"] = parsear_numero(coords[1])

    columnas_objetivo = [
        "cod_mun",
        "provincia",
        "municipio",
        "extension_superficial_km2_2019",
        "perimetro_m_2019",
        "altitud_sobre_el_nivel_del_mar_m_2019",
        "latitud_nucleo_2022",
        "longitud_nucleo_2022",
        "distancia_a_la_capital_km_2019",
        "poblacion_total_2025",
        "poblacion_hombres_2025",
        "poblacion_mujeres_2025",
        "edad_media_2025",
        "hoteles_2024",
        "hostales_y_pensiones_2024",
        "plazas_en_hoteles_2024",
        "plazas_en_hostales_y_pensiones_2024",
        "renta_bruta_media_2023",
        "renta_disponible_media_2023",
        "tasa_municipal_de_desempleo_2024",
    ]
    cols_presentes = [c for c in columnas_objetivo if c in df.columns]
    df_limpio = df[cols_presentes].copy()

    renombres = {
        "extension_superficial_km2_2019": "extension_km2_2019",
        "altitud_sobre_el_nivel_del_mar_m_2019": "altitud_m_2019",
        "distancia_a_la_capital_km_2019": "distancia_capital_km_2019",
        "hostales_y_pensiones_2024": "hostales_pensiones_2024",
        "plazas_en_hoteles_2024": "plazas_hoteles_2024",
        "plazas_en_hostales_y_pensiones_2024": "plazas_hostales_pensiones_2024",
        "tasa_municipal_de_desempleo_2024": "tasa_desempleo_pct_2024",
    }
    df_limpio = df_limpio.rename(columns=renombres)

    cols_texto = {"cod_mun", "provincia", "municipio"}
    for col in df_limpio.columns:
        if col not in cols_texto:
            df_limpio[col] = parsear_numero(df_limpio[col])

    return df_limpio.drop_duplicates(subset=["cod_mun"], keep="first").reset_index(drop=True)


def limpiar_interes_turistico(ruta_xls="data/dataset_interes_turistico_23122025.xls"):
    xls = pd.ExcelFile(ruta_xls)
    df = pd.read_excel(xls, sheet_name=xls.sheet_names[0])
    df.columns = [normalizar_nombre_columna(c) for c in df.columns]

    for col in df.select_dtypes(include=["object", "string"]).columns:
        df[col] = df[col].apply(limpiar_texto)

    if "provincia" in df.columns:
        df["provincia"] = df["provincia"].apply(
            lambda x: re.sub(r"\s*,\s*", ", ", x) if isinstance(x, str) else x
        )

    for col_cat in ["tipo", "ambito"]:
        if col_cat in df.columns:
            df[col_cat] = df[col_cat].apply(
                lambda x: x.capitalize() if isinstance(x, str) else x
            )

    if "fecha_de_resolucion" in df.columns:
        fechas = pd.to_datetime(df["fecha_de_resolucion"], errors="coerce")
        df["anio_resolucion"] = fechas.dt.year.astype("Int64")
        df["fecha_resolucion"] = fechas.dt.strftime("%Y-%m-%d")
        df = df.drop(columns=["fecha_de_resolucion"])

    df = df.rename(columns={"declaracion_de_interes_turistico": "declaracion_interes_turistico"})
    return df.drop_duplicates().reset_index(drop=True)


def limpiar_csv_act01(ruta_csv="data/data_act_01.csv"):
    df = pd.read_csv(ruta_csv, sep=";", encoding="utf-8")
    df.columns = [normalizar_nombre_columna(c) for c in df.columns]

    for col in df.select_dtypes(include=["object", "string"]).columns:
        df[col] = df[col].apply(limpiar_texto)

    cols_vacias = [c for c in df.columns if df[c].isna().all()]
    if cols_vacias:
        df = df.drop(columns=cols_vacias)

    if "offense_date" in df.columns:
        df["offense_date"] = pd.to_datetime(df["offense_date"], errors="coerce").dt.strftime("%Y-%m-%d")

    if "call_datetime" in df.columns:
        dt_call = pd.to_datetime(df["call_datetime"], errors="coerce")
        df["call_datetime"] = dt_call.dt.strftime("%Y-%m-%dT%H:%M:%S")
        df["anio_llamada"] = dt_call.dt.year.astype("Int64")

    if "call_time" in df.columns:
        hora_parseada = pd.to_datetime(df["call_time"], format="%H:%M", errors="coerce")
        df["call_time"] = np.where(
            hora_parseada.notna(),
            hora_parseada.dt.strftime("%H:%M"),
            df["call_time"],
        )

    if "range" in df.columns:
        df = df.rename(columns={"range": "range_val"})

    if "crime_id" in df.columns:
        df = df.drop_duplicates(subset=["crime_id"], keep="first")

    return df.reset_index(drop=True)


if __name__ == "__main__":
    df_smex = limpiar_smex99("data/smex99.xls")
    df_tur = limpiar_interes_turistico("data/dataset_interes_turistico_23122025.xls")
    df_csv = limpiar_csv_act01("data/data_act_01.csv")

    exportar_y_validar_json(df_smex, "data/smex99_limpio.json")
    exportar_y_validar_json(df_tur, "data/interes_turistico_limpio.json")
    exportar_y_validar_json(df_csv, "data/data_act_01_limpio.json")