from cryptography.fernet import Fernet
import os
import base64
from sqlmodel import Session, select
from app.core.database import engine, Integration

MASTER_KEY = os.getenv("ENCRYPTION_KEY", Fernet.generate_key().decode())


class CredentialManager:
    def __init__(self):
        self.cipher = Fernet(MASTER_KEY)

    def encrypt(self, plain_text_key: str) -> str:
        if not plain_text_key:
            return None
        return self.cipher.encrypt(plain_text_key.encode()).decode()

    def decrypt(self, encrypted_key: str) -> str:
        if not encrypted_key:
            return None
        return self.cipher.decrypt(encrypted_key.encode()).decode()


def save_credential(connection_id: str, api_key: str | None, name: str, spec_url: str) -> bool:
    """
    Saves or Updates an integration record in the DB.
    """
    manager = CredentialManager()
    encrypted = manager.encrypt(api_key)

    with Session(engine) as session:
        statement = select(Integration).where(
            Integration.connection_id == connection_id)
        results = session.exec(statement)
        existing_integration = results.first()

        if existing_integration:
            existing_integration.name = name
            existing_integration.spec_url = spec_url

            if encrypted is not None:
                existing_integration.encrypted_key = encrypted
            else:
                session.add(existing_integration)
                session.commit()
                print(
                    f"No api_key provided; preserved existing key for '{connection_id}'.")
                return False

            session.add(existing_integration)
        else:
            new_integration = Integration(
                name=name,
                spec_url=spec_url,
                encrypted_key=encrypted,
                connection_id=connection_id
            )
            session.add(new_integration)

        session.commit()
    print(f"Credentials for '{connection_id}' saved to DB.")
    return True


def get_auth_headers(connection_id: str) -> dict:
    """
    Retrieves key from DB -> Decrypts -> Returns Header.
    """
    with Session(engine) as session:
        statement = select(Integration).where(
            Integration.connection_id == connection_id)
        result = session.exec(statement).first()

        if not result or not result.encrypted_key:
            return {}

        manager = CredentialManager()
        decrypted_key = manager.decrypt(result.encrypted_key)

        return {"Authorization": f"Bearer {decrypted_key}"}
