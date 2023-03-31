import sqlalchemy
from sqlalchemy import orm

from .db_session import SqlAlchemyBase


class Question(SqlAlchemyBase):
    __tablename__ = 'questions'

    question_id = sqlalchemy.Column(
        sqlalchemy.Integer,
        primary_key=True,
        autoincrement=True,
    )
    text = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    coords = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    pic_link = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    answer = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    #question_id = orm.relationship("quiz-question", back_populates='question_id')