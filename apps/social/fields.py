"""Fields for encrypting OAuth secrets before they reach the database."""

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.db import models


class EncryptedTextField(models.TextField):
    """A transparent Fernet-encrypted text field.

    Existing plaintext values remain readable and are encrypted on their next
    save, allowing a non-destructive rollout.
    """

    prefix = "enc::"

    @staticmethod
    def _fernet():
        configured_key = getattr(settings, "TOKEN_ENCRYPTION_KEY", "")
        if configured_key:
            key = configured_key.encode("ascii")
        else:
            digest = hashlib.sha256(settings.SECRET_KEY.encode("utf-8")).digest()
            key = base64.urlsafe_b64encode(digest)
        return Fernet(key)

    def from_db_value(self, value, expression, connection):
        if not value or not value.startswith(self.prefix):
            return value
        try:
            return self._fernet().decrypt(value[len(self.prefix):].encode("ascii")).decode("utf-8")
        except (InvalidToken, ValueError, UnicodeDecodeError):
            # Do not destroy an inaccessible credential; surface it as unusable.
            return ""

    def to_python(self, value):
        return value

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        if not value or value.startswith(self.prefix):
            return value
        return self.prefix + self._fernet().encrypt(value.encode("utf-8")).decode("ascii")
