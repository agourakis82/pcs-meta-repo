#!/usr/bin/env python3
"""
Generate a Fernet key for MEM_ENCRYPTION_KEY.

Usage:
  python scripts/generate_fernet_key.py

Then export:
  export MEM_ENCRYPTION_KEY=<printed_key>
"""

try:
    from cryptography.fernet import Fernet
except Exception:
    print("cryptography not installed. Run: pip install cryptography")
    raise SystemExit(1)

key = Fernet.generate_key()
print(key.decode("utf-8"))

