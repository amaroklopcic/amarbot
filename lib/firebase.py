import json
import os

import firebase_admin
from firebase_admin import credentials, firestore


def get_credentials():
    try:
        return credentials.Certificate(cert="service_account.json")
    except Exception as e:
        print(f"Encountered an error when trying to fetch Firebase credentials:\n{e}")
    finally:
        return None


def init_app():
    return firebase_admin.initialize_app(credential=get_credentials())


def get_firestore(app):
    db = firestore.client(app)
