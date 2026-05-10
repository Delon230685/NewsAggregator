from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker, Session
from app.config import config
from app.models import Base
from app.logger import logger


class Database:
    """Класс для управления подключением к базе данных"""

    def __init__(self) -> None:
        """Инициализация подключения к БД"""
        self.engine = self._create_engine()
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        logger.debug(f"Database initialized with URL: {self._mask_url(config.DATABASE_URL)}")

    def _create_engine(self):
        """Создание движка SQLAlchemy с учетом типа БД"""
        if 'sqlite' in config.DATABASE_URL:
            logger.debug("Using SQLite database")
            return create_engine(
                config.DATABASE_URL,
                echo=config.DEBUG,
                connect_args={"check_same_thread": False}  # Для SQLite
            )
        else:
            logger.debug(f"Using database: {config.DATABASE_URL.split('://')[0]}")
            return create_engine(config.DATABASE_URL, echo=config.DEBUG)

    def _mask_url(self, url: str) -> str:
        """Маскирует пароль в URL для безопасного логирования"""
        if not url:
            return "not set"
        if 'sqlite' in url:
            return url
        if '@' in url:
            parts = url.split('@')
            protocol_auth = parts[0]
            protocol = protocol_auth.split('://')[0]
            return f"{protocol}://***@{parts[1]}"
        return url

    def create_tables(self) -> None:
        """Создание таблиц, если они не существуют"""
        inspector = inspect(self.engine)
        existing_tables = inspector.get_table_names()

        if not existing_tables:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully!")
            inspector = inspect(self.engine)
            tables = inspector.get_table_names()
            logger.debug(f"Created tables: {', '.join(tables)}")
        else:
            logger.info(f"Tables already exist: {', '.join(existing_tables)}")

    def get_session(self) -> Session:
        """Получить новую сессию БД"""
        return self.SessionLocal()

    def drop_all_tables(self) -> None:
        """Удалить все таблицы (осторожно, только для разработки!)"""
        if config.DEBUG:
            logger.warning("Dropping all database tables!")
            Base.metadata.drop_all(bind=self.engine)
            logger.info("All tables dropped")
        else:
            logger.error("drop_all_tables can only be used in DEBUG mode")

    def get_tables_info(self) -> dict[str, int]:
        """Получить информацию о таблицах (название -> количество записей)"""
        from sqlalchemy import text

        tables_info: dict[str, int] = {}
        inspector = inspect(self.engine)

        for table_name in inspector.get_table_names():
            try:
                with self.engine.connect() as conn:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                    count = result.scalar()
                    tables_info[table_name] = count
            except Exception as e:
                logger.error(f"Error getting count for table {table_name}: {e}")
                tables_info[table_name] = -1

        return tables_info


db = Database()


def get_db():
    """Генератор сессий для зависимостей FastAPI"""
    session = db.get_session()
    try:
        yield session
    except Exception as e:
        logger.error(f"Database session error: {e}")
        session.rollback()
        raise
    finally:
        session.close()