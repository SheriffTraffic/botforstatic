import telebot
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# Токен бота
BOT_TOKEN = "8053486744:AAFtM6plXwfXX5gGkJGfw1_xG1Na5b8BF2w"
bot = telebot.TeleBot(BOT_TOKEN)

# Налаштування доступу до Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("lali4ka-653f000826ef.json", scope)
client = gspread.authorize(creds)

# Відкриття таблиць
try:
    general_sheet = client.open("bazaclient")
    manager_sheet = client.open("Bazaformanager")
except gspread.SpreadsheetNotFound:
    print("Таблицю не знайдено. Перевірте назви таблиць у Google Sheets.")
    exit()

# Стан користувача
user_state = {}

# Функція для отримання кнопок з іменами менеджерів
def get_manager_buttons():
    sheet_names = [sheet.title for sheet in manager_sheet.worksheets()]
    buttons = [telebot.types.KeyboardButton(name) for name in sheet_names]
    return buttons

# Функція для перевірки наявності контакту в загальній таблиці
def contact_exists(contact):
    worksheet = general_sheet.sheet1
    all_contacts = worksheet.col_values(3)  # 3-тя колонка — контакти
    return contact in all_contacts

# Функція для запису даних у таблицю
def save_to_sheet(sheet, data):
    worksheet = sheet.worksheet(data["manager"])
    last_row = len(worksheet.get_all_values()) + 1
    worksheet.append_row([last_row, data["date"], data["contact"], data["phone"], data["link"], data["service"], data["status"]])

# Хендлер для /start
@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    user_state[chat_id] = {"manager": None, "resource": None, "phone": None, "contact": None, "link": None,
                           "service": None, "status": None}

    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(*get_manager_buttons())
    bot.send_message(chat_id, "Виберіть себе 🧑‍💻:", reply_markup=markup)

# Обробка вибору менеджера
@bot.message_handler(func=lambda message: message.text in [sheet.title for sheet in manager_sheet.worksheets()])
def choose_manager(message):
    chat_id = message.chat.id
    user_state[chat_id]["manager"] = message.text
    user_state[chat_id]["date"] = datetime.now().strftime("%Y-%m-%d")

    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    resources = ["Трейдери 📈", "Крипто Адміни 👨🏻‍💻", "Внешка 📤", "Проекти 💼"]
    markup.add(*resources)
    bot.send_message(chat_id, "Виберіть ресурс 📝:", reply_markup=markup)

# Обробка вибору ресурсу
@bot.message_handler(func=lambda message: message.text in ["Трейдери 📈", "Крипто Адміни 👨🏻‍💻", "Внешка 📤", "Проекти 💼"])
def choose_resource(message):
    chat_id = message.chat.id
    user_state[chat_id]["resource"] = message.text

    if message.text in ["Внешка 📤", "Проекти 💼"]:
        bot.send_message(chat_id, "Вкажіть номер телефону ☎️:")
    else:
        bot.send_message(chat_id, "Впишіть контакт:")

# Обробка номера телефону
@bot.message_handler(func=lambda message: user_state[message.chat.id]["resource"] in ["Внешка 📤", "Проекти 💼"] and
                                          user_state[message.chat.id]["phone"] is None)
def handle_phone(message):
    chat_id = message.chat.id
    user_state[chat_id]["phone"] = message.text
    bot.send_message(chat_id, "Впишіть контакт:")

# Обробка контакту
@bot.message_handler(func=lambda message: user_state[message.chat.id]["contact"] is None)
def handle_contact(message):
    chat_id = message.chat.id
    user_state[chat_id]["contact"] = message.text

    if contact_exists(user_state[chat_id]["contact"]):
        bot.send_message(chat_id, "Цей контакт вже є у загальній базі. Будь ласка, спробуйте інший.")
        user_state[chat_id]["contact"] = None  # Очищуємо контакт, щоб попросити ще раз
    else:
        bot.send_message(chat_id, "Впишіть посилання:")

# Обробка посилання
@bot.message_handler(func=lambda message: user_state[message.chat.id]["link"] is None)
def handle_link(message):
    chat_id = message.chat.id
    user_state[chat_id]["link"] = message.text
    bot.send_message(chat_id, "Впишіть послугу:")

# Обробка послуги
@bot.message_handler(func=lambda message: user_state[message.chat.id]["service"] is None)
def handle_service(message):
    chat_id = message.chat.id
    user_state[chat_id]["service"] = message.text
    bot.send_message(chat_id, "Надайте статус:")

# Обробка статусу
@bot.message_handler(func=lambda message: user_state[message.chat.id]["status"] is None)
def handle_status(message):
    chat_id = message.chat.id
    user_state[chat_id]["status"] = message.text

    data = user_state[chat_id]

    # Зберігаємо дані в таблиці менеджера
    save_to_sheet(manager_sheet, data)

    # Зберігаємо дані в загальну таблицю
    general_worksheet = general_sheet.sheet1
    last_row = len(general_worksheet.get_all_values()) + 1
    general_worksheet.append_row([last_row, data["date"], data["contact"], data["phone"], data["link"], data["service"], data["manager"], data["status"]])

    bot.send_message(chat_id, "Дані успішно збережені! Для початку заново натисніть /start.")
    user_state[chat_id] = {}  # Очищення стану користувача

# Запуск бота
bot.infinity_polling()
