import os
import requests
from dotenv import load_dotenv

load_dotenv()


class AdminClient:
    def __init__(self, base_url=None):
        self.base_url = base_url or os.getenv("ADMIN_SERVICE_URL", "http://administration-service:5002")

    def get_facultades(self):
        res = requests.get(f"{self.base_url}/api/administracion/facultades/")
        res.raise_for_status()
        return res.json()
