import os
from cryptography.fernet import Fernet

FERNET_SECRET = os.getenv("NOLIMITZ_FERNET_KEY")

if not FERNET_SECRET:
    raise RuntimeError("NOLIMITZ_FERNET_KEY is not set")

fernet = Fernet(FERNET_SECRET.encode())


def encrypt_text(value: str) -> str:
    return fernet.encrypt(value.encode()).decode()


def decrypt_text(value: str) -> str:
    return fernet.decrypt(value.encode()).decode()