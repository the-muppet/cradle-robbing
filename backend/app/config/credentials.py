import os
import json
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from google.oauth2 import service_account

class CredentialsInfo(BaseModel):
    """
    Handles Google Cloud credentials and project information.
    Provides methods for initialization and credential management.
    """
    credentials: Optional[service_account.Credentials] = None
    project_id: str = Field(default="")
    
    model_config = ConfigDict(arbitrary_types_allowed=True)

    @classmethod
    def init_credentials(cls):
        """Initialize credentials from environment variables"""
        credentials_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
        if not credentials_json:
            raise ValueError("GOOGLE_APPLICATION_CREDENTIALS_JSON environment variable not set")

        try:
            creds_dict = json.loads(credentials_json)
            project_id = creds_dict.get("project_id")
            if not project_id:
                raise ValueError("project_id not found in credentials")

            credentials = service_account.Credentials.from_service_account_info(creds_dict)
            return cls(credentials=credentials, project_id=project_id)
            
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON in GOOGLE_APPLICATION_CREDENTIALS_JSON")
        except Exception as e:
            raise ValueError(f"Error initializing credentials: {str(e)}")

    def verify(self) -> bool:
        """Verify that credentials are properly initialized"""
        return bool(self.credentials and self.project_id)