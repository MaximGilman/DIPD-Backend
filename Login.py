import dotenv
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

load_dotenv("connect.env")

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
    requires = ["login", "password"]
    
    check = CheckInputs(inputs, requires)
    if check != 'passed':
        return check

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

# Метод получения пользователя
def GetUser():

    inputs = request.get_json()

    requires = ["login", "password"]

    check = CheckInputs(inputs, requires)
    if check != 'passed':
        return check

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
            return user 

# Проверка входных данных (json)
def CheckInputs(inputs, requires):
    for param in requires:
            if param not in inputs:
                return ({'status': 'data_error', 'message': f'{param} expected'}, 400)
    return 'passed'
# Проверка на существование логина в таблице log_data
def CheckLogin():

    inputs = request.get_json()

    if ('login' not in inputs):
        return ({'status': 'data_error', 'message': 'login expected'}, 400)

    login = inputs['login']

    with con:
        cur = con.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
        query = f"SELECT key FROM public.log_data WHERE login = \'{login}\'"
        cur.execute(query)

        loginKey = cur.fetchone()

        return json.dumps(loginKey)

# Метод обновления существующей записи
@app.route('/user/update', methods=['POST'])
def UpdateUser():

    inputs = request.get_json() # получаем данные из запроса

    requires = ['key', 'name', 'password', 'login', 'email'] # обязательные параметры запроса

    for param in requires:
        if param not in inputs:
            return ({'status': 'data_error', 'message': f'{param} expected'}, 400)

    key = inputs['key']
    name = inputs['name']
    password = inputs['password']
    login = inputs['login']
    email = inputs['email']

    with con:

        cur = con.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
        query = f"SELECT name, login_id FROM public.user WHERE key = \'{key}\'" # получили имя пользователя и логин_ид 
        cur.execute(query)

        user = cur.fetchone()
        userCopy = user
        user = json.dumps(user)

        if user != 'null':
            loginKey = userCopy["login_id"] #логин_ид 
            query = f"UPDATE public.user SET (name, email) = (\'{name}\', \'{email}\') WHERE key =\'{key}\'" #обновляем имя и почту пользователя
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

    requires = ['name', 'password', 'login', 'email'] # обязательные параметры запроса

    check = CheckInputs(inputs, requires)
    if check != 'passed':
        return check

    name = inputs['name']
    password = inputs['password']
    login = inputs['login']
    email = inputs['email']
    
    requiresInput = dict(zip(['name', 'password', 'login', 'email'],[name, password, login, email]))

    # Сообщение об отсутствии заполнения данных. Пока что выводит только для одного поля
    # Если отсутствует больше 1 поля, выводит сообщение только про первое прочитанное
    for input in requiresInput:
        if requiresInput[input] == "":
            return ({'status': 'data_error', 'message': f'value for {input} expected'}, 400)

    userCheck = GetUser() #пытаемся найти пользователя по логину и паролю

    loginCheck = CheckLogin()
    # Если userCheck не нашёл существующей записи о пользователе и loginCheck не нашёл логин  
    if ("key" not in userCheck) and (loginCheck == "null"):
        with con:
            cur = con.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
            query = f"INSERT INTO public.log_data (login, password) VALUES (\'{login}\', \'{password}\')"
            cur.execute(query)

            # Получаем key пользователя из log_data
            query = f"SELECT key FROM public.log_data WHERE (login, password) = (\'{login}\', \'{password}\')"
            cur.execute(query)
            loginKey = cur.fetchone()["key"]
            
            # Создаём запись в user
            query = f"INSERT INTO public.user (name, login_id, email) VALUES (\'{name}\', \'{loginKey}\', \'{email}\')"
            cur.execute(query)

            return {"status":"check"}
    else:
        return ({'status': 'data_found', 'message': 'there`s already user in tb user'}, 412)

# Метод удаления пользователя
@app.route('/user/delete', methods=['POST'])
def DeleteUser():

    inputs = request.get_json() # получаем данные из запроса

    key = inputs['key']

    requires = ['key', 'password', 'login'] # обязательные параметры запроса

    check = CheckInputs(inputs, requires)
    if check != 'passed':
        return check
    
    userCheck = GetUser()

    # Проверка, что запись есть в log_data
    if "key" in userCheck:
        loginKey = userCheck["key"]
        # Проверка, что запись есть в user
        if GetUserById(loginKey) != "null":
            key = GetUser()['login_id']
            with con:
                cur = con.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
                #query = f"DELETE FROM public.profile_pic WHERE user_key = \'{loginKey}\'"
                #cur.execute(query)

                #query = f"DELETE FROM public.user WHERE key = \'{loginKey}\'"
                #ur.execute(query)

                query = f"DELETE FROM public.log_data WHERE key = \'{key}\'"
                cur.execute(query)
                
                return{'status': 'OK', 'message': 'user deleted'}
                
        else:
            return ({'status': 'data_error', 'message': 'no such user in tb user'}, 400)    
    else:
        return ({'status': 'data_error', 'message': 'no such user in tb log_data'}, 400)


# Метод добавления массива байт в табилцу profile_pic. Если запись существет - удалить и создать 
@app.route('/image/set', methods=['POST'])
def SetImage():
    inputs = request.get_json() # получаем данные из запроса

    requires = ['key', 'bytearray'] # обязательные параметры запроса

    check = CheckInputs(inputs, requires)
    if check != 'passed':
        return check

    key = inputs['key']
    # массив байт
    imgbyte = inputs['bytearray']
    # проверка, что пользователь существует
    if GetUserById(key) != "null":
        with con:
            cur = con.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
            query = f"SELECT * FROM public.profile_pic WHERE user_key = {key}"
            cur.execute(query)
            # если нашлась запись
            if cur.fetchone() != 'null':
                query = f"DELETE FROM public.profile_pic WHERE user_key = \'{key}\'"
                cur.execute(query)
                query = f"INSERT INTO public.profile_pic (user_key, image) VALUES (\'{key}\', \'{imgbyte}\')"
                cur.execute(query)
                return {"status":"check"}
            else:
                query = f"INSERT INTO public.profile_pic (user_key, image) VALUES (\'{key}\', \'{imgbyte}\')"
                cur.execute(query)
                return {"status":"check"}
    else:
        return ({'status': 'data_error', 'message': 'no such user in tb user'}, 400)

# Метод получения массива байт (фото профиля)
@app.route('/image/<id>', methods=['GET'])
def GetImageById(id):
    with con:
        cur = con.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
        query = f"SELECT image FROM public.profile_pic WHERE user_key = {id}"
        cur.execute(query)
        # объект memoryview в tuple
        mview = tuple(cur.fetchone().items())
        # memoryview в bytes
        new_bin_data=bytes(mview[0][1])
        #возвращает массив байт
        return new_bin_data

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



# Logout пользователя - делать не нужно, сделаем со стороны клиента
# Опубликовать это на стенде - делать не нужно, сделаем это, когда будет готова реализация
