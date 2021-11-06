import re
from flask_login import UserMixin

from db import get_db

class User(UserMixin):
    def __init__(self, id_, name, email, profile_pic):
        self.id = id_
        self.name = name
        self.email = email
        self.profile_pic = profile_pic

    @staticmethod
    def get(user_id):
        db = get_db()
        db.execute(
            f"SELECT (google_id, name, email, profile_pic_url) FROM public.user WHERE google_id = '{user_id}'"
            )
        try:
            user = db.fetchall()
        except AttributeError:
            return None

        if not user:
            return None
        # Проблема с psycopg2.extras.DictRow, делаем это дело в массив, чтобы можно было получить значения
        userOutStr = user[0][0].split(",")
        # Убираем скобки у первого и последнего элемента
        userOutStr[0] = userOutStr[0][1:]
        userOutStr[-1] = userOutStr[-1][:-1]

        user = User(
            id_= userOutStr[0], name = userOutStr[1], email = userOutStr[2], profile_pic = userOutStr[3]
        )
        return user

    @staticmethod
    def create(id_, name, email, profile_pic):
        db = get_db()
        db.execute(
            f"INSERT INTO public.user (google_id, name, email, profile_pic_url) VALUES (\'{id_}\', \'{name}\', \'{email}\', \'{profile_pic}\')"
        )
        db.close()
        

