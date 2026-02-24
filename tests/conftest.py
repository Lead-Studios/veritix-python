import os

# Provide a non-default test key so startup validation passes in test environments.
os.environ.setdefault("QR_SIGNING_KEY", "a" * 32)
