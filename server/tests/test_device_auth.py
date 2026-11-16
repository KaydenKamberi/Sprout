"""B4: authenticate_device checks the Authorization: Bearer device key (spec 10.1, step 1).

The tests call authenticate_device directly, with a stake whose key is stored only as
hash_device_key(key). No web request is needed.
"""

from datetime import UTC, datetime

import pytest
from sqlalchemy import select

from app.device_auth import authenticate_device, hash_device_key
from app.errors import ApiError
from app.models import Device

KEY = "sprout-test-device-key-0123456789abcdef"
SERIAL = "SPR-TEST-0001"


def make_device(session, serial: str = SERIAL, key: str = KEY, retired: bool = False) -> Device:
    device = Device(
        serial=serial,
        key_hash=hash_device_key(key),
        retired_at=datetime.now(UTC).replace(tzinfo=None) if retired else None,
    )
    session.add(device)
    session.commit()
    return device


def test_right_key_returns_the_device_row(db_session) -> None:
    stored = make_device(db_session)

    device = authenticate_device(db_session, SERIAL, f"Bearer {KEY}")

    assert device.id == stored.id


def test_retired_stake_with_right_key_is_not_rejected(db_session) -> None:
    stored = make_device(db_session, retired=True)

    device = authenticate_device(db_session, SERIAL, f"Bearer {KEY}")

    assert device.id == stored.id
    assert device.retired_at is not None


@pytest.mark.parametrize(
    ("serial", "header"),
    [
        (SERIAL, None),
        (SERIAL, f"Token {KEY}"),
        (SERIAL, "Bearer the-wrong-key"),
        ("SPR-UNKNOWN-9999", f"Bearer {KEY}"),
    ],
)
def test_missing_or_wrong_key_or_unknown_serial_raises_401(
    db_session, serial: str, header: str | None
) -> None:
    make_device(db_session)

    with pytest.raises(ApiError) as raised:
        authenticate_device(db_session, serial, header)

    assert raised.value.status == 401


def test_every_401_has_the_same_code_and_message(db_session) -> None:
    make_device(db_session)

    codes_and_messages = set()
    for serial, header in [
        (SERIAL, None),
        (SERIAL, f"Token {KEY}"),
        (SERIAL, "Bearer the-wrong-key"),
        ("SPR-UNKNOWN-9999", f"Bearer {KEY}"),
    ]:
        with pytest.raises(ApiError) as raised:
            authenticate_device(db_session, serial, header)
        codes_and_messages.add((raised.value.code, raised.value.message))

    assert len(codes_and_messages) == 1


def test_key_hash_never_contains_the_key_itself(db_session) -> None:
    make_device(db_session)

    device = db_session.execute(select(Device).where(Device.serial == SERIAL)).scalar_one()

    assert device.key_hash != KEY
    assert KEY not in device.key_hash
