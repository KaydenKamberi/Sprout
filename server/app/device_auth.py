"""Device key auth: the check POST /api/readings runs as step 1 of spec 10.1.

Every stake sends its key as `Authorization: Bearer <device key>` on every upload. The
server stores only an argon2 hash of each key (devices.key_hash), never the key itself
(spec 8.7, DEC-18). A retired stake with the right key authenticates like any other
(spec 8.5.1): the paused config comes later, in the config reply (task card B5).

Every 401 carries the same code and message, so the reply never says which part failed
(unknown serial, missing key or wrong key). Task card B3 uses the same code and message.
"""

from argon2 import PasswordHasher
from argon2.exceptions import Argon2Error
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import ApiError
from app.models import Device

# Stop-and-ask 9.1: the spec says "argon2" without settings, so this card uses
# argon2-cffi's default PasswordHasher. B17's create_device calls hash_device_key, so
# keys are always made and checked the same way.
# Stop-and-ask 9.3: spec 10.6 gives no code for 401; this card chooses "unauthorized".
UNAUTHORIZED_STATUS = 401
UNAUTHORIZED_CODE = "unauthorized"
UNAUTHORIZED_MESSAGE = "Missing or invalid device key"

_hasher = PasswordHasher()


def hash_device_key(key: str) -> str:
    """The argon2 hash stored in devices.key_hash."""
    return _hasher.hash(key)


def authenticate_device(
    session: Session, serial: str, authorization_header: str | None
) -> Device:
    """Return the stake's devices row when the key is right, else raise ApiError 401.

    `authorization_header` is the raw Authorization header value, or None when the
    header is missing. A retired stake (retired_at set) is returned like any other.
    """
    scheme, _, key = (authorization_header or "").partition(" ")
    if scheme != "Bearer" or not key:
        raise ApiError(UNAUTHORIZED_STATUS, UNAUTHORIZED_CODE, UNAUTHORIZED_MESSAGE)

    device = session.execute(select(Device).where(Device.serial == serial)).scalar_one_or_none()
    if device is None:
        raise ApiError(UNAUTHORIZED_STATUS, UNAUTHORIZED_CODE, UNAUTHORIZED_MESSAGE)

    try:
        _hasher.verify(device.key_hash, key)
    except Argon2Error:
        raise ApiError(UNAUTHORIZED_STATUS, UNAUTHORIZED_CODE, UNAUTHORIZED_MESSAGE) from None

    return device
