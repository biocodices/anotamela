from sqlalchemy.dialects.postgresql import JSONB

from anotala.cache import SqlCache


class PostgresCache(SqlCache):
    CREDS_FILE = '~/.postgres_credentials.yml'
    JSON_TYPE = JSONB
    URL = '{driver}://{user}:{pass}@{host}:{port}/{db}'

