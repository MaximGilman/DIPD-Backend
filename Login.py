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
            return user #убрал json.dumps(user), т.к. из-за этого не мог получать данные user

# Метод обновления существующей записи
@app.route('/user/update', methods=['POST'])
def UpdateUser():

    inputs = request.get_json() # получаем данные из запроса

    requires = ['key', 'name', 'password', 'login'] # обязательные параметры запроса

    for param in requires:
        if param not in inputs:
            return ({'status': 'data_error', 'message': f'{param} expected'}, 400)

    key = inputs['key']
    name = inputs['name']
    password = inputs['password']
    login = inputs['login']

    with con:

        cur = con.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
        query = f"SELECT name, login_id FROM public.user WHERE key = \'{key}\'" # получили имя пользователя и логин_ид 
        cur.execute(query)

        user = cur.fetchone()
        userCopy = user
        user = json.dumps(user)

        if user != 'null':
            loginKey = userCopy["login_id"] #логин_ид 
            query = f"UPDATE public.user SET name = \'{name}\' WHERE key =\'{key}\'" #обновляем имя пользователя
            cur.execute(query)

            query = f"SELECT * FROM public.log_data WHERE key = \'{loginKey}\'" #в таблице log_data собираем поля по ид
            cur.execute(query)
            user = json.dumps(cur.fetchone())

            #если есть пользователь, то обновляем, иначе выдаём ошибку
            if user != 'null':
                query = f"UPDATE public.log_data SET (login, password) =  (\'{login}\', \'{password}\') WHERE key =\'{loginKey}\'"
                cur.execute(query)
                return {"status":"OK"}
            else:
                return ({'status': 'data_not_found', 'message': 'not found such user in log_data'}, 404)
        else:
            return ({'status': 'data_not_found', 'message': 'not found such user in user'}, 404)

# Метод создания записи о пользователе
@app.route('/user/create', methods=['POST'])
def CreateUser():

    inputs = request.get_json() # получаем данные из запроса

    requires = ['name', 'password', 'login'] # обязательные параметры запроса

    for param in requires:
        if param not in inputs:
            return ({'status': 'data_error', 'message': f'{param} expected'}, 400)

    name = inputs['name']
    password = inputs['password']
    login = inputs['login']
    
    requiresInput = dict(zip(['name', 'password', 'login'],[name, password, login]))

    # Сообщение об отсутствии заполнения данных. Пока что выводит только для одного поля
    # Если отсутствует больше 1 поля, выводит сообщение только про первое прочитанное
    for input in requiresInput:
        if requiresInput[input] == "":
            return ({'status': 'data_error', 'message': f'value for {input} expected'}, 400)

    userCheck = LoginUser() #пытаемся найти пользователя по логину и паролю

    # Если userCheck не нашёл существующей записи о пользователе 
    if "key" not in userCheck:
        with con:
            cur = con.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
            query = f"INSERT INTO public.log_data (login, password) VALUES (\'{login}\', \'{password}\')"
            cur.execute(query)

            # Получаем key пользователя из log_data
            query = f"SELECT key FROM public.log_data WHERE (login, password) = (\'{login}\', \'{password}\')"
            cur.execute(query)
            loginKey = cur.fetchone()["key"]
            
            # Создаём запись в user
            query = f"INSERT INTO public.user (name, login_id) VALUES (\'{name}\', \'{loginKey}\')"
            cur.execute(query)
            return {"status":"check"}
    else:
        return ({'status': 'data_found', 'message': 'there`s already user in tb user'}, 412)

# Метод удаления пользователя

@app.route('/user/delete', methods=['POST'])
def DeleteUser():

    inputs = request.get_json() # получаем данные из запроса

    key = inputs['key']
    password = inputs['password']
    login = inputs['login']

    requires = ['key', 'password', 'login'] # обязательные параметры запроса

    for param in requires:
        if param not in inputs:
            return ({'status': 'data_error', 'message': f'{param} expected'}, 400)
    
    userCheck = LoginUser()

    # Проверка, что запись есть в log_data
    if "key" in userCheck:
        loginKey = userCheck["key"]

        # Проверка, что запись есть в user
        if GetUserById(loginKey) != "null":
            with con:
                cur = con.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
                query = f"SELECT * FROM public.log_data WHERE key = \'{key}\'"
                cur.execute(query)
                user = cur.fetchone() # Сохранили в User
                
                query = f"DELETE FROM public.log_data WHERE key = \'{key}\'"
                cur.execute(query)

                return{'status': 'OK', 'message': 'user deleted'}
                
        else:
            return ({'status': 'data_error', 'message': 'no such user in tb user'}, 400)    
    else:
        return ({'status': 'data_error', 'message': 'no such user in tb log_data'}, 400)

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