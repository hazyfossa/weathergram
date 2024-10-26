from loguru import logger
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from .schema import Base, InternalKV


def maybe_first_time_migrate(engine: Engine):
    with Session(engine) as session:
        try:
            session.query(InternalKV).get("initialized")
            migrate = False
        except Exception:
            migrate = True

    if migrate:
        logger.info("Detected first time setup: migrating database")
        Base.metadata.create_all(engine)
