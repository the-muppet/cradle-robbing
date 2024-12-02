import os
import json
from google.oauth2 import service_account
from dataclasses import dataclass

@dataclass
class CredentialsInfo:
    credentials: service_account.Credentials
    project_id: str

    @staticmethod
    def init_credentials():
        """Initialize and return credentials and project info"""
        credentials_json = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON")
        if not credentials_json:
            raise Exception(
                "GOOGLE_APPLICATION_CREDENTIALS_JSON environment variable not set"
            )

        creds = json.loads(credentials_json)
        project_id = creds.get("project_id")
        if not project_id:
            raise Exception("project_id not found in credentials")

        credentials = service_account.Credentials.from_service_account_info(
            creds
        )
        return CredentialsInfo(credentials=credentials, project_id=project_id)
