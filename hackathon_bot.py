from selenium import webdriver
from selenium.webdriver.common.by import By
import telebot
import json
from bot_token import token
from random import randint
import json
import requests

from time import sleep

HOST = 'http://127.0.0.1:8000/market/books/'
GENRE = 'http://127.0.0.1:8000/market/genres/'
HEADERS = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'}


def get_html(url: str, headers: dict='', params: str=''):
    """ Функция для получения html кода """
    html = requests.get(
        url,
        headers=headers,
        params=params,
        verify=False
    )
    return html.text

html = get_html(HOST)
def get_db(db):
    with open(f'{db}.json', 'r') as file:
        return json.load(file)

def write_db(db,data):
    with open(f'{db}.json', 'w') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def get_last_page():
    url = 'http://127.0.0.1:8000/market/books/'
    driveru = webdriver.Chrome(executable_path='/home/hello/dies_irae_bot/chromedriver')
    driveru.get(url=url)
    a = driveru.find_element(By.XPATH, value='//*[@id="content"]/div[2]/nav/ul/li[6]/a').text
    return int(a)


def list_(html):
    a = html.split('results":')[1].lstrip('[')[:-2]
    testy = a.strip('[').strip(']').replace('},', '\n').replace('"', '').replace('{', '').replace('}', '').split('\n')
    result = []
    for i in testy:
        title = i.split('title:')[1].split(',author:')[0].split(',genre')[0]
        author = i.split(',author:')[1].split(',')[0]
        price =i.split(',price:')[1].split(',')[0]
        data = {
            'title': title,
            'author': author,
            'price': price
        }
        result.append(data)
    return result


def full_parse():
    result = []
    for page in range(11):
        if page > 0:
            HOST = f'http://127.0.0.1:8000/market/books/?page={page}'
            html = get_html(HOST, HEADERS)
            dict_ = list_(html)
            result.extend(dict_)
    return result


bot = telebot.TeleBot(token)

def full_parse_find(msg_text):
    result = []
    try:
        for page in range(11):
            if page > 0:
                HOST = f'http://127.0.0.1:8000/market/books/?page={page}&q={msg_text}'
                html = get_html(HOST, HEADERS)
                dict_ = list_(html)
                result.extend(dict_)
            write_db('test', result)
    except:
        pass
    return result


@bot.message_handler(commands=['del'])
def start_message(message):
    chat_id = message.chat.id
    msg = bot.send_message(chat_id, 'Название книги, которую надо удалить:')
    bot.register_next_step_handler(msg, full_find_del)


@bot.message_handler(commands=['help'])
def start_message(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, """
Список команд бота:
/random - случайная книга
/find - поиск книги 
/help - помощь
    """)

@bot.message_handler(commands=['admin'])
def start_message(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, """
Список команд для администратора:
/add_book - добавить книгу
/del - удалить книгу 
/admin - помощь
    """)


@bot.message_handler(commands=['random'])
def start_message(message):
    books = full_parse()
    num = randint(0, len(books))
    chat_id = message.chat.id
    dict_ = f"""
Книга: {books[num]['title']} \n
Автор: {books[num]['author']} \n
Цена: {books[num]['price']} сом
    """
    bot.send_message(chat_id, dict_)


@bot.message_handler(commands=['find'])
def start_message(message):
    chat_id = message.chat.id
    msg = bot.send_message(chat_id, 'Отправь мне название книги и я поищу его (◕‿◕✿)')
    bot.register_next_step_handler(msg, find)


def find(message):
    chat_id = message.chat.id
    msg_text = message.text
    write_db('user', msg_text)
    html = get_html(HOST, HEADERS)
    if len(msg_text) > 2:
        books = full_parse_find(msg_text)
        if books:
            for book in books:
                dict_ = f"""
Книга: {book['title']} \n
Автор: {book['author']} \n
Цена: {book['price']} сом
                """
                bot.send_message(chat_id, dict_)
                if int(len(books)) > 1:
                    msg = bot.send_message(chat_id, f'Найдено ещё {int(len(books))-1} совпадений.\nПоказать некоторые совпадения(макс. 5)\n(Да\Нет)')
                    bot.register_next_step_handler(msg, full_find)
                break
        else:
            bot.send_message(chat_id, 'Упс, кажется я ничего подходящего не нашел (⁄ ⁄•⁄ω⁄•⁄ ⁄)')
            bot.send_sticker(chat_id, 'CAACAgIAAxkBAAEGgpZjfQ34DWlazZ0pOrFddLeNirXcZgACEgADdJypFjoE3jbqKm1pKwQ')
    else:
        bot.send_message(chat_id, 'Введите минимум 3 символа (⁄ ⁄•⁄ω⁄•⁄ ⁄)')


def full_find_del(message):
    chat_id = message.chat.id
    msg_text = message.text
    write_db('user', msg_text)
    db = get_db('user')
    books = full_parse_find(msg_text)
    for book in books:
        dict_ = f"""
Книга: {book['title']} \n
Автор: {book['author']} \n
Цена: {book['price']} сом
            """
        print(dict_)
        bot.send_message(chat_id, dict_)
    if not books:
        bot.send_message(chat_id, 'Книга не найдена.\nПопробуйте уточнить запрос.')
    if books:
        msg = bot.send_message(chat_id, 'Уточните запрос, если не нашли нужной книги.\nУточните запрос для удаление одной книги.\nУдалить все найденные книги?\n(Удалить/Нет)')
        bot.register_next_step_handler(msg, del_books_sel)


def full_find(message):
    chat_id = message.chat.id
    msg_text = message.text
    db = get_db('user')
    num = 0
    if msg_text.lower() == 'да':
        books = full_parse_find(db)[1:]
        for book in books:
            num +=1
            if num < 5:
                dict_ = f"""
Книга: {book['title']} \n
Автор: {book['author']} \n
Цена: {book['price']} сом
                """
                bot.send_message(chat_id, dict_)
    bot.send_message(chat_id, 'Уточните запрос, если не нашли нужной книги.')


@bot.message_handler(commands=['add_book'])
def start_message(message):
    chat_id = message.chat.id
    db = get_db('book')
    if db['id'] == message.from_user.id:
        msg = bot.send_message(chat_id, 'Название Книги:')
        bot.register_next_step_handler(msg, book_title)
    else:
        msg = bot.send_message(chat_id, 'Этой функция только для администраторов!')


def book_title(message):
    chat_id = message.chat.id
    text_ = message.text
    db = get_db('book') 
    db['title'] = text_
    write_db('book', db)
    msg = bot.send_message(chat_id, 'Автор:')
    bot.register_next_step_handler(msg, book_author)
    

def book_author(message):
    chat_id = message.chat.id
    text_ = message.text
    db = get_db('book') 
    db['author'] = text_
    write_db('book', db)
    msg = bot.send_message(chat_id, 'Жанр:')
    bot.register_next_step_handler(msg, book_genre)


def book_genre(message):
    chat_id = message.chat.id
    text_ = message.text
    db = get_db('book') 
    db['genre'] = text_
    write_db('book', db)
    msg = bot.send_message(chat_id, 'Описание:')
    bot.register_next_step_handler(msg, book_desc)



def book_desc(message):
    chat_id = message.chat.id
    text_ = message.text
    db = get_db('book') 
    db['desc'] = text_
    write_db('book', db)
    msg = bot.send_message(chat_id, 'Год выпуска:')
    bot.register_next_step_handler(msg, book_year)


def book_year(message):
    chat_id = message.chat.id
    text_ = message.text
    db = get_db('book')
    try:
        if int(text_) > 0 and int(text_) <= 2022:
            db['year'] = text_
            write_db('book', db)
            msg = bot.send_message(chat_id, 'Цена:')
            bot.register_next_step_handler(msg, book_price)
        else:
            msg = bot.send_message(chat_id, 'Напишите корректный год:')
            bot.register_next_step_handler(msg, book_year)
    except ValueError:
        msg = bot.send_message(chat_id, 'Напишите корректный год:')
        bot.register_next_step_handler(msg, book_year)


def book_price(message):
    chat_id = message.chat.id
    text_ = message.text
    db = get_db('book')
    try:
        db['price'] = int(text_)
        write_db('book', db)
        msg = bot.send_message(chat_id, 'Количество страниц:')
        bot.register_next_step_handler(msg, book_page)
    except ValueError:
        msg = bot.send_message(chat_id, 'Используйте только цифры.')
        bot.register_next_step_handler(msg, book_price)

def book_page(message):
    chat_id = message.chat.id
    text_ = message.text
    db = get_db('book')
    try:
        db['page'] = int(text_)
        write_db('book', db)
        msg = bot.send_message(chat_id, 'Вес(г):')
        bot.register_next_step_handler(msg, book_weight)
    except ValueError:
        msg = bot.send_message(chat_id, 'Используйте только цифры.')
        bot.register_next_step_handler(msg, book_page)


def book_weight(message):
    chat_id = message.chat.id
    text_ = message.text
    db = get_db('book') 
    try:
        db['weight'] = int(text_)
        write_db('book', db)
        msg = bot.send_message(chat_id, 'Книг в наличии:')
        bot.register_next_step_handler(msg, book_stock)
    except ValueError:
        msg = bot.send_message(chat_id, 'Используйте только цифры.')
        bot.register_next_step_handler(msg, book_weight)


