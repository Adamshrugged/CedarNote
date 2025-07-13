from sqlmodel import SQLModel, create_engine, Session # type: ignore

DATABASE_URL = "sqlite:///./cedarnote.db"
engine = create_engine(DATABASE_URL, echo=False)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    return Session(engine)
