import os

class BaseConfig:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    DATABASE_PATH = os.environ.get('DATABASE_PATH', 'data/local.db')
    TURSO_DATABASE_URL = os.environ.get('TURSO_DATABASE_URL')
    TURSO_AUTH_TOKEN = os.environ.get('TURSO_AUTH_TOKEN')

class DevConfig(BaseConfig):
    DEBUG = True

class ProdConfig(BaseConfig):
    DEBUG = False

class TestConfig(BaseConfig):
    TESTING = True
    DATABASE_PATH = ':memory:'