import asyncio
import logging
import sqlite3
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message
import aiohttp  # Добавлен импорт aiohttp

from confing import TOKEN, WEATHER_API_KEY

# Инициализация логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера с хранилищем состояний
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Определение состояний формы
class Form(StatesGroup):
    name = State()
    age = State()
    city = State()

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect('user_data.db')
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        age INTEGER NOT NULL,
        city TEXT NOT NULL
    )
    ''')
    conn.commit()
    conn.close()

init_db()

# Обработчик команды /start
@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await message.answer("Привет! Как тебя зовут?")
    await state.set_state(Form.name)

# Обработчик состояния Form.name
@dp.message(Form.name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Сколько тебе лет?")
    await state.set_state(Form.age)

# Обработчик состояния Form.age
@dp.message(Form.age)
async def process_age(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введи корректный возраст (число).")
        return
    await state.update_data(age=int(message.text))
    await message.answer("Из какого ты города?")
    await state.set_state(Form.city)

# Обработчик состояния Form.city
@dp.message(Form.city)
async def process_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    user_data = await state.get_data()

    # Сохранение данных в базу данных
    try:
        conn = sqlite3.connect('user_data.db')
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO users (name, age, city) VALUES (?, ?, ?)
        ''', (user_data['name'], user_data['age'], user_data['city']))
        conn.commit()
        conn.close()

        # Получение данных о погоде
        async with aiohttp.ClientSession() as session:
            async with session.get(f"http://api.openweathermap.org/data/2.5/weather?q={user_data['city']}&appid={WEATHER_API_KEY}&units=metric&lang=ru") as response:
                if response.status == 200:
                    weather_data = await response.json()
                    main = weather_data['main']
                    weather = weather_data['weather'][0]

                    temperature = main['temp']
                    humidity = main['humidity']
                    description = weather['description']

                    weather_report = (f"Город - {user_data['city']}\n"
                                      f"Температура - {temperature}°C\n"
                                      f"Влажность воздуха - {humidity}%\n"
                                      f"Описание погоды - {description}")

                    # Отправка отчета о погоде пользователю
                    await message.answer(weather_report)
                else:
                    await message.answer("Не удалось получить данные о погоде. Попробуйте позже.")

        await message.answer("Спасибо! Твои данные сохранены.")
    except Exception as e:
        logging.error(f"Ошибка при сохранении данных: {e}")
        await message.answer("Произошла ошибка при сохранении данных. Попробуй позже.")

    # Завершение состояния
    await state.clear()

# Обработчик команды /help
@dp.message(Command('help'))
async def help_command(message: Message):
    await message.answer("Этот бот умеет выполнять команды:\n/start\n/help")

# Основная функция запуска бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
