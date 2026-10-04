"""Client for the shared identity-service: sign-in, sign-up, and token verification."""
import os
import time
from dataclasses import dataclass

import jwt
import requests
from jwt import PyJWKClient

# identity-service runs on a free tier that sleeps; the first call can take a minute or more.
TIMEOUT_SECONDS = 20
ATTEMPTS = 3
RETRY_DELAY_SECONDS = 4
TRANSIENT_STATUSES = (502, 503, 504)
WAKING_MESSAGE = "The sign-in service is waking up. Please try again in a minute."


class IdentityError(Exception):
    """Carries a message that is safe to show to the user."""


class InvalidCredentials(IdentityError):
    pass


@dataclass(frozen=True)
class Identity:
    sub: str
    email: str


def _base_url():
    return os.environ.get("IDENTITY_URL", "http://localhost:8081").rstrip("/")


_jwks_client = None
_jwks_client_url = None


def _jwks():
    global _jwks_client, _jwks_client_url
    url = f"{_base_url()}/.well-known/jwks.json"
    if _jwks_client is None or _jwks_client_url != url:
        _jwks_client = PyJWKClient(url, cache_keys=True)
        _jwks_client_url = url
    return _jwks_client


def verify_access_token(token):
    """Verify signature and expiry against identity-service's published keys; reject non-access tokens."""
    try:
        key = _jwks().get_signing_key_from_jwt(token).key
        claims = jwt.decode(token, key, algorithms=["RS256"], options={"require": ["exp", "sub"]})
    except jwt.PyJWTError as exc:
        raise IdentityError("Your sign-in could not be verified. Please try again.") from exc
    if claims.get("type") != "access":
        raise IdentityError("Your sign-in could not be verified. Please try again.")
    return Identity(sub=claims["sub"], email=(claims.get("email") or "").strip().lower())


def _post(path, payload):
    """POST with a couple of retries for cold starts (connection errors, 502/503/504)."""
    for attempt in range(1, ATTEMPTS + 1):
        try:
            response = requests.post(f"{_base_url()}{path}", json=payload, timeout=TIMEOUT_SECONDS)
            if response.status_code not in TRANSIENT_STATUSES:
                return response
            print(f"identity {path}: HTTP {response.status_code} (attempt {attempt}/{ATTEMPTS})", flush=True)
        except requests.RequestException as exc:
            print(f"identity {path}: {type(exc).__name__} (attempt {attempt}/{ATTEMPTS})", flush=True)
        if attempt < ATTEMPTS:
            time.sleep(RETRY_DELAY_SECONDS)
    raise IdentityError(WAKING_MESSAGE)


def authenticate(email, password):
    response = _post("/auth/login", {"email": email.strip(), "password": password})
    if response.status_code in (400, 401):
        raise InvalidCredentials("Invalid email or password.")
    if not response.ok:
        print(f"identity login failed: HTTP {response.status_code} from {_base_url()}/auth/login", flush=True)
        raise IdentityError("Sign-in failed. Please try again.")
    return verify_access_token(response.json()["accessToken"])


def register(email, password, first_name, last_name):
    """Create the identity-service account only. The caller signs in separately."""
    response = _post("/auth/register", {
        "email": email.strip(),
        "password": password,
        "firstName": first_name.strip(),
        "lastName": last_name.strip(),
    })
    if response.status_code == 409:
        raise IdentityError("An account with that email already exists. Try signing in instead.")
    if response.status_code == 400:
        raise IdentityError("That sign-up was rejected. Check your name, email and password (use a longer password).")
    if not response.ok:
        raise IdentityError("Could not create the account. Please try again.")
