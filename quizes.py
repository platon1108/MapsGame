import sqlalchemy
from sqlalchemy import orm

from .db_session import SqlAlchemyBase


class Quiz(SqlAlchemyBase):
    __tablename__ = 'quizes'

    quiz_id = sqlalchemy.Column(
        sqlalchemy.Integer,
        primary_key=True,
        autoincrement=True,
    )
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    description = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    question_count = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    level = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    owner_id = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    #question_id = orm.relationship("quiz-question", back_populates='question_id')