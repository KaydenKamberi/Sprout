"""Build firmware/certs/x509_crt_bundle, the root certificate bundle the net_test program
embeds so WiFiClientSecure can check any public HTTPS server's certificate (spec 7.9).

Input: Mozilla's root list as ESP-IDF ships it, from the same IDF version the pinned
Arduino core is built on (core 3.3.9 = ESP-IDF v5.5.4):
  https://raw.githubusercontent.com/espressif/esp-idf/v5.5.4/components/mbedtls/esp_crt_bundle/cacrt_all.pem

Run (needs the "cryptography" Python package):
  python make_bundle.py cacrt_all.pem x509_crt_bundle

Output format is the one ESP-IDF 5.5's esp_crt_bundle.c reads: n little-endian uint32
offsets, then per certificate [name_len u16][key_len u16][subject DER][public key DER],
sorted by subject DER. (The older gen_crt_bundle.py inside the Arduino core writes the
pre-5.5 format, which IDF 5.5 rejects.)
"""

import struct
import sys

from cryptography import x509
from cryptography.hazmat.primitives import serialization

MAX_CERTS = 200  # CONFIG_MBEDTLS_CERTIFICATE_BUNDLE_MAX_CERTS in the core's sdkconfig


def main(pem_path: str, out_path: str) -> None:
    with open(pem_path, "rb") as f:
        certs = x509.load_pem_x509_certificates(f.read())
    if not certs or len(certs) > MAX_CERTS:
        sys.exit(f"expected 1..{MAX_CERTS} certificates, got {len(certs)}")

    entries = []
    for crt in certs:
        name = crt.subject.public_bytes()
        key = crt.public_key().public_bytes(
            serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo
        )
        entries.append((name, key))
    entries.sort(key=lambda e: e[0])

    body = b""
    offsets = []
    table_len = 4 * len(entries)
    for name, key in entries:
        offsets.append(table_len + len(body))
        body += struct.pack("<HH", len(name), len(key)) + name + key

    with open(out_path, "wb") as f:
        f.write(struct.pack(f"<{len(offsets)}L", *offsets) + body)
    print(f"{len(entries)} certificates, {table_len + len(body)} bytes -> {out_path}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: python make_bundle.py cacrt_all.pem x509_crt_bundle")
    main(sys.argv[1], sys.argv[2])
