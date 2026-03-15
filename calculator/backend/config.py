"""
Configuration module for Rocket Logistic backend.

All runtime settings are sourced from environment variables with safe defaults.
Call Config.validate() at startup to surface configuration problems early.
"""

from __future__ import annotations

import os
from typing import ClassVar


class Config:
    """Central configuration for the Rocket Logistic backend."""

    # ---------------------------------------------------------------------------
    # Paths
    # ---------------------------------------------------------------------------

    BASE_DIR: ClassVar[str] = os.path.dirname(os.path.abspath(__file__))

    SUBMISSIONS_DIR: ClassVar[str] = os.getenv(
        "SUBMISSIONS_DIR", os.path.join(BASE_DIR, "submissions")
    )

    CONTACTS_JSON: ClassVar[str] = os.path.join(SUBMISSIONS_DIR, "contacts.json")
    CONTACTS_CSV: ClassVar[str] = os.path.join(SUBMISSIONS_DIR, "contacts.csv")

    QUOTES_JSON: ClassVar[str] = os.path.join(SUBMISSIONS_DIR, "quotes.json")
    QUOTES_CSV: ClassVar[str] = os.path.join(SUBMISSIONS_DIR, "quotes.csv")

    PRICES_FILE: ClassVar[str] = os.getenv(
        "PRICES_FILE", os.path.join(BASE_DIR, "prices.json")
    )

    # ---------------------------------------------------------------------------
    # Rate limiting
    # ---------------------------------------------------------------------------

    PRICES_MAX_REQUESTS_PER_HOUR: ClassVar[int] = int(
        os.getenv("PRICES_MAX_REQUESTS_PER_HOUR", "60")
    )
    MAX_SUBMISSIONS_PER_HOUR: ClassVar[int] = 5

    # ---------------------------------------------------------------------------
    # Security
    # ---------------------------------------------------------------------------

    SECRET_KEY: ClassVar[str] = os.getenv("SECRET_KEY", "dev-secret-key")

    # ---------------------------------------------------------------------------
    # Email
    # ---------------------------------------------------------------------------

    MAIL_SERVER: ClassVar[str] = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT: ClassVar[int] = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USE_TLS: ClassVar[bool] = os.getenv("MAIL_USE_TLS", "True").lower() in (
        "true", "1", "yes",
    )
    MAIL_USERNAME: ClassVar[str] = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD: ClassVar[str] = os.getenv("MAIL_PASSWORD", "")
    COMPANY_EMAIL: ClassVar[str] = os.getenv(
        "COMPANY_EMAIL", "info@rocketlogistic.bg"
    )

    # ---------------------------------------------------------------------------
    # Validation
    # ---------------------------------------------------------------------------

    @classmethod
    def validate(cls) -> list[str]:
        """Check that required runtime configuration is present and valid.

        Returns a list of human-readable warning strings. An empty list means
        everything is fine.
        """
        errors: list[str] = []

        if not os.path.isfile(cls.PRICES_FILE):
            errors.append(
                f"PRICES_FILE not found: '{cls.PRICES_FILE}'. "
                "Set the PRICES_FILE environment variable to the correct path."
            )

        if cls.SECRET_KEY == "dev-secret-key":
            errors.append(
                "SECRET_KEY is using the insecure default. "
                "Set the SECRET_KEY environment variable in production."
            )

        if not cls.MAIL_USERNAME:
            errors.append(
                "MAIL_USERNAME is not set. Email notifications will not be sent."
            )

        if not cls.MAIL_PASSWORD:
            errors.append(
                "MAIL_PASSWORD is not set. Email notifications will not be sent."
            )

        return errors
