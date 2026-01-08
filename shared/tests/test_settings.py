import os

from django.test import SimpleTestCase

from digital_wallet.settings import _database_from_env


class SettingsTests(SimpleTestCase):
    def setUp(self):
        self._env_backup = {
            key: os.environ.get(key)
            for key in [
                "DB_HOST",
                "DB_NAME",
                "DB_USER",
                "DB_PASSWORD",
                "DB_PORT",
            ]
        }

    def tearDown(self):
        for key, value in self._env_backup.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def test_database_from_env_sqlite_default(self):
        os.environ["DB_HOST"] = ""
        databases = _database_from_env()
        self.assertEqual(databases["default"]["ENGINE"], "django.db.backends.sqlite3")

    def test_database_from_env_postgres(self):
        os.environ["DB_HOST"] = "db"
        os.environ["DB_NAME"] = "wallet"
        os.environ["DB_USER"] = "wallet_user"
        os.environ["DB_PASSWORD"] = "secret"
        os.environ["DB_PORT"] = "5433"

        databases = _database_from_env()
        self.assertEqual(
            databases["default"]["ENGINE"], "django.db.backends.postgresql"
        )
        self.assertEqual(databases["default"]["NAME"], "wallet")
        self.assertEqual(databases["default"]["USER"], "wallet_user")
        self.assertEqual(databases["default"]["PASSWORD"], "secret")
        self.assertEqual(databases["default"]["HOST"], "db")
        self.assertEqual(databases["default"]["PORT"], "5433")
