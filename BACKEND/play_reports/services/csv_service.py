import csv
import chardet
import logging
from pathlib import Path
from datetime import datetime

# Configuration du logger
logger = logging.getLogger(__name__)

class CSVService:
    def __init__(self):
        self.batch_size = 500

    def detect_encoding(self, file_path: str) -> str:
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read(10000)
            result = chardet.detect(raw_data)
            return result['encoding'] or 'utf-8'
        except Exception as e:
            logger.error(f"Erreur lors de la détection de l'encodage du fichier {file_path}: {e}")
            return 'utf-8'

    def normalize_column_name(self, column: str) -> str:
        if not isinstance(column, str):
            return ''
        return column.strip().lower().replace(' ', '_')

    async def process_by_batches(self, file_path: str, process_batch: callable, batch_size: int = 1000) -> int:
        encoding = self.detect_encoding(file_path)
        logger.info(f"Traitement du fichier {file_path} avec l'encodage {encoding}")

        total_rows = 0
        batch = []
        batch_number = 1

        try:
            with open(file_path, 'r', encoding=encoding, errors='ignore') as csvfile:
                reader = csv.DictReader(csvfile)

                if reader.fieldnames:
                    reader.fieldnames = [self.normalize_column_name(h) for h in reader.fieldnames]
                else:
                    raise ValueError(f"Le fichier CSV {file_path} ne contient pas d'en-têtes.")

                for row in reader:
                    if not isinstance(row, dict):
                        logger.warning(f"Ligne ignorée : le format attendu est dict, reçu {type(row)}")
                        continue

                    batch.append(row)

                    if len(batch) >= batch_size:
                        await process_batch(batch, batch_number)
                        total_rows += len(batch)
                        batch = []
                        batch_number += 1

                # Dernier lot
                if batch:
                    await process_batch(batch, batch_number)
                    total_rows += len(batch)

        except Exception as e:
            logger.error(f"Erreur lors du traitement du fichier CSV {file_path}: {e}")

        logger.info(f"Traitement terminé pour {file_path}. {total_rows} lignes traitées en {batch_number} lots.")
        return total_rows

    def clean_value(self, value):
        if value is None or str(value).strip().lower() in ('', 'null', 'none'):
            return None
        return str(value).strip()

    def parse_number(self, value):
        try:
            return float(self.clean_value(value))
        except (ValueError, TypeError):
            return None

    def parse_date(self, value, date_format='%Y-%m-%d'):
        try:
            return datetime.strptime(self.clean_value(value), date_format)
        except (ValueError, TypeError):
            return None

# ✅ Instance unique (singleton-like)
csv_service = CSVService()

# ✅ Export pour import direct depuis le service
__all__ = ["csv_service", "CSVService"]
