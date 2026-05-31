from pathlib import Path
from datetime import datetime
import pandas as pd
import shutil
import csv
import json

BASE_DIR = Path(__file__).resolve().parent.parent

DATALAKE_DIR = BASE_DIR / "DataLake"
RAW_CSV_DIR = DATALAKE_DIR / "raw" / "csv"
RAW_EXCEL_DIR = DATALAKE_DIR / "raw" / "excel"
RAW_JSON_DIR = DATALAKE_DIR / "raw" / "json"
SILVER_DIR = DATALAKE_DIR / "silver"
REJECTED_DIR = DATALAKE_DIR / "rejected"
LOGS_DIR = BASE_DIR / "logs"
LOG_FILE = LOGS_DIR / "datalake_log.csv"

def escribir_log(nivel, proceso, archivo, accion, estado, detalle):
    existe = LOG_FILE.exists()

    with open(LOG_FILE, mode="a", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)

        if not existe:
            writer.writerow([
                "fecha_hora",
                "nivel",
                "proceso",
                "archivo",
                "accion",
                "estado",
                "detalle"
            ])

        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            nivel,
            proceso,
            archivo,
            accion,
            estado,
            detalle
        ])

def normalizar_columnas(df):
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
    )
    return df

def limpiar_texto(df):
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].astype(str).str.strip()
    return df

def limpiar_dataframe(df):
    filas_iniciales = len(df)

    df = df.dropna(how="all")
    filas_sin_vacias = len(df)

    df = normalizar_columnas(df)
    df = limpiar_texto(df)

    antes_duplicados = len(df)
    df = df.drop_duplicates()
    duplicados_eliminados = antes_duplicados - len(df)

    detalle = (
        f"Filas iniciales: {filas_iniciales}, "
        f"sin vacías: {filas_sin_vacias}, "
        f"duplicados eliminados: {duplicados_eliminados}, "
        f"filas finales: {len(df)}"
    )

    return df, detalle

def nombre_salida(nombre_archivo):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{Path(nombre_archivo).stem}_clean_{timestamp}.csv"

def procesar_csv():
    for archivo in RAW_CSV_DIR.glob("*.csv"):
        try:
            df = pd.read_csv(archivo)

            if df.empty:
                raise ValueError("Archivo CSV vacío o sin datos válidos")

            df_limpio, detalle = limpiar_dataframe(df)

            salida = SILVER_DIR / nombre_salida(archivo.name)
            df_limpio.to_csv(salida, index=False, encoding="utf-8")

            archivo.unlink()

            escribir_log(
                "INFO",
                "LIMPIEZA_RAW",
                archivo.name,
                "CSV limpiado y eliminado de raw",
                "Éxito",
                detalle
            )

        except Exception as e:
            try:
                destino = REJECTED_DIR / archivo.name
                shutil.move(str(archivo), str(destino))
                escribir_log(
                    "ERROR",
                    "LIMPIEZA_RAW",
                    archivo.name,
                    "Error procesando CSV; movido a rejected",
                    "Error",
                    str(e)
                )
            except Exception as move_error:
                escribir_log(
                    "ERROR",
                    "LIMPIEZA_RAW",
                    archivo.name,
                    "Error doble en CSV",
                    "Error",
                    f"Procesamiento: {e} | Movimiento a rejected: {move_error}"
                )

def procesar_excel():
    archivos_excel = list(RAW_EXCEL_DIR.glob("*.xlsx")) + list(RAW_EXCEL_DIR.glob("*.xls"))

    for archivo in archivos_excel:
        try:
            df = pd.read_excel(archivo)

            if df.empty:
                raise ValueError("Archivo Excel vacío o sin datos válidos")

            df_limpio, detalle = limpiar_dataframe(df)

            salida = SILVER_DIR / nombre_salida(archivo.name)
            df_limpio.to_csv(salida, index=False, encoding="utf-8")

            archivo.unlink()

            escribir_log(
                "INFO",
                "LIMPIEZA_RAW",
                archivo.name,
                "Excel limpiado y eliminado de raw",
                "Éxito",
                detalle
            )

        except Exception as e:
            try:
                destino = REJECTED_DIR / archivo.name
                shutil.move(str(archivo), str(destino))
                escribir_log(
                    "ERROR",
                    "LIMPIEZA_RAW",
                    archivo.name,
                    "Error procesando Excel; movido a rejected",
                    "Error",
                    str(e)
                )
            except Exception as move_error:
                escribir_log(
                    "ERROR",
                    "LIMPIEZA_RAW",
                    archivo.name,
                    "Error doble en Excel",
                    "Error",
                    f"Procesamiento: {e} | Movimiento a rejected: {move_error}"
                )

def procesar_json():
    for archivo in RAW_JSON_DIR.glob("*.json"):
        try:
            with open(archivo, "r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, dict):
                df = pd.json_normalize(data)
            elif isinstance(data, list):
                df = pd.DataFrame(data)
            else:
                raise ValueError("Estructura JSON no soportada")

            if df.empty:
                raise ValueError("Archivo JSON vacío o sin datos válidos")

            df_limpio, detalle = limpiar_dataframe(df)

            salida = SILVER_DIR / nombre_salida(archivo.name)
            df_limpio.to_csv(salida, index=False, encoding="utf-8")

            archivo.unlink()

            escribir_log(
                "INFO",
                "LIMPIEZA_RAW",
                archivo.name,
                "JSON limpiado y eliminado de raw",
                "Éxito",
                detalle
            )

        except Exception as e:
            try:
                destino = REJECTED_DIR / archivo.name
                shutil.move(str(archivo), str(destino))
                escribir_log(
                    "ERROR",
                    "LIMPIEZA_RAW",
                    archivo.name,
                    "Error procesando JSON; movido a rejected",
                    "Error",
                    str(e)
                )
            except Exception as move_error:
                escribir_log(
                    "ERROR",
                    "LIMPIEZA_RAW",
                    archivo.name,
                    "Error doble en JSON",
                    "Error",
                    f"Procesamiento: {e} | Movimiento a rejected: {move_error}"
                )

if __name__ == "__main__":
    procesar_csv()
    procesar_excel()
    procesar_json()
    print("Proceso de limpieza finalizado.")