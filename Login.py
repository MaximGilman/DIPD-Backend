# Для всех недостающих пакетов пропиши команду
# pip3 install {Имя пакета}

## Вот список базовых, которых точно нет на "чистом ПК"
#pip3 install Flask
#pip3 install psycopg2
#pip3 install flask-cors

import psycopg2
import psycopg2.extras
import http.server
import socketserver
from threading import Thread
import time
import sys
import json
import time
from flask import Flask
from flask import request
from flask_cors import CORS
import os
from dotenv import load_dotenv

app = Flask(__name__)
CORS(app)

PORT = 8999

load_dotenv()

con = psycopg2.connect(host=os.getenv('POSTGRESQL_HOST'), 
                        port=os.getenv('POSTGRESQL_PORT'), 
                        user=os.getenv('POSTGRESQL_USER'),  
                        password=os.getenv('POSTGRESQL_PASS'), 
                        dbname=os.getenv('POSTGRESQL_DB'))
con.autocommit = True


@app.route('/ping', methods=['GET'])
def ping():
    return {'status': 'working'}

# Метод получения данных о пользователе
@app.route('/user/<id>', methods=['GET'])
def GetUserById(id):
    with con:
        cur = con.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
        query = f"SELECT * FROM public.user WHERE key = {id}"
        cur.execute(query)
        return json.dumps(cur.fetchone())

# Метод для входа пользователя. Возвращает данные о пользователе по логину/паролю
@app.route('/user/login', methods=['POST'])
def LoginUser():
    inputs = request.get_json()
    if ('login' not in inputs):
        return ({'status': 'data_error', 'message': 'login expected'}, 400)
    if ('password' not in inputs):
        return ({'status': 'data_error', 'message': 'password expected'}, 400)
    login = inputs['login']
    password = inputs['password']
    with con:
        cur = con.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
        query = f"SELECT key FROM public.log_data WHERE login = \'{login}\' AND password=\'{password}\'"
        cur.execute(query)
        loginKey = cur.fetchone()
        if(loginKey == None):
            return ({'status': 'data_not_found', 'message': 'not found such user'}, 404)
        else:
            query = f"SELECT * FROM public.user WHERE login_id = {loginKey['key']}"
            cur.execute(query)
            user = cur.fetchone()
            return json.dumps(user)

# Метод получения всех пользователей
@app.route('/users/all', methods=['GET'])
def allScripts():
    return json.dumps(getuser())

def getuser():
    with con:
        cur = con.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
        query = f"SELECT * FROM public.user"
        cur.execute(query)
        rows = cur.fetchall() #fetchall() и fetchone()
    return rows

def server():
    global PORT   
    app.run(host="0.0.0.0", port=PORT)

server()

# Нужно добавить по аналогии методы:

# [POST] Создание пользователя
# Вх. параметры: Имя, Login, Password в формате JSON
# {
#   name: "",
#   password: "",
#   login: ""
# }

## проверить запросом, что нет такого логина в таблице log_data
## если уже есть, вернуть сообщение с ошибкой "user exists"
## если нет, создать пользователя в бд через INSERT запрос
### перед вставкой проверить, что все поля не равны null и заполнены


# [POST] Обновление пользователя. Имя, пароль, логин
# Вх. параметры: Ключ, Имя, Login, Password в формате JSON
## Получает модель пользователя  в виде json
# {
#   key: 1,
#   name: "",
#   password: "",
#   login: ""
# }

## метод UPDATE
## Проверить, что пользователь с таким ключем существует (в таблице user) и сохранить все поля в переменную User
## Получить ключ записи(log_data:key), у которой в таблице log_data пароль и логин равны тем, что пришло в запросе
### Если такого нет - вернуть ошибку
## Проверить, что log_data:key равен полю User.login_id, если нет - вернуть ошибку
## Выполнить запрос на изменение данных. Все переданные в аргументе параметры должны быть изменены в бд.
### Это лучше сделать 2мя запросами:
#### 1) Обновить имя пользователя в таблице user
#### 2) Обновить login / password в таблице log_data



# [POST] Удаление пользователя
# Вх. параметры: Ключ, Login, Password в формате JSON
# {
#   key: 1,
#   password: "",
#   login: ""
# }
## Проверить, что пользователь с таким ключем существует и сохранить все поля в переменную User
## Получить запись из таблицы log_data, в 
### SELECT * FROM log_data where key = {значение из User.Login_Id}
#### DELETE - запрос

# Logout пользователя - делать не нужно, сделаем со стороны клиента
# Опубликовать это на стенде - делать не нужно, сделаем это, когда будет готова реализация


#maxim / password