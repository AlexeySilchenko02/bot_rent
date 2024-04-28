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

#Основные кнопки
def make_reply_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    places_button = KeyboardButton("Получить информацию о местах")
    rentals_button = KeyboardButton("Мои аренды")
    feedback_button = KeyboardButton("Обратная связь")  # Новая кнопка для обратной связи
    markup.add(places_button, rentals_button, feedback_button)
    return markup

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = make_reply_keyboard()
    bot.reply_to(message, "Привет! Используй кнопки ниже.", reply_markup=markup)

# Обработчик текстовых сообщений для обработки нажатий кнопок клавиатуры
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if message.text == "Получить информацию о местах":
        send_places_info(message)
    elif message.text == "Мои аренды":
        request_phone_number(message)
    elif message.text == "Вернуться назад":
        send_welcome(message)
    elif message.text == "Обратная связь":
        request_feedback(message)
    else:
        bot.send_message(message.chat.id, "Извините, я не понял команду.")

#Кнопки которые будут вызваны после активации "Мои аренды"
def request_phone_number(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    contact_button = KeyboardButton("Поделиться номером телефона", request_contact=True)
    back_button = KeyboardButton("Вернуться назад")
    markup.add(contact_button, back_button)
    bot.send_message(message.chat.id, "Пожалуйста, поделитесь вашим номером телефона для получения информации об аренде.", reply_markup=markup)

# Функция отправки информации о местах    
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

#Получение мест аренды для данного номера телефона
@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    phone_number = message.contact.phone_number
    user_id = get_user_id_by_phone(phone_number)
    if user_id:
        send_user_rentals(message, user_id)
    else:
        bot.send_message(message.chat.id, "Извините, мы не смогли найти аренды для данного номера телефона.")

#Поиск пользователя в бд
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

#Получение списка мест пользователя из БД
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

#Обработка кнопки "Обратная связь"
@bot.message_handler(func=lambda message: message.text == "Обратная связь")
def request_feedback(message):
    msg = bot.send_message(message.chat.id, "Пожалуйста, введите ваше имя:")
    bot.register_next_step_handler(msg, process_name_step)

def process_name_step(message):
    name = message.text
    msg = bot.send_message(message.chat.id, "Введите вашу почту:")
    bot.register_next_step_handler(msg, process_email_step, name)

def process_email_step(message, name):
    email = message.text
    msg = bot.send_message(message.chat.id, "Введите тему вашего сообщения:")
    bot.register_next_step_handler(msg, process_subject_step, name, email)

def process_subject_step(message, name, email):
    subject = message.text
    msg = bot.send_message(message.chat.id, "Введите ваше сообщение:")
    bot.register_next_step_handler(msg, process_message_step, name, email, subject)

def process_message_step(message, name, email, subject):
    feedback_message = message.text
    save_feedback(name, email, subject, feedback_message)
    bot.send_message(message.chat.id, "Спасибо за ваше сообщение! Мы свяжемся с вами.")

#Отправка сообщения в БД
def save_feedback(name, email, subject, message):
    platform = "ТГ Бот"
    with pyodbc.connect(CONNECTION_STRING) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO [db_aa7919_rent].[dbo].[Feedbacks] ([Name], [Email], [Subject], [Message], [Platform], [Status])
            VALUES (?, ?, ?, ?, ?, '0')
        """, (name, email, subject, message, platform))
        conn.commit()

# Запуск бота
bot.infinity_polling()