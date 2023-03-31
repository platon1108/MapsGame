import sqlalchemy
from sqlalchemy import orm

from .db_session import SqlAlchemyBase


class Quiz2Question(SqlAlchemyBase):
    __tablename__ = 'quiz2question'

    quiz_id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    question_id = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)