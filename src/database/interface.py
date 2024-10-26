from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from telethon.sessions import StringSession

from src.database.migrate import maybe_first_time_migrate

from .schema import InternalKV, User


class DatabaseSchemaInvalid(Exception): ...


class TelethonSessionStore(StringSession):
    def __init__(self, db_session: Session):
        self.db_session = db_session
        with db_session.begin():
            store: InternalKV | None = db_session.query(InternalKV).get("session")

            if store is None:
                store = InternalKV()
                store.key = "session"
                store.value = None
                db_session.add(store)

            self.store = store

        super().__init__(self.store.value)  # type: ignore upstream typing bug

    def save(self) -> str:
        data = super().save()

        self.store.value = data
        self.db_session.commit()

        return data

    def close(self):
        self.db_session.close()
        return super().close()


class UserStore:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, id: int) -> User | None:
        return self.session.query(User).get(id)

    def add(self, object: User) -> None:
        self.session.add(object)
        self.session.commit()

    def remove(self, id: int) -> None:
        user = self.session.query(User).get(id)

        if user is None:
            raise KeyError()

        self.session.delete(user)
        self.session.commit()


class Database:
    def __init__(self, datastore: str):
        self.engine = create_engine(datastore)
        maybe_first_time_migrate(self.engine)

        self.start_session = sessionmaker(bind=self.engine)

        self.session_store = TelethonSessionStore(self.start_session())
        self.user_store = UserStore(self.start_session())
