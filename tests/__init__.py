import os


os.environ.setdefault("QR_SIGNING_KEY", "test_signing_key_for_tests_min_len_32")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("NEST_API_BASE_URL", "https://api.example.test")
