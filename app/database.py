from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker, Session
from app.config import config
from app.models import Base
import json


class Database:
    def __init__(self):
        # Для SQLite нужно добавить это
        if 'sqlite' in config.DATABASE_URL:
            self.engine = create_engine(
                config.DATABASE_URL,
                echo=config.DEBUG,
                connect_args={"check_same_thread": False}  # Для SQLite
            )
        else:
            self.engine = create_engine(config.DATABASE_URL, echo=config.DEBUG)

        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def create_tables(self):
        """Создание таблиц, если они не существуют"""
        # Проверяем существование таблиц
        inspector = inspect(self.engine)
        if not inspector.get_table_names():
            Base.metadata.create_all(bind=self.engine)
            print("Tables created successfully!")
        else:
            print("Tables already exist")

    def get_session(self) -> Session:
        return self.SessionLocal()


db = Database()


def get_db():
    session = db.get_session()
    try:
        yield session
    finally:
        session.close()