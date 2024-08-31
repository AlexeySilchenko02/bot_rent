import telebot
import pyodbc
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# Токен, который выдал BotFather
TOKEN = ''
bot = telebot.TeleBot(TOKEN)

# Строка подключения к базе данных
CONNECTION_STRING = "Driver={SQL Server};Server=SQL9001.site4now.net;Database=db_aa7919_aplicationrent;Uid=db_aa7919_aplicationrent_admin;Pwd=Alex2356;"

# Словарь для хранения состояния пользователей
user_states = {}

# Функция для извлечения информации из таблицы Place
def get_places_info():
    with pyodbc.connect(CONNECTION_STRING) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT TOP (1000) [Id], [Name], [StartRent], [EndRent], [InRent], [Price], [Description], [SizePlace], [Category]
            FROM [db_aa7919_aplicationrent].[data].[Place]
        """)
        places = cursor.fetchall()
    return places

# Основные кнопки
def make_reply_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    places_button = KeyboardButton("Места")
    personal_account_button = KeyboardButton("Личный кабинет")
    feedback_button = KeyboardButton("Обратная связь")
    markup.add(places_button, personal_account_button, feedback_button)
    return markup

# Кнопки для просмотра информации о месте и отзывах
def make_place_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    reviews_button = KeyboardButton("Посмотреть отзывы")
    back_button = KeyboardButton("Вернуться назад")
    markup.add(reviews_button, back_button)
    return markup

# Кнопки для личного кабинета
def make_personal_account_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    balance_button = KeyboardButton("Посмотреть баланс")
    transactions_button = KeyboardButton("Посмотреть транзакции")
    my_rentals_button = KeyboardButton("Мои аренды")
    back_button = KeyboardButton("Вернуться назад")
    markup.add(balance_button, transactions_button, my_rentals_button, back_button)
    return markup

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = make_reply_keyboard()
    bot.reply_to(message, "Привет! Используй кнопки ниже.", reply_markup=markup)

# Обработчик текстовых сообщений для обработки нажатий кнопок клавиатуры
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if message.text == "Места":
        send_places_info(message)
    elif message.text == "Личный кабинет":
        request_phone_number(message)
    elif message.text == "Вернуться назад":
        send_welcome(message)
    elif message.text == "Обратная связь":
        request_feedback(message)
    elif message.text == "Посмотреть отзывы":
        request_place_id(message)
    elif message.text == "Посмотреть баланс":
        send_balance_info(message)
    elif message.text == "Посмотреть транзакции":
        send_transactions_info(message)
    elif message.text == "Мои аренды":
        send_rentals_info(message)
    else:
        bot.send_message(message.chat.id, "Извините, я не понял команду.")

# Функция для запроса номера телефона пользователя
def request_phone_number(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    contact_button = KeyboardButton("Поделиться номером телефона", request_contact=True)
    back_button = KeyboardButton("Вернуться назад")
    markup.add(contact_button, back_button)
    bot.send_message(message.chat.id, "Пожалуйста, поделитесь вашим номером телефона для получения информации об аренде.", reply_markup=markup)

# Обработка номера телефона и отображение кнопок "Посмотреть баланс", "Посмотреть транзакции" и "Мои аренды"
@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    phone_number = message.contact.phone_number
    user_id = get_user_id_by_phone(phone_number)
    if user_id:
        user_states[message.chat.id] = {'phone_number': phone_number, 'user_id': user_id}
        markup = make_personal_account_keyboard()
        bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "Извините, мы не смогли найти аренды для данного номера телефона.")

# Функция отправки информации о местах
def send_places_info(message):
    places = get_places_info()
    if places:
        # Создание заголовка таблицы
        reply = "<b>Название места - Статус - Размер - Цена - Категория</b>\n"
        for i, place in enumerate(places, start=1):
            # Определение статуса места
            if place[4]:  # Если InRent == True
                start_date = place[2].split(' ')[0]  # Извлечение даты начала аренды
                end_date = place[3].split(' ')[0]  # Извлечение даты окончания аренды
                status = f"Занято с {start_date} по {end_date}"
            else:
                status = "Свободно"
            
            # Добавление информации о месте в ответ
            reply += f"{i}. {place[1]} - {status} - {place[7]} м² - {place[5]} руб. - {place[8]}\n"
        
        bot.send_message(message.chat.id, reply, parse_mode='HTML')
        markup = make_place_keyboard()
        bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "Информация о местах отсутствует.")

# Функция для получения ID пользователя по номеру телефона
def get_user_id_by_phone(phone_number):
    phone_number = phone_number.lstrip('+')
    with pyodbc.connect(CONNECTION_STRING) as conn:
        cursor = conn.cursor()
        # Пытаемся найти номер с "+" и без него
        cursor.execute("""
            SELECT [Id] FROM [db_aa7919_aplicationrent].[dbo].[AspNetUsers]
            WHERE REPLACE([PhoneNumber], '+', '') = ?
        """, phone_number)
        result = cursor.fetchone()
    return result[0] if result else None

# Функция для отправки информации о балансе пользователя
def send_balance_info(message):
    user_state = user_states.get(message.chat.id)
    if user_state:
        user_id = user_state['user_id']
        with pyodbc.connect(CONNECTION_STRING) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT [Balance] FROM [db_aa7919_aplicationrent].[dbo].[AspNetUsers]
                WHERE [Id] = ?
            """, user_id)
            result = cursor.fetchone()
        if result:
            bot.send_message(message.chat.id, f"Ваш баланс: {result[0]} руб.")
        else:
            bot.send_message(message.chat.id, "Извините, не удалось получить баланс.")
    else:
        bot.send_message(message.chat.id, "Извините, не удалось найти пользователя.")

# Функция для отправки информации о транзакциях пользователя
def send_transactions_info(message):
    user_state = user_states.get(message.chat.id)
    if user_state:
        user_id = user_state['user_id']
        with pyodbc.connect(CONNECTION_STRING) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT [Amount], [TransactionDate] FROM [db_aa7919_aplicationrent].[dbo].[TransactionHistories]
                WHERE [UserId] = ?
                ORDER BY [TransactionDate] DESC
            """, user_id)
            transactions = cursor.fetchall()
        if transactions:
            reply = "<b>Ваши транзакции:</b>\n"
            for transaction in transactions:
                date = transaction[1].split(' ')[0]  # Используем строковое представление даты
                reply += f"{date}: {transaction[0]} руб.\n"
            bot.send_message(message.chat.id, reply, parse_mode='HTML')
        else:
            bot.send_message(message.chat.id, "У вас нет транзакций.")
    else:
        bot.send_message(message.chat.id, "Извините, не удалось найти пользователя.")

# Функция для отправки информации о текущих арендах пользователя
def send_rentals_info(message):
    user_state = user_states.get(message.chat.id)
    if user_state:
        user_id = user_state['user_id']
        with pyodbc.connect(CONNECTION_STRING) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.[Name], r.[StartRent], r.[EndRent], p.[Price]
                FROM [db_aa7919_aplicationrent].[dbo].[Rentals] r
                JOIN [db_aa7919_aplicationrent].[data].[Place] p ON r.[PlaceId] = p.[Id]
                WHERE r.[UserId] = ? AND r.[EndRent] > GETDATE()
                ORDER BY r.[StartRent] DESC
            """, user_id)
            rentals = cursor.fetchall()
        if rentals:
            reply = "<b>Ваши аренды:</b>\n"
            for rental in rentals:
                start_date = rental[1].split(' ')[0]  # Используем строковое представление даты
                end_date = rental[2].split(' ')[0]  # Используем строковое представление даты
                reply += f"{rental[0]} - С {start_date} по {end_date} - {rental[3]} руб.\n"
            bot.send_message(message.chat.id, reply, parse_mode='HTML')
        else:
            bot.send_message(message.chat.id, "У вас нет текущих аренд.")
    else:
        bot.send_message(message.chat.id, "Извините, не удалось найти пользователя.")

# Обработка кнопки "Обратная связь"
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

# Отправка сообщения в БД
def save_feedback(name, email, subject, message):
    platform = "ТГ Бот"
    with pyodbc.connect(CONNECTION_STRING) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO [db_aa7919_aplicationrent].[dbo].[Feedbacks] ([Name], [Email], [Subject], [Message], [Platform], [Status])
            VALUES (?, ?, ?, ?, ?, '0')
        """, (name, email, subject, message, platform))
        conn.commit()

# Функция для запроса ID места у пользователя
def request_place_id(message):
    msg = bot.send_message(message.chat.id, "Введите номер места для просмотра отзывов:")
    bot.register_next_step_handler(msg, send_reviews_info)

# Функция для отправки отзывов о месте
def send_reviews_info(message):
    place_index = int(message.text) - 1  # Минус один, так как индекс в списке начинается с нуля
    places = get_places_info()
    if 0 <= place_index < len(places):
        place_id = places[place_index][0]
        reviews = get_reviews_by_place_id(place_id)
        if reviews:
            reply = "<b>Последние отзывы:</b>\n"
            for review in reviews:
                reply += f"{review[0]}: {review[1]} (Оценка: {review[2]}/10)\n"
            bot.send_message(message.chat.id, reply, parse_mode='HTML')
        else:
            bot.send_message(message.chat.id, "Отзывов нет.")
    else:
        bot.send_message(message.chat.id, "Неверный номер места. Пожалуйста, попробуйте снова.")

# Функция для получения отзывов по ID места
def get_reviews_by_place_id(place_id):
    with pyodbc.connect(CONNECTION_STRING) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT [Name], [Comment], [Rating]
            FROM [db_aa7919_aplicationrent].[dbo].[Reviews]
            WHERE [PlaceId] = ?
            ORDER BY [Id] DESC
            OFFSET 0 ROWS FETCH NEXT 20 ROWS ONLY
        """, place_id)
        reviews = cursor.fetchall()
    return reviews

# Запуск бота
bot.infinity_polling()
