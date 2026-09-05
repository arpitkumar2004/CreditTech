"""Cryptographic utilities for PII encryption (AES-256-GCM) and request signing (HMAC-SHA256)."""

import base64
import hashlib
import hmac
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from services.core.config import get_settings

settings = get_settings()


class CryptographyError(Exception):
    pass


class PIIEncryptor:
    """Handles AES-256-GCM encryption and decryption for sensitive data fields (Aadhaar, phone, name)."""

    def __init__(self) -> None:
        # Decode the base64-encoded key from settings
        try:
            key_bytes = base64.b64decode(settings.pii_encryption_key)
            # Ensure the key is exactly 32 bytes (256 bits)
            if len(key_bytes) != 32:
                # If invalid or default, derive a key using SHA-256 from the secret key
                key_bytes = hashlib.sha256(settings.secret_key.encode()).digest()
            self.aesgcm = AESGCM(key_bytes)
        except Exception:
            # Fallback to key derivation
            key_bytes = hashlib.sha256(settings.secret_key.encode()).digest()
            self.aesgcm = AESGCM(key_bytes)

    def encrypt(self, plain_text: str) -> str:
        """Encrypt a string and return a base64-encoded string containing nonce + ciphertext."""
        if not plain_text:
            return ""
        try:
            nonce = os.urandom(12)  # 96-bit nonce is recommended for GCM
            encrypted_bytes = self.aesgcm.encrypt(nonce, plain_text.encode("utf-8"), None)
            # Combine nonce and ciphertext, then base64 encode
            return base64.b64encode(nonce + encrypted_bytes).decode("utf-8")
        except Exception as e:
            raise CryptographyError(f"Encryption failed: {e}") from e

    def decrypt(self, cipher_text: str) -> str:
        """Decrypt a base64-encoded string and return the original plaintext string."""
        if not cipher_text:
            return ""
        try:
            raw_bytes = base64.b64decode(cipher_text.encode("utf-8"))
            if len(raw_bytes) < 12:
                raise CryptographyError("Ciphertext too short")
            nonce = raw_bytes[:12]
            encrypted_bytes = raw_bytes[12:]
            decrypted_bytes = self.aesgcm.decrypt(nonce, encrypted_bytes, None)
            return decrypted_bytes.decode("utf-8")
        except Exception as e:
            raise CryptographyError(f"Decryption failed: {e}") from e


class RequestSigner:
    """Generates and verifies HMAC-SHA256 signatures for API request bodies."""

    @staticmethod
    def generate_signature(payload: str, secret: str) -> str:
        """Compute the HMAC-SHA256 signature of a payload string."""
        key = secret.encode("utf-8")
        msg = payload.encode("utf-8")
        return hmac.new(key, msg, hashlib.sha256).hexdigest()

    @classmethod
    def verify_signature(cls, payload: str, signature: str, secret: str) -> bool:
        """Verify that a signature matches the payload."""
        expected = cls.generate_signature(payload, secret)
        return hmac.compare_digest(expected, signature)
