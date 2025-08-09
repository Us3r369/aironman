import os
from garminconnect import (
    Garmin,
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
)
from garth.exc import GarthHTTPError
from utils.config import settings


def get_garmin_client() -> Garmin:
    """
    Returns an authenticated Garmin client using credentials from centralized config (Pydantic BaseSettings).
    Handles token reuse and refresh. Tokens are stored in ~/.garminconnect by default.
    """
    email = settings.GARMIN_EMAIL
    password = settings.GARMIN_PASSWORD
    tokenstore = settings.GARMINTOKENS or os.path.expanduser("~/.garminconnect")

    if not email or not password:
        raise ValueError(
            "EMAIL and PASSWORD must be set as environment variables or in a .env file."
        )

    try:
        # Try to login using stored tokens
        garmin = Garmin()
        garmin.login(tokenstore)
    except (FileNotFoundError, GarthHTTPError, GarminConnectAuthenticationError):
        # Session is expired or tokens missing, need to log in again
        try:
            garmin = Garmin(
                email=email, password=password, is_cn=False, return_on_mfa=True
            )
            result1, result2 = garmin.login()
            if result1 == "needs_mfa":
                mfa_code = input("MFA one-time code: ")
                garmin.resume_login(result2, mfa_code)
            # Save tokens for future use
            garmin.garth.dump(tokenstore)
            garmin.login(tokenstore)
        except (
            FileNotFoundError,
            GarthHTTPError,
            GarminConnectAuthenticationError,
        ) as err:
            raise RuntimeError(f"Garmin authentication failed: {err}")
    return garmin

def get_garmin_credentials() -> tuple[str, str]:
    """Return Garmin account credentials from settings.

    This helper is used by tests to verify that credentials are sourced from the
    environment or configuration layer.
    """
    return settings.GARMIN_EMAIL, settings.GARMIN_PASSWORD
