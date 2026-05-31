from pathlib import Path
from datetime import datetime
import shutil
import csv

BASE_DIR = Path(__file__).resolve().parent.parent

LANDING_DIR = BASE_DIR / "Landing"
DATALAKE_DIR = BASE_DIR / "DataLake"
RAW_CSV_DIR = DATALAKE_DIR / "raw" / "csv"
RAW_EXCEL_DIR = DATALAKE_DIR / "raw" / "excel"
RAW_JSON_DIR = DATALAKE_DIR / "raw" / "json"
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

def obtener_nombre_unico(destino: Path) -> Path:
    if not destino.exists():
        return destino

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nuevo_nombre = f"{destino.stem}_{timestamp}{destino.suffix}"
    return destino.with_name(nuevo_nombre)

def mover_archivos():
    archivos = list(LANDING_DIR.iterdir())

    if not archivos:
        escribir_log(
            "INFO",
            "INGESTA_RAW",
            "-",
            "Revisión de Landing",
            "Éxito",
            "No se encontraron archivos para procesar"
        )
        print("No hay archivos en Landing.")
        return

    for archivo in archivos:
        if archivo.is_dir():
            continue

        extension = archivo.suffix.lower()

        try:
            if extension == ".csv":
                destino = obtener_nombre_unico(RAW_CSV_DIR / archivo.name)
                shutil.move(str(archivo), str(destino))
                escribir_log(
                    "INFO",
                    "INGESTA_RAW",
                    archivo.name,
                    "Movido a raw/csv",
                    "Éxito",
                    f"Destino final: {destino.name}"
                )

            elif extension in [".xlsx", ".xls"]:
                destino = obtener_nombre_unico(RAW_EXCEL_DIR / archivo.name)
                shutil.move(str(archivo), str(destino))
                escribir_log(
                    "INFO",
                    "INGESTA_RAW",
                    archivo.name,
                    "Movido a raw/excel",
                    "Éxito",
                    f"Destino final: {destino.name}"
                )

            elif extension == ".json":
                destino = obtener_nombre_unico(RAW_JSON_DIR / archivo.name)
                shutil.move(str(archivo), str(destino))
                escribir_log(
                    "INFO",
                    "INGESTA_RAW",
                    archivo.name,
                    "Movido a raw/json",
                    "Éxito",
                    f"Destino final: {destino.name}"
                )

            else:
                destino = obtener_nombre_unico(REJECTED_DIR / archivo.name)
                shutil.move(str(archivo), str(destino))
                escribir_log(
                    "WARNING",
                    "INGESTA_RAW",
                    archivo.name,
                    "Formato no permitido; movido a rejected",
                    "Éxito",
                    f"Extensión detectada: {extension if extension else 'sin extensión'}"
                )

        except Exception as e:
            escribir_log(
                "ERROR",
                "INGESTA_RAW",
                archivo.name,
                "Error durante la ingesta",
                "Error",
                str(e)
            )

if __name__ == "__main__":
    mover_archivos()
    print("Proceso de ingesta finalizado.")