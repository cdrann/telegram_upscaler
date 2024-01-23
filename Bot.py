import os
import shutil
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import ContentTypes
from dotenv import load_dotenv
import tempfile

# Функция для обработки изображений (заглушка)
def upscale_image(image_path):
    # Тут должна быть логика обработки изображения
    return image_path  # Возвращаем путь к обработанному изображению

# Загрузка токена из .env файла
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# Обработчик команды /start
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply("Привет! Отправь мне изображение, и я его обработаю.")

# Обработчик получения изображений
@dp.message_handler(content_types=ContentTypes.PHOTO)
async def handle_docs_photo(message: types.Message):
    with tempfile.TemporaryDirectory() as temp_dir:
        for photo in message.photo:
            # Сохраняем изображение во временную директорию
            image = await photo[-1].download(destination_file=os.path.join(temp_dir, f"{photo.file_id}.jpg"))

            # Обработка изображения
            processed_image_path = upscale_image(image.name)

            # Отправляем обработанное изображение обратно
            with open(processed_image_path, 'rb') as photo:
                await message.reply_photo(photo, caption="Вот обработанное изображение:")

            # Файлы удаляются автоматически при выходе из блока with

# Запуск бота
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)