from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

engine = create_engine("postgresql+psycopg://postgres:dev@localhost:5432/simjobs")
SessionLocal = sessionmaker(engine)

class Base(DeclarativeBase):
    pass

class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    simulation: Mapped[str]
    params: Mapped[dict] = mapped_column(JSONB)
    status: Mapped[str]
    result: Mapped[dict | None] = mapped_column(JSONB)

Base.metadata.create_all(engine)
