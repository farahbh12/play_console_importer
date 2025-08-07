from ast import Await
import os
import shutil
import tempfile
import zipfile
import re
import os
from django.apps import apps
import asyncio
import time
start_time = time.time()
import logging
from pathlib import Path
from asgiref.sync import sync_to_async
import asyncio
logger = logging.getLogger("pbs")
from datetime import datetime
import time
from play_reports.services.gcs_service import GCSService
gcs_service = GCSService()
import logging
from pathlib import Path
from typing import Optional, Callable, Dict, Any
from django.utils import timezone
from django.db import connection, transaction
from google.cloud import storage

import asyncio 
from django.utils.timezone import now
from play_reports.models import FileTracking
import hashlib
from play_reports.services.gcs_service import GCSService 
from play_reports.services.csv_service import CSVService 
# Configuration du logger principal

import logging

logger = logging.getLogger("pbs")
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('[%(levelname)s] %(asctime)s - %(message)s', "%Y-%m-%dT%H:%M:%S")
console_handler.setFormatter(formatter)

if not logger.hasHandlers():
    logger.addHandler(console_handler)

def log_info(*args):
    logger.info(" ".join(map(str, args)))

def log_error(*args):
    logger.error(" ".join(map(str, args))) # Added the missing closing parenthesis here

def log_debug(*args):
    logger.debug(" ".join(map(str, args)))


    

csv_service = CSVService()
class ProcessBucketService:
    def log_info(*args):
        logger.info(" ".join(map(str, args)))

    def log_error(*args):
        logger.error(" ".join(map(str, args)))

    def log_debug(*args):
        logger.debug(" ".join(map(str, args)))

    def __init__(self, data_source, gcs_service, progress_callback=None, tenant_id=None, **kwargs):
        if not data_source or not gcs_service:
            raise ValueError("Arguments du constructeur manquants")

        self.data_source = data_source
        # S'assurer que le tenant_id est celui de la source de données pour la cohérence

        self.tenant_id = data_source.tenant_id
        self.gcs_service = gcs_service
        self.progress_callback = progress_callback
        
        # Ignorer les arguments supplémentaires non reconnus
        if kwargs:
            logger.warning(f"Arguments ignorés dans ProcessBucketService.__init__: {list(kwargs.keys())}")

        logger.info(f"Service initialisé pour le tenant {self.tenant_id}, DataSource {getattr(data_source, 'id', 'inconnu')}")

        self.file_to_table_mapping = [
            # Reviews
            {
                'regex': r'^reviews/reviews_([\w\.]+)_(\d{6})\.csv$',
                'table': 'google_play_reviews',
                'type': 'csv',
                'report_type': 'reviews',
                'capture_groups': {'app_package': 1, 'report_period': 2}
            },
            # Sales
            {
                'regex': r'^sales/salesreport_(\d{6})\.zip$',
                'table': 'google_play_sales',
                'type': 'zip',
                'inner_csv_regex': r'^salesreport_\d{6}\.csv$',
                'report_type': 'sales',
                'capture_groups': {'report_period': 1}
            },
            # Earnings
            {
                'regex': r'^earnings/earnings_(\d{6})\.zip$',
                'table': 'google_play_earnings',
                'type': 'zip',
                'inner_csv_regex': r'^earnings_\d{6}\.csv$',
                'report_type': 'earnings',
                'capture_groups': {'report_period': 1}
            },
            # Invoice Billing
            {
                'regex': r'^invoice_billing_reports/invoice_billing_report_(\d{6})\.zip$',
                'table': 'google_play_invoice',
                'type': 'zip',
                'inner_csv_regex': r'^invoice_billing_report_\d{6}\.csv$',
                'report_type': 'invoice_billing',
                'capture_groups': {'report_period': 1}
            },
            # Play Balance KRW
            {
                'regex': r'^play_balance_krw/play_balance_krw_(\d{6})\.zip$',
                'table': 'google_play_krw',
                'type': 'zip',
                'inner_csv_regex': r'^play_balance_krw_\d{6}\.csv$',
                'report_type': 'play_balance_krw',
                'capture_groups': {'report_period': 1}
            },
            # Installs
            {
                'regex': r'^stats/installs/installs_([\w\.]+)_(\d{6})(?:_(overview|country|device|app_version|carrier|language|os_version))?\.csv$',
                'table_overview': 'google_play_installs_overview',
                'table_dimensioned': 'google_play_installs_dimensioned',
                'type': 'csv',
                'report_type': 'installs',
                'capture_groups': {
                    'app_package': 1,
                    'report_period': 2,
                    'suffix': 3
                }
            },
            # Crashes
            {
                'regex': r'^stats/crashes/crashes_([\w\.]+)_(\d{6})(?:_(overview|app_version|device|os_version|android_os_version))?\.csv$',
                'table_overview': 'google_play_crashes_overview',
                'table_dimensioned': 'google_play_crashes_dimensioned',
                'type': 'csv',
                'report_type': 'crashes',
                'capture_groups': {
                    'app_package': 1,
                    'report_period': 2,
                    'suffix': 3
                }
            },
            # Ratings
            {
                'regex': r'^stats/ratings/ratings_([\w\.]+)_(\d{6})(?:_(overview|country|device|app_version|carrier|language|os_version|android_os_version))?\.csv$',
                'table_overview': 'google_play_ratings_overview',
                'table_dimensioned': 'google_play_ratings_dimensioned',
                'type': 'csv',
                'report_type': 'ratings',
                'capture_groups': {'app_package': 1, 'report_period': 2, 'suffix': 3}
            },
            # Ratings v2
            {
                'regex': r'^stats/ratings_v2/ratings_v2_([\w\.]+)_(\d{6})(?:_(overview|country|device|app_version|carrier|language|os_version|android_os_version))?\.csv$',
                'table_overview': 'google_play_ratings_overview',
                'table_dimensioned': 'google_play_ratings_dimensioned',
                'type': 'csv',
                'report_type': 'ratings_v2',
                'capture_groups': {'app_package': 1, 'report_period': 2, 'suffix': 3}
            },
            # Subscriptions
            {
                'regex': r'^financial-stats/subscriptions/subscriptions_([\w\.]+)_([\w\-]+)_(\d{6})(?:_(overview|country))?\.csv$',
                'table_overview': 'google_play_subscriptions_overview',
                'table_dimensioned': 'google_play_subscriptions_dimensioned',
                'type': 'csv',
                'report_type': 'subscriptions',
                'capture_groups': {'app_package': 1, 'subscription_id': 2, 'report_period': 3, 'suffix': 4}
            },
            # Store Performance
            {
                'regex': r'^stats/store_performance/store_performance_([\w\.]+)_(\d{6})(?:_(overview|country|traffic_source|search_term))?\.csv$',
                'table_overview': 'google_play_store_performance_overview',
                'table_dimensioned': 'google_play_store_performance_dimensioned',
                'type': 'csv',
                'report_type': 'store_performance',
                'capture_groups': {'app_package': 1, 'report_period': 2, 'suffix': 3}
            },
            # Subscription Cancellation
            {
                'regex': r'^financial-stats/subscription_cancellation_reasons/subscription_cancellation_reasons_([\w\.]+)_([\w\-]+)_(\d{6})\.csv$',
                'table': 'google_play_subscription_cancellation_reasons',
                'type': 'csv',
                'report_type': 'subscription_cancellation_reasons',
                'capture_groups': {'app_package': 1, 'subscription_id': 2, 'report_period': 3}
            },
            # Promotional Content
            {
                'regex': r'^promotional_content/promotional_content_([\w\.]+)_(\d{6})\.csv$',
                'table': 'google_play_promotional_content',
                'type': 'csv',
                'report_type': 'promotional_content',
                'capture_groups': {'app_package': 1, 'report_period': 2}
            }
        ]


    def _get_report_info(self, remote_path):
        if not isinstance(remote_path, str):
            self.log_error(f"[_get_report_info] remote_path invalide: {remote_path} (type: {type(remote_path)})")
            return None

        lower_path = remote_path.lower()
        self.log_debug(f"[_get_report_info] Analyse du fichier: {remote_path} (lower: {lower_path})")

        for mapping in self.file_to_table_mapping:
            pattern = mapping.get("regex")
            if not pattern:
                continue

            match = re.search(pattern, lower_path)
            if match:
                self.log_debug(f"[_get_report_info] ✓ Regex match trouvé pour {remote_path}")
                self.log_debug(f"[_get_report_info]   Pattern: {pattern}")
                self.log_debug(f"[_get_report_info]   Groups: {match.groups()}")

                info = {
                    "originalPath": remote_path,
                    "mapping": mapping,
                    "fileType": mapping.get("type"),
                    "reportType": mapping.get("report_type"),
                    "appPackage": None,
                    "reportPeriod": None,
                    "suffix": None,
                    "dimensionCol": None,
                    "preferredTableName": None,
                    "tenantId": self.tenant_id,
                    "dataSourceId": getattr(self.data_source, "id", None),
                }

                capture_groups = mapping.get("capture_groups", {})
                for key, index in capture_groups.items():
                    try:
                        group_value = match.group(index)
                        if group_value:
                            info[key] = "os_version" if key == "suffix" and group_value == "android_os_version" else group_value
                    except IndexError:
                        self.log_debug(f"[_get_report_info] Groupe {index} introuvable pour la clé {key}")

                self.log_debug(f"[_get_report_info]   Info extraite: appPackage={info['appPackage']}, reportPeriod={info['reportPeriod']}, suffix={info['suffix']}")

                dimension_suffixes = ("country", "device", "traffic_source", "os_version", "android_os_version", "app_version", "carrier", "language")
                is_dimensioned = info["suffix"] in dimension_suffixes
                is_overview = not is_dimensioned and (info["suffix"] == "overview" or info["suffix"] is None)

                self.log_debug(f"[_get_report_info]   Logic flags: isOverview={is_overview}, isDimensioned={is_dimensioned}")
                self.log_debug(f"[_get_report_info]   Mapping props: table={mapping.get('table')}, table_overview={mapping.get('table_overview')}, table_dimensioned={mapping.get('table_dimensioned')}")

                if mapping.get("table") and info["suffix"] is None:
                    self.log_debug(f"[_get_report_info]   ✓ Utilisation de mapping.table: {mapping.get('table')}")
                    info["preferredTableName"] = mapping.get("table")
                elif is_dimensioned and mapping.get("table_dimensioned"):
                    self.log_debug(f"[_get_report_info]   ✓ Utilisation de mapping.table_dimensioned: {mapping.get('table_dimensioned')}")
                    info["preferredTableName"] = mapping.get("table_dimensioned")
                    info["dimensionCol"] = info["suffix"]
                elif is_overview and mapping.get("table_overview"):
                    self.log_debug(f"[_get_report_info]   ✓ Utilisation de mapping.table_overview: {mapping.get('table_overview')}")
                    info["preferredTableName"] = mapping.get("table_overview")
                else:
                    self.log_error(f"[_get_report_info] Impossible de déterminer le nom de la table pour {remote_path} avec suffixe '{info['suffix']}'")
                    self.log_error(f"[_get_report_info] Mapping disponible: table={mapping.get('table')}, table_overview={mapping.get('table_overview')}, table_dimensioned={mapping.get('table_dimensioned')}")
                    return None

                if not info["preferredTableName"]:
                    self.log_error(f"[_get_report_info] Nom de table préféré est null pour {remote_path}")
                    return None

                self.log_debug(f"[_get_report_info]   ✓ preferredTableName défini: {info['preferredTableName']}")
                self.log_debug(f"[_get_report_info]   ✓ Mapping trouvé pour {remote_path}: {info}")
                return info

        self.log_info(f"[_get_report_info] Aucun mapping trouvé pour le fichier: {remote_path}")
        return None






    def send_progress_event(self, data):
        if hasattr(self, 'progress_callback') and callable(self.progress_callback):
            try:
                self.progress_callback(data)
            except Exception as e:
                logger.error(f"Erreur lors de l'envoi de l'événement de progression: {str(e)}")
    async def update_file_tracking(self, tracking, success: bool, rows_processed: int = 0):
        try:
            if not tracking:
                log_error("Objet de tracking non fourni")
                return None

            now = datetime.utcnow()
            base_str = f"{tracking.file_path}_{now.isoformat()}"
            file_hash = hashlib.md5(base_str.encode("utf-8")).hexdigest()

            tracking.last_processed = now
            tracking.file_hash = file_hash

            if success and not tracking.first_processed:
                tracking.first_processed = now

            await tracking.asave(update_fields=["last_processed", "file_hash", "first_processed"] if success and not tracking.first_processed else ["last_processed", "file_hash"])

            log_debug(f"Tracking mis à jour pour {tracking.file_path}, traitement {'réussi' if success else 'echoué'}")
            return tracking
        except Exception as error:
            log_error("Erreur lors de la mise à jour du tracking:", str(error))
            return tracking
    
    async def process_csv_data(self, local_path: str, report_info: dict, batch_size: int = 500) -> int:
        """
        Traite un fichier CSV par lots en appelant insert_batch sur chaque lot.

        Args:
            local_path (str): chemin local du fichier CSV
            report_info (dict): informations sur le rapport (dont 'preferredTableName', 'originalPath', etc.)
            batch_size (int): taille des lots

        Returns:
            int: nombre total de lignes insérées
        """
        logging.info(f"process_csv_data: Début pour CSV: {local_path} -> Table: {report_info['preferredTableName']}")
        total_rows_inserted = 0

        try:
            logging.info(f"process_csv_data: Appel de csv_service.process_by_batches pour {local_path}")

            async def process_batch_callback(rows_batch, batch_number):
                logging.info(
                    f"process_csv_data: >>> DEBUT CALLBACK process_batch pour lot #{batch_number} "
                    f"({len(rows_batch)} lignes) pour {report_info['preferredTableName']} depuis {report_info['originalPath']}"
                )
                try:
                    # Vérification que chaque ligne est un dict
                    if not all(isinstance(row, dict) for row in rows_batch):
                        for i, row in enumerate(rows_batch):
                            if not isinstance(row, dict):
                                logging.error(f"process_csv_data: Ligne invalide à l’index {i} du lot #{batch_number}: {row}")
                        raise ValueError("process_csv_data: Une ou plusieurs lignes du batch ne sont pas des dictionnaires.")

                    inserted_count = await self.insert_batch(
                        rows_batch, report_info["preferredTableName"], report_info
                    )
                    logging.info(f"process_csv_data: insert_batch retourné {inserted_count} pour lot #{batch_number}")

                    nonlocal total_rows_inserted
                    total_rows_inserted += inserted_count
                except Exception as callback_error:
                    logging.error(
                        f"process_csv_data: ERREUR DANS LE CALLBACK process_batch (lot #{batch_number}) "
                        f"pour {report_info['originalPath']}: {callback_error}"
                    )
                logging.info(f"process_csv_data: <<< FIN CALLBACK process_batch pour lot #{batch_number}")

            # Appel asynchrone pour traiter les batches
            await csv_service.process_by_batches(local_path, process_batch_callback, batch_size)

            logging.info(
                f"process_csv_data: csv_service.process_by_batches terminé pour {local_path}. "
                f"Total lignes insérées: {total_rows_inserted}"
            )

        except Exception as error:
            logging.error(f"process_csv_data: ERREUR lors du traitement global du fichier CSV {local_path}: {error}")

        logging.info(f"process_csv_data: Fin pour {local_path}. Retourne {total_rows_inserted}")
        return total_rows_inserted




    async def process_all(self, gcs_uri):
    
     self.log_stats(f"🚀 Début synchronisation pour DataSource {self.data_source.id} ({self.data_source.name})")

     self.send_progress_event({
        "type": "sync_start",
        "message": f"Début synchronisation {self.data_source.name}",
        "progress": 0,
        "totalFiles": 0,
        "processedFiles": 0
    })

     sync_history = None
     try:
         sync_history = await self.create_sync_history("running", f"Synchronisation démarrée pour {self.data_source.name}")
     except Exception as history_error:
         self.log_error("Erreur création sync history:", str(history_error))

     try:
         self.send_progress_event({
            "type": "listing_files",
            "message": "Analyse du bucket en cours...",
            "progress": 5
        })
         files = await gcs_service.list_csv_files(gcs_uri)
         total_files_count = len(files)
         self.log_stats(f"📁 {total_files_count} fichiers trouvés dans le bucket")

         if total_files_count == 0:
             self.send_progress_event({
                "type": "sync_complete",
                "message": "Aucun fichier à traiter",
                "progress": 100
            })
             await self.update_sync_history(sync_history, 'success', {
                "logMessage": "Aucun fichier à traiter",
                "recordsProcessed": 0
            })
             return {"success": True, "message": "Aucun fichier à traiter", "filesProcessed": 0}

         results, skip_reasons = [], {}
         processed_count = error_count = skipped_count = total_records = 0

         for i, file in enumerate(files):
             remote_path = file.get('name') if isinstance(file, dict) else getattr(file, 'name', file)

             try:
                 mapping = self._get_report_info(remote_path)

                # Vérifie si mapping est bien un dictionnaire avec les bonnes clés
                 if isinstance(mapping, dict) and mapping.get("preferredTableName"):
                     result = await self.process_file(remote_path, mapping)
                     results.append(result)

                     if result.get("status") == "success":
                         processed_count += 1
                         total_records += result.get("rowsProcessed", 0)
                     else:
                         error_count += 1
                 else:
                     reason = self._analyze_skip_reason(remote_path)
                     skip_reasons[reason] = skip_reasons.get(reason, 0) + 1
                     skipped_count += 1
                     results.append({
                        "status": "skipped",
                        "path": remote_path,
                        "skipped": True,
                        "reason": reason
                    })

                 if (i + 1) % 10 == 0 or (i + 1) == total_files_count:
                     progress = round(10 + ((i + 1) / total_files_count) * 85)
                     self.send_progress_event({
                        "type": "processing_files",
                        "message": f"Traitement: {i + 1}/{total_files_count} fichiers",
                        "progress": progress,
                        "totalFiles": total_files_count,
                        "processedFiles": i + 1,
                        "successfulFiles": processed_count,
                        "skippedFiles": skipped_count,
                        "errorFiles": error_count,
                        "recordsInserted": total_records
                    })

             except Exception as file_error:
                 self.log_error(f"Erreur traitement fichier {i + 1}:", str(file_error))
                 results.append({
                    "status": "error",
                    "path": remote_path,
                    "error": str(file_error)
                })
                 error_count += 1

         duration = round(time.time() - start_time)
         success_rate = round((processed_count / total_files_count) * 100) if total_files_count else 0
         self.log_stats(f"✅ SYNCHRONISATION TERMINÉE en {duration}s")

         self.send_progress_event({
            "type": "sync_complete",
            "message": f"Synchronisation terminée: {processed_count}/{total_files_count} fichiers traités",
            "progress": 100,
            "success": True,
            "summary": {
                "filesProcessed": processed_count,
                "totalFiles": total_files_count,
                "recordsInserted": total_records,
                "successRate": success_rate,
                "duration": duration,
                "newStatus": 'synced' if processed_count > 0 else 'warning'
            }
        })

         await self.update_sync_history(sync_history, 'success', {
            "logMessage": f"{processed_count}/{total_files_count} fichiers traités avec succès",
            "recordsProcessed": total_records
        })

         return {
            "success": True,
            "message": f"Synchronisation terminée: {processed_count}/{total_files_count} fichiers traités",
            "filesProcessed": processed_count,
            "recordsInserted": total_records,
            "duration": duration,
            "successRate": success_rate,
            "results": results
        }

     except Exception as error:
         duration = round(time.time() - start_time)
         self.log_error(f"Erreur globale de synchronisation après {duration}s:", str(error))
         self.send_progress_event({
            "type": "sync_error",
            "message": f"Erreur: {str(error)}",
            "error": True,
            "duration": duration
        })
         await self.update_sync_history(sync_history, 'error', {
            "logMessage": f"Erreur: {str(error)}"
        })
         raise


    async def process_file(self, remote_path, report_info):
        logger.info(f"process_file: --- Début traitement pour: {remote_path} ---")

        # Vérification des paramètres
        if not isinstance(report_info, dict):
            logger.error("report_info n'est pas un dictionnaire valide")
            return {"status": "error", "rowsProcessed": 0, "error": "report_info invalide"}

        mapping = report_info.get("mapping", {})
        if not isinstance(mapping, dict):
            logger.error("mapping invalide dans report_info")
            return {"status": "error", "rowsProcessed": 0, "error": "mapping invalide"}

        file_tracking_result = await self.check_file_tracking(remote_path, report_info)
        file_tracking = file_tracking_result.get("tracking")

        temp_dir = tempfile.mkdtemp(prefix="datasource_")
        local_path = os.path.join(
            temp_dir,
            f"datasource_{report_info.get('dataSourceId', 'unknown')}_{os.path.basename(remote_path)}"
        )

        temp_extract_dir = None
        total_rows_processed = 0
        status = "pending"
        error_message = None

        try:
            # ✅ Récupération du bucket URI
            bucket_uri = report_info.get("bucketUri") or getattr(self.data_source, "bucket_uri", None)
            if not bucket_uri:
                raise ValueError("bucketUri manquant dans report_info ou data_source")

            logger.info(f"Téléchargement: {remote_path}")
            await self.gcs_service.download_file(bucket_uri, remote_path, local_path)
            logger.info(f"Téléchargement terminé: {local_path}")

            file_type = report_info.get("fileType")
            if file_type == "zip":
                temp_extract_dir = tempfile.mkdtemp(prefix="extract_")
                with ZipFile(local_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_extract_dir)

                csv_found = False
                for entry in os.listdir(temp_extract_dir):
                    entry_path = os.path.join(temp_extract_dir, entry)
                    regex = mapping.get("innerCsvRegex")
                    if regex and regex.search(entry):
                        logger.info(f"Fichier CSV interne trouvé : {entry_path}")
                        total_rows_processed = await self.process_csv_data(entry_path, report_info)
                        csv_found = True
                        break

                if not csv_found:
                    raise FileNotFoundError("Aucun CSV interne trouvé correspondant dans le ZIP.")

            elif file_type == "csv":
                logger.info(f"Traitement CSV direct: {local_path}")
                total_rows_processed = await self.process_csv_data(local_path, report_info)
            else:
                raise ValueError(f"Type de fichier non supporté : {file_type}")

            status = "success"
            if file_tracking:
                await self.update_file_tracking(file_tracking, True, total_rows_processed)

        except Exception as error:
            logger.error(f"ERREUR traitement {remote_path}: {str(error)}", exc_info=True)
            status = "error"
            error_message = str(error)
            if file_tracking:
                await self.update_file_tracking(file_tracking, False)

        finally:
            logger.info(f"--- Fin traitement {remote_path} ---")
            try:
                if temp_extract_dir and os.path.exists(temp_extract_dir):
                    shutil.rmtree(temp_extract_dir)
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
            except Exception as cleanup_error:
                logger.error(f"Erreur nettoyage: {cleanup_error}", exc_info=True)

        return {
            "status": status,
            "rowsProcessed": total_rows_processed,
            "error": error_message
        }



    async def download_file(self, remote_path: str, local_path: str) -> str:
        """
        Télécharge un fichier depuis le bucket GCS vers un chemin local.

        Args:
            remote_path (str): Chemin du fichier dans le bucket GCS.
            local_path (str): Chemin absolu où sauvegarder localement le fichier.

        Returns:
            str: Le chemin local du fichier téléchargé.
        """
        try:
            bucket_uri = getattr(self.data_source, "bucket_uri", None)
            if not bucket_uri:
                self.log_error("[download_file] bucket_uri manquant dans data_source.")
                raise ValueError("Le bucket_uri n'est pas défini dans la data source.")

            self.log_debug(f"Téléchargement de {remote_path} vers {local_path}...")
            await self.gcs_service.download_file(bucket_uri, remote_path, local_path)
            self.log_debug(f"Téléchargement de {remote_path} réussi.")
            return local_path

        except Exception as e:
            self.log_error(f"[download_file] Échec du téléchargement de {remote_path}: {e}")
            raise


    async def check_file_tracking(self, remote_path: str, report_info: dict) -> dict:
        try:
            file_tracking = await FileTracking.objects.filter(
                tenant_id=self.tenant_id,
                file_path=remote_path
            ).afirst()

            if file_tracking:
                last_processed = file_tracking.last_processed
                hours_since_last = (now() - last_processed).total_seconds() / 3600
                should_skip = hours_since_last < 24

                if should_skip:
                    logger.debug(f"Fichier {remote_path} traité il y a {round(hours_since_last)}h - ignoré")

                return {
                    "exists": True,
                    "tracking": file_tracking,
                    "should_skip": should_skip
                }

            new_tracking = await FileTracking.objects.acreate(
                tenant_id=self.tenant_id,
                file_path=remote_path,
                file_hash="",
                report_type=report_info.get('reportType'),
                target_table=report_info.get('preferredTableName'),
                first_processed=now(),
                last_processed=now(),
                is_deleted=False
            )

            logger.debug(f"Nouvelle entrée de tracking créée pour {remote_path}")
            return {
                "exists": False,
                "tracking": new_tracking,
                "should_skip": False
            }

        except Exception as error:
            logger.error(f"Erreur lors de la vérification du tracking pour {remote_path}:", exc_info=error)
            return {
                "exists": False,
                "error": str(error),
                "should_skip": False
            }
    async def create_sync_history(self, status, message):
        try:
            from play_reports.models import DataSourceSyncHistory
            from django.utils import timezone

            sync_history = await DataSourceSyncHistory.objects.acreate(
            data_source=self.data_source,
            status=status,
            started_at=timezone.now(),
            log_message=message
)

            logger.debug(f"Création de l'historique de synchronisation: {status} - {message}")
            return sync_history
        except Exception as e:
            logger.error(f"Erreur lors de la création de l'historique: {str(e)}", exc_info=True)
            return None

    async def update_sync_history(self, sync_history, status, details=None):
     if not sync_history:
         return

     sync_history.status = status
     sync_history.updated_at = timezone.now()

     # Filtrer uniquement les vrais champs du modèle
     valid_fields = [f.name for f in sync_history._meta.get_fields() if f.concrete and not f.many_to_many]
     update_fields = {}

     if details:
         for key, value in details.items():
             if key in valid_fields:
                 setattr(sync_history, key, value)
                 update_fields[key] = value
             else:
                 self.log_debug(f"[update_sync_history] Champ ignoré (inexistant): {key}")

     update_fields['status'] = status 
     update_fields['updated_at'] = sync_history.updated_at

     try:
         await sync_to_async(sync_history.save)(update_fields=list(update_fields.keys()))
     except Exception as e:
         self.log_error("Erreur lors de la mise à jour de l'historique:", e)

    @staticmethod
    def parse_flexible_date(date_string: str):
        if not date_string or not isinstance(date_string, str):
            return None
        cleaned = date_string.strip()
        if not cleaned:
            return None
        for fmt in ("%Y-%m-%d", "%Y%m%d", "%m/%d/%Y", "%d-%m-%Y", "%Y/%m/%d"):
            try:
                return datetime.strptime(cleaned, fmt).date()
            except ValueError:
                pass
        try:
            from dateutil.parser import parse
            return parse(cleaned).date()
        except (ValueError, ImportError):
            logger.debug(f"parse_flexible_date: Erreur parsing date '{date_string}'")
            return None

    def sanitize_db_column_name(self, col):
        return col.lower().replace(" ", "_")

    def prepare_row_data(self, row, report_info, model_fields):
        ModelClass = apps.get_model('play_reports', report_info["preferredTableName"])

        data_to_insert = {
            "tenant_id": self.tenant_id,
            "data_source_id": self.data_source.id,
            "file_path": report_info.get("originalPath"),
            "import_date": datetime.utcnow(),
            "app_package": report_info.get("appPackage"),
        }

        for col, value in row.items():
            field_name = self.sanitize_db_column_name(col)

            if report_info.get('dimensionCol') and ':' in col:
                try:
                    dim, key = col.split(':', 1)
                    if dim == report_info.get('dimensionCol'):
                        field_name = self.sanitize_db_column_name(key)
                except ValueError:
                    logger.warning(f"Colonne dimensionnée '{col}' mal formée et ignorée.")
                    continue

            if field_name in model_fields:
                django_field = ModelClass._meta.get_field(field_name)
                internal_type = django_field.get_internal_type()

                if value in ["", None]:
                    if not django_field.null:
                        # Fournir une valeur par défaut pour les champs NOT NULL
                        if internal_type in ["IntegerField", "BigIntegerField", "FloatField", "DecimalField"]:
                            data_to_insert[field_name] = 0
                        elif internal_type == "BooleanField":
                            data_to_insert[field_name] = False
                        else:
                            # Pour les autres types (ex: CharField), None peut être acceptable ou causer une erreur si non-nul
                            # Laisser None pour que l'erreur soit explicite si la contrainte est violée
                            data_to_insert[field_name] = None
                    else:
                        data_to_insert[field_name] = None
                else:
                    try:
                        if internal_type in ["IntegerField", "BigIntegerField"]:
                            data_to_insert[field_name] = int(value)
                        elif internal_type in ["FloatField", "DecimalField"]:
                            data_to_insert[field_name] = float(value)
                        elif internal_type in ["DateField", "DateTimeField"]:
                            data_to_insert[field_name] = self.parse_flexible_date(str(value))
                        elif internal_type == "BooleanField":
                            data_to_insert[field_name] = str(value).lower() in ["true", "1", "yes"]
                        else:
                            data_to_insert[field_name] = str(value)
                    except Exception as e:
                        logger.error(f"insert_batch: Erreur conversion champ '{field_name}', valeur '{value}': {e}")
                        data_to_insert[field_name] = None

        date_col = row.get('date') or row.get('Date')
        if date_col:
            data_to_insert["report_date"] = self.parse_flexible_date(date_col)
        elif report_info.get("reportPeriod"):
            try:
                data_to_insert["report_date"] = datetime.strptime(report_info["reportPeriod"], "%Y%m").date()
            except (ValueError, TypeError):
                logger.warning(f"insert_batch: reportPeriod '{report_info['reportPeriod']}' invalide")

        return data_to_insert

    @sync_to_async
    def _update_sync_history_sync(self, sync_history, updates):
        sync_history.save(update_fields=list(updates.keys()))

    async def insert_batch(self, rows_batch, table_name, report_info):
        try:
            ModelClass = apps.get_model('play_reports', table_name)
        except LookupError:
            logger.error(f"insert_batch: Modèle '{table_name}' introuvable.")
            return 0

        model_fields = {f.name for f in ModelClass._meta.get_fields()}
        objects_to_create = []

        for row_idx, row in enumerate(rows_batch, start=1):
            if not isinstance(row, dict):
                logger.error(f"Ligne {row_idx} invalide: type {type(row)}")
                continue

            # Préparation des données de la ligne
            data = self.prepare_row_data(row, report_info, model_fields)

            # ✅ Injection correcte de tenant_id
            if "tenantId" in report_info:
                data["tenant_id"] = report_info["tenantId"]
            elif self.tenant_id is not None:
                data["tenant_id"] = self.tenant_id
            else:
                logger.warning(f"Ligne {row_idx} sans tenant_id – ignorée.")
                continue  # Ignore les lignes sans tenant_id

            # Filtrer uniquement les champs valides
            filtered_data = {k: v for k, v in data.items() if k in model_fields}

            try:
                obj = ModelClass(**filtered_data)
                objects_to_create.append(obj)
            except Exception as e:
                logger.error(f"Erreur création objet ligne {row_idx}: {e}")

        if not objects_to_create:
            logger.warning("insert_batch: aucune ligne prête pour insertion")
            return 0

        try:
            await ModelClass.objects.abulk_create(objects_to_create, ignore_conflicts=True)
            logger.info(f"insert_batch: {len(objects_to_create)} lignes insérées pour {table_name}")
            return len(objects_to_create)
        except Exception as e:
            logger.error(f"insert_batch: erreur lors de l'insertion: {e}")
            return 0
    def log_stats(*args):
     logger.info("[PBS_STATS] " + " ".join(map(str, args)))        

    def _analyze_skip_reason(self, remote_path: str) -> str:
        """
        Analyse pourquoi un fichier est ignoré, basé sur son chemin, son extension ou son nom.

        Args:
            remote_path (str): Le chemin distant du fichier

        Returns:
            str: La raison pour laquelle le fichier doit être ignoré
        """
        if not remote_path:
            return "Chemin vide"

        file_name = remote_path.lower()
        extension = file_name.split('.')[-1]

        # 1. Extensions non supportées
        unsupported_extensions = {
            'tmp', 'temp', 'bak', 'old', 'log', 'info', 'metadata',
            'cache', 'swp', 'lock', 'ds_store', 'thumbs'
        }
        if extension in unsupported_extensions:
            return "Extension non supportée"

        # 2. Fichiers cachés ou système
        if file_name.startswith('.') or '/.' in file_name:
            return "Fichier caché/système"

        # 3. Noms suspects (fichiers de test, copies, etc.)
        suspicious_patterns = [
            r'test_', r'sample_', r'example_', r'demo_', r'backup_',
            r'_test', r'_sample', r'_backup', r'_old', r'_temp',
            r'duplicate', r'copy', r'untitled'
        ]
        for pattern in suspicious_patterns:
            if re.search(pattern, file_name, flags=re.IGNORECASE):
                return "Fichier de test/backup"

        # 4. Répertoires non supportés
        unsupported_directories = {
            'temp', 'tmp', 'cache', 'logs', 'backup', 'test', 'samples',
            'metadata', 'system', '.git', '.svn', 'node_modules'
        }
        main_dir = file_name.split('/')[0]
        if main_dir in unsupported_directories:
            return "Répertoire non supporté"

        # 5. Cas par défaut
        return "Format de nom de fichier non reconnu"
 