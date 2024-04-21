import telebot
import pyodbc
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# Токен, который выдал BotFather
TOKEN = '7002641960:AAGFGouyZOs57f_1XczDXwSxSHwEIf3IYXI'
bot = telebot.TeleBot(TOKEN)

# Строка подключения к базе данных
CONNECTION_STRING = "Driver={SQL Server};Server=SQL9001.site4now.net;Database=db_aa7919_rent;Uid=db_aa7919_rent_admin;Pwd=Alex2356;"

# Функция для извлечения информации из таблицы Place
def get_places_info():
    with pyodbc.connect(CONNECTION_STRING) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT TOP (1000) [Id], [Name], [StartRent], [EndRent], [InRent], [Price], [Description], [SizePlace]
            FROM [db_aa7919_rent].[data].[Place]
        """)
        places = cursor.fetchall()
    return places

def make_reply_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    places_button = KeyboardButton("Получить информацию о местах")
    rentals_button = KeyboardButton("Мои аренды")
    markup.add(places_button, rentals_button)
    return markup

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = make_reply_keyboard()
    bot.reply_to(message, "Привет! Используй кнопку ниже, чтобы получить информацию о местах.", reply_markup=markup)

# Обработчик текстовых сообщений для обработки нажатий кнопок клавиатуры
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if message.text == "Получить информацию о местах":
        send_places_info(message)
    elif message.text == "Мои аренды":  # Обработка запроса "Мои аренды"
        request_phone_number(message)
    else:
        bot.send_message(message.chat.id, "Извините, я не понял команду.")

def request_phone_number(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    contact_button = KeyboardButton("Поделиться номером телефона", request_contact=True)
    markup.add(contact_button)
    bot.send_message(message.chat.id, "Пожалуйста, поделитесь вашим номером телефона для получения информации об аренде.", reply_markup=markup)


# Функция отправки информации о местах, без изменений      
def send_places_info(message):
    places = get_places_info()
    if places:
        # Создание заголовка таблицы
        reply = "<b>Название места - Статус - Размер - Цена</b>\n"
        for place in places:
            # Определение статуса места
            if place[4]:  # Если InRent == True
                start_date = place[2].split(' ')[0]  # Извлечение даты начала аренды
                end_date = place[3].split(' ')[0]  # Извлечение даты окончания аренды
                status = f"Занято с {start_date} по {end_date}"
            else:
                status = "Свободно"
            
            # Добавление информации о месте в ответ
            reply += f"{place[1]} - {status} - {place[7]} м² - {place[5]} руб.\n"
        
        bot.send_message(message.chat.id, reply, parse_mode='HTML')
    else:
        bot.send_message(message.chat.id, "Информация о местах отсутствует.")


@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    phone_number = message.contact.phone_number
    user_id = get_user_id_by_phone(phone_number)
    if user_id:
        send_user_rentals(message, user_id)
    else:
        bot.send_message(message.chat.id, "Извините, мы не смогли найти аренды для данного номера телефона.")

def get_user_id_by_phone(phone_number):
    phone_number = phone_number.lstrip('+')
    with pyodbc.connect(CONNECTION_STRING) as conn:
        cursor = conn.cursor()
        # Пытаемся найти номер с "+" и без него
        cursor.execute("""
            SELECT [Id] FROM [db_aa7919_rent].[dbo].[AspNetUsers]
            WHERE REPLACE([PhoneNumber], '+', '') = ?
        """, phone_number)
        result = cursor.fetchone()
    return result[0] if result else None


def send_user_rentals(message, user_id):
    with pyodbc.connect(CONNECTION_STRING) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.[Name], r.[StartRent], r.[EndRent], p.[SizePlace], p.[Price]
            FROM [db_aa7919_rent].[dbo].[Rentals] r
            JOIN [db_aa7919_rent].[data].[Place] p ON r.[PlaceId] = p.[Id]
            WHERE r.[UserId] = ? AND r.[EndRent] >= GETDATE()
        """, user_id)
        rentals = cursor.fetchall()
    
    if rentals:
        reply = "<b>Ваши актуальные аренды:</b>\n"
        for rental in rentals:
            start_date = rental[1].split(' ')[0]
            end_date = rental[2].split(' ')[0]
            reply += f"{rental[0]} - Занято с {start_date} по {end_date} - {rental[3]} м² - {rental[4]} руб.\n"
        bot.send_message(message.chat.id, reply, parse_mode='HTML')
    else:
        bot.send_message(message.chat.id, "У вас нет текущих аренд или все аренды истекли.")

# Запуск бота
bot.infinity_polling()