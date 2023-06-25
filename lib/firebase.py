import os

import firebase_admin
from firebase_admin import firestore_async, storage
from google.auth.exceptions import DefaultCredentialsError
from google.cloud.firestore import AsyncClient

from lib.logging import get_logger

logger = get_logger(__name__)


def _setup_adc():
    """Updates environment variable `GOOGLE_APPLICATION_CREDENTIALS` to point to the
    service account file in the root of the project if it exists.
    """
    creds_path = f"{os.getcwd()}/service_account.json"
    if os.path.exists(creds_path):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds_path


def _init_app() -> firebase_admin.App:
    _setup_adc()
    options = {"storageBucket": os.environ.get("FIREBASE_BUCKET_URL")}
    return firebase_admin.initialize_app(name="amarbot-app", options=options)


def get_app() -> firebase_admin.App:
    try:
        return firebase_admin.get_app("amarbot-app")
    except ValueError:
        return _init_app()


def get_firestore(app: firebase_admin.App = None) -> AsyncClient:
    try:
        return firestore_async.client(app or get_app())
    except DefaultCredentialsError:
        logger.warning(
            "Encountered DefaultCredentialsError when trying to fetch a Firestore "
            "instance. Some features utilizing Firestore database might not work "
            "correctly."
        )
        return None


def get_storage_bucket(app: firebase_admin.App = None) -> storage.storage.Bucket:
    return storage.bucket(app=app or get_app())
