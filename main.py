import asyncio
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from confing import TOKEN

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command('help'))

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer("Приветики, я бот!")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
