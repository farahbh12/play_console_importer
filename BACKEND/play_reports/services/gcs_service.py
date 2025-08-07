import os
import logging
from pathlib import Path
import tempfile
import uuid
from google.cloud import storage
from google.oauth2 import service_account

logger = logging.getLogger(__name__)
DEBUG_MODE = os.environ.get("DJANGO_DEBUG", "false").lower() == "true"

def log_debug(*args):
    if DEBUG_MODE:
        logger.debug("[GCS DEBUG] " + " ".join(map(str, args)))

def log_stats(*args):
    logger.info("📊 [GCS] " + " ".join(map(str, args)))

class GCSService:
    def __init__(self, credentials_path=None):
        self.client = None
        self.initialized = False
        self.credentials_path = credentials_path or os.getenv(
            "GCS_KEY_FILE", "./credentials/service-account.json"
        )

    def initialize(self):
        try:
            if not Path(self.credentials_path).exists():
                alt_path = Path("./credentials/service-account.json")
                if alt_path.exists():
                    self.credentials_path = str(alt_path)
                    log_debug("Clé trouvée dans le chemin alternatif:", self.credentials_path)
                    creds = service_account.Credentials.from_service_account_file(self.credentials_path)
                    self.client = storage.Client(credentials=creds, project=creds.project_id)
                else:
                    log_debug("Aucune clé trouvée, tentative sans credentials.")
                    self.client = storage.Client()
            else:
                creds = service_account.Credentials.from_service_account_file(self.credentials_path)
                self.client = storage.Client(credentials=creds, project=creds.project_id)
                log_debug("Client GCS initialisé avec:", self.credentials_path)

            self.initialized = True
            log_stats("Initialisation réussie ✅")
            return True
        except Exception as e:
            logger.error("❌ Erreur initialisation GCS:", exc_info=True)
            self.initialized = False
            return False

    def _check_initialized(self):
        if not self.initialized:
            log_debug("Initialisation automatique GCS...")
            if not self.initialize():
                raise RuntimeError("Le service GCS n’est pas initialisé.")

    def parse_bucket_uri(self, bucket_uri):
        log_debug("Parsing bucket URI:", bucket_uri)
        if bucket_uri.startswith("gs://"):
            parts = bucket_uri[5:].split("/", 1)
            bucket = parts[0]
            path = parts[1] if len(parts) > 1 else ""
            return bucket, path.rstrip("/")
        elif bucket_uri.startswith("pubsite_prod_rev_"):
            return bucket_uri, ""
        else:
            raise ValueError(f"URI GCS invalide: {bucket_uri}")

    async def list_files(self, bucket_uri, prefix=""):
        self._check_initialized()
        bucket_name, path_prefix = self.parse_bucket_uri(bucket_uri)
        bucket = self.client.bucket(bucket_name)
        prefix = ""  # comme dans Node.js : toujours depuis racine

        try:
            blobs = list(bucket.list_blobs(prefix=prefix))
            files = []
            for blob in blobs:
                files.append({
                    "name": blob.name,
                    "size": blob.size,
                    "content_type": blob.content_type,
                    "updated": blob.updated,
                    "full_path": f"gs://{bucket_name}/{blob.name}",
                })
            log_stats(f"Récupéré {len(files)} fichiers depuis bucket \"{bucket_name}\"")
            for f in files[:5]:
                log_debug(f" - {f['name']}")
            return files
        except Exception as e:
            logger.error(f"❌ Erreur listing {bucket_uri}:", exc_info=True)
            raise RuntimeError(f"Erreur listing GCS: {str(e)}")

    async def list_files_recursively(self, bucket_uri):
        log_debug("list_files_recursively appelé pour:", bucket_uri)
        return await self.list_files(bucket_uri)

    async def list_csv_files(self, bucket_uri):
        try:
            files = await self.list_files(bucket_uri)
            csv_files = [
                f for f in files
                if f["name"].lower().endswith(".csv") or f["content_type"] in ("text/csv", "application/csv")
            ]
            log_stats(f"📄 {len(csv_files)} fichiers CSV trouvés dans {bucket_uri}")
            if DEBUG_MODE:
                for f in csv_files[:10]:
                    log_debug(f" - {f['name']}")
                if len(csv_files) > 10:
                    log_debug(f"... et {len(csv_files) - 10} autres")
            return csv_files
        except Exception as e:
            logger.error(f"❌ Erreur listage CSV {bucket_uri}:", exc_info=True)
            raise

    async def download_file(self, bucket_uri, file_path, local_path=None):
        self._check_initialized()
        bucket_name, _ = self.parse_bucket_uri(bucket_uri)
        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(file_path)

        local_path = local_path or os.path.join(
            tempfile.gettempdir(),
            f"gcs-download-{uuid.uuid4()}-{os.path.basename(file_path)}"
        )

        try:
            blob.download_to_filename(local_path)
            log_debug("✅ Téléchargement réussi:", local_path)
            return local_path
        except Exception as e:
            logger.error(f"❌ Erreur téléchargement {file_path}:", exc_info=True)
            raise RuntimeError(f"Erreur téléchargement: {str(e)}")

    async def validate_bucket_access(self, bucket_uri):
        self._check_initialized()
        bucket_name, _ = self.parse_bucket_uri(bucket_uri)
        try:
            bucket = self.client.bucket(bucket_name)
            exists = bucket.exists()
            log_stats(f"🔐 Accès bucket {bucket_name}: {'✅ OK' if exists else '❌ KO'}")
            return exists
        except Exception as e:
            logger.error("❌ Erreur validation accès bucket:", exc_info=True)
            return False

# Singleton (comme module.exports = new GCSService())
gcs_service = GCSService()