def book_stock(message):
    chat_id = message.chat.id
    text_ = message.text
    db = get_db('book') 
    try:
        db['stock'] = int(text_)
        write_db('book', db)
        msg = bot.send_message(chat_id, f"""Ваша книга:\n
Название: {db['title']}
Автор: {db['author']}
Жанр: {db['genre']}
Описание: {db['desc']}
Год выпуска: {db['year']}
Цена: {db['price']}
Страниц: {db['page']}
Вес: {db['weight']}
В наличии: {db['stock']}
    """)
        msg = bot.send_message(chat_id, 'Хотите добавить книгу?\n(Добавить/Нет)')
        bot.register_next_step_handler(msg, add_book_sel)
    except ValueError:
        msg = bot.send_message(chat_id, 'Используйте только цифры.')
        bot.register_next_step_handler(msg, book_stock)


def add_book_sel(message):
    chat_id = message.chat.id
    text_ = message.text
    if text_.lower() == 'добавить':
        db = get_db('book')
        url = 'http://127.0.0.1:8000/admin/'
        driveru = webdriver.Chrome(executable_path='/home/hello/hackathon_bot/chromedriver')
        driveru.get(url=url)    
        log_admin = driveru.find_element(By.XPATH, value='//*[@id="id_username"]').send_keys('admin')
        log_admin = driveru.find_element(By.XPATH, value='//*[@id="id_password"]').send_keys('1')
        open = driveru.find_element(By.XPATH, value='//*[@id="login-form"]/div[3]/input').click()
        add_book = driveru.find_element(By.XPATH, value='//*[@id="content-main"]/div[2]/table/tbody/tr[2]/td[1]/a').click()
        user = driveru.find_element(By.XPATH, value='//*[@id="id_user"]/option[3]').click()
        genre = driveru.find_element(By.XPATH, value='//*[@id="id_genre"]/option[2]').click()
        author =driveru.find_element(By.XPATH, value='//*[@id="id_author"]').send_keys(db['author'])
        title = driveru.find_element(By.XPATH, value='//*[@id="id_title"]').send_keys(db['title'])
        desc = driveru.find_element(By.XPATH, value='//*[@id="id_description"]').send_keys(db['desc'])
        year = driveru.find_element(By.XPATH, value='//*[@id="id_year"]').send_keys(db['year'])
        price = driveru.find_element(By.XPATH, value='//*[@id="id_price"]').send_keys(db['price'])
        page = driveru.find_element(By.XPATH, value='//*[@id="id_pages"]').send_keys(db['page'])
        weight = driveru.find_element(By.XPATH, value='//*[@id="id_weight"]').send_keys(db['weight'])
        stock = driveru.find_element(By.XPATH, value='//*[@id="id_stock"]').send_keys(db['stock'])
        add = driveru.find_element(By.XPATH, value='//*[@id="book_form"]/div/div[2]/input[1]').click()
        bot.send_message(chat_id, 'Успешно добавлено!')
    if text_.lower() == 'нет':
        bot.send_message(chat_id, 'Успешно отменено')


def del_books_sel(message):
    chat_id = message.chat.id
    msg_text = message.text
    if msg_text.lower() == 'удалить':
        db = get_db('user')
        url = 'http://127.0.0.1:8000/admin/'
        driveru = webdriver.Chrome(executable_path='/home/hello/hackathon_bot/chromedriver')
        driveru.get(url=url)    
        log_admin = driveru.find_element(By.XPATH, value='//*[@id="id_username"]').send_keys('admin')
        log_admin = driveru.find_element(By.XPATH, value='//*[@id="id_password"]').send_keys('1')
        open = driveru.find_element(By.XPATH, value='//*[@id="login-form"]/div[3]/input').click()
        driveru.find_element(By.XPATH, value='//*[@id="content-main"]/div[2]/table/tbody/tr[2]/td[2]/a').click()
        driveru.find_element(By.XPATH, value='//*[@id="searchbar"]').send_keys(db)
        driveru.find_element(By.XPATH, value='//*[@id="changelist-search"]/div/input[2]').click()
        driveru.find_element(By.XPATH, value='//*[@id="action-toggle"]').click()
        driveru.find_element(By.XPATH, value='//*[@id="changelist-form"]/div[2]/label/select/option[2]').click()
        driveru.find_element(By.XPATH, value='//*[@id="changelist-form"]/div[2]/button').click()
        bot.send_message(chat_id, 'Успешно удалено!')
        sleep(3)
        driveru.find_element(By.XPATH, value='//*[@id="content"]/form/div/input[4]').click()
    else:
        bot.send_message(chat_id, 'Действие отменено')


def get_genre():
    html = get_html(GENRE, HEADERS)
    a = html.split('results":')[1].lstrip('[')[:-2]
    testy = a.replace("{", '').replace('},', '\n').replace('"', '').replace('}', '').split('\n')
    result = []
    for i in testy:
        obj = {
            'genres': i.split(',')[0].split('title:')[1]
        }
        result.append(obj)
    return result
       


bot.polling()






