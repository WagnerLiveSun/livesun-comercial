import os
import unittest
from unittest.mock import patch

from src.core.database_config import (
    FORBIDDEN_POSTGRES_USERS,
    build_database_uri,
    get_db_engine,
    is_postgresql_configured,
    is_postgresql_uri,
    missing_production_env,
    uri_without_password,
)


_DB_KEYS = [
    'DB_ENGINE', 'DB_TYPE', 'DB_HOST', 'DB_PORT', 'DB_USER', 'DB_PASSWORD', 'DB_NAME',
    'MYSQL_HOST', 'MYSQL_PORT', 'MYSQL_USER', 'MYSQL_PASSWORD', 'MYSQL_DATABASE',
    'POSTGRES_HOST', 'POSTGRES_PORT', 'POSTGRES_USER', 'POSTGRES_PASSWORD', 'POSTGRES_DATABASE',
    'POSTGRES_RLS_ENABLED',
]


def _clear_db_env():
    env = {k: v for k, v in os.environ.items() if k not in _DB_KEYS}
    return env


class DatabaseConfigTestCase(unittest.TestCase):
    def test_invalid_engine(self):
        with patch.dict(os.environ, {**_clear_db_env(), 'DB_ENGINE': 'oracle'}, clear=True):
            with self.assertRaises(RuntimeError) as ctx:
                get_db_engine()
            self.assertIn('DB_ENGINE', str(ctx.exception))
            self.assertNotIn('senha', str(ctx.exception).lower())

    def test_missing_postgres_password_does_not_leak_secret(self):
        env = _clear_db_env()
        env.update({
            'DB_ENGINE': 'postgresql',
            'POSTGRES_HOST': '127.0.0.1',
            'POSTGRES_USER': 'livesun_api',
            'POSTGRES_DATABASE': 'comercial',
        })
        with patch.dict(os.environ, env, clear=True):
            with self.assertRaises(RuntimeError) as ctx:
                build_database_uri()
            message = str(ctx.exception)
            self.assertIn('POSTGRES_PASSWORD', message)
            self.assertNotIn('secret', message.lower())

    def test_mysql_uri_uses_legacy_db_vars(self):
        env = _clear_db_env()
        env.update({
            'DB_ENGINE': 'mysql',
            'DB_HOST': 'mysql.example',
            'DB_PORT': '3306',
            'DB_USER': 'app_user',
            'DB_PASSWORD': 'p@ss/word',
            'DB_NAME': 'comercial',
        })
        with patch.dict(os.environ, env, clear=True):
            uri = build_database_uri()
            self.assertTrue(uri.startswith('mysql+pymysql://'))
            self.assertIn('mysql.example:3306/comercial', uri)
            self.assertIn('charset=utf8mb4', uri)
            self.assertIn('app_user', uri)
            self.assertNotIn('p@ss/word', uri_without_password(uri))
            self.assertIn(':***@', uri_without_password(uri))
            self.assertFalse(is_postgresql_configured())

    def test_postgres_uri_montu_defaults(self):
        env = _clear_db_env()
        env.update({
            'DB_ENGINE': 'postgresql',
            'POSTGRES_PASSWORD': 'local-only',
        })
        with patch.dict(os.environ, env, clear=True):
            uri = build_database_uri()
            self.assertTrue(uri.startswith('postgresql+psycopg2://'))
            self.assertIn('livesun_api', uri)
            self.assertIn('127.0.0.1:55432/comercial', uri)
            self.assertIn('application_name=livesun_comercial', uri)
            self.assertTrue(is_postgresql_uri(uri))
            self.assertNotIn('local-only', uri_without_password(uri))

    def test_postgres_alias_engine_name(self):
        env = _clear_db_env()
        env.update({
            'DB_ENGINE': 'postgres',
            'POSTGRES_PASSWORD': 'x',
            'POSTGRES_USER': 'livesun_api',
        })
        with patch.dict(os.environ, env, clear=True):
            self.assertEqual(get_db_engine(), 'postgresql')
            self.assertIn('postgresql+psycopg2://', build_database_uri())

    def test_forbidden_postgres_runtime_users(self):
        for user in FORBIDDEN_POSTGRES_USERS:
            env = _clear_db_env()
            env.update({
                'DB_ENGINE': 'postgresql',
                'POSTGRES_USER': user,
                'POSTGRES_PASSWORD': 'x',
            })
            with patch.dict(os.environ, env, clear=True):
                with self.assertRaises(RuntimeError) as ctx:
                    build_database_uri()
                self.assertIn('livesun_api', str(ctx.exception))

    def test_missing_production_mysql_names(self):
        env = _clear_db_env()
        env.pop('SECRET_KEY', None)
        env['DB_ENGINE'] = 'mysql'
        with patch.dict(os.environ, env, clear=True):
            missing = missing_production_env()
            self.assertIn('SECRET_KEY', missing)
            self.assertTrue(any(name in missing for name in ('DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_NAME')))


if __name__ == '__main__':
    unittest.main()
