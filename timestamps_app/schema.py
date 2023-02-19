import sqlalchemy as sa
from db import engine
from loguru import logger
from sqlalchemy.orm import Session, declarative_base, relationship

Base = declarative_base()


# Define a model for the url and summary markdown
class Summary(Base):
    __tablename__ = "summary"
    id = sa.Column(sa.Integer, primary_key=True)
    url = sa.Column(sa.String, index=True)
    video_id = sa.Column(sa.String, index=True)
    created_at = sa.Column(sa.DateTime, default=sa.func.now())
    summary_markdown = sa.Column(sa.String)


if __name__ == "__main__":
    Base.metadata.create_all(engine)
