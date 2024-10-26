from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase): ...


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer(), primary_key=True)

    latitude: Mapped[float]
    longitude: Mapped[float]

    # N of seconds as an Integer here is more efficent than sqlalchemy.Interval, because we don't actually perform any time-specific operations with that value
    interval: Mapped[int | None]


class InternalKV(Base):
    __tablename__ = "internal"

    key: Mapped[str] = mapped_column(String(), primary_key=True)
    value: Mapped[str | None]
