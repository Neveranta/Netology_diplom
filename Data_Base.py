# импорты
import sqlalchemy as sq
from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import Session
from Config import db_url_object


# схема БД
metadata = MetaData()
Base = declarative_base()


class Viewed(Base):
    __tablename__ = 'viewed'
    profile_id = sq.Column(sq.Integer, primary_key=True)
    worksheet_id = sq.Column(sq.Integer, primary_key=True)
    name = sq.Column(sq.String)
    black_list = sq.Column(sq.Boolean)
    favorites = sq.Column(sq.Boolean)

# добавление записи в бд


def add_user(engine, profile_id, worksheet_id,name, black_list, favorites):
    with Session(engine) as session:
        to_bd = Viewed(profile_id=profile_id,
                       worksheet_id=worksheet_id,
                       name=name,
                       black_list=black_list,
                       favorites=favorites)
        session.add(to_bd)
        session.commit()

# извлечение записей из БД


def check_user(engine, profile_id, worksheet_id):
    with Session(engine) as session:
        user = session.query(Viewed).filter(
            Viewed.profile_id == profile_id,
            Viewed.worksheet_id == worksheet_id
        ).first()
        return True if user else False


def exact_lists(engine,profile_id, category):
    with Session(engine) as session:
        if category == 'favorites':
            users = session.query(Viewed).filter(Viewed.profile_id == profile_id, Viewed.favorites == 'True').all()

        elif category == 'black_list':
            users = session.query(Viewed).filter(Viewed.profile_id == profile_id, Viewed.black_list == 'True').all()

        elif category == 'viewed':
            users = session.query(Viewed).filter(Viewed.profile_id == profile_id, Viewed.black_list == 'False', Viewed.favorites == 'False').all()

        return users


if __name__ == '__main__':
    engine = create_engine(db_url_object)
    Base.metadata.create_all(engine)
