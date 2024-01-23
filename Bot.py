from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import ContentTypes, InputMediaPhoto
# from aiogram_media_group import media_group_handler
# from aiogram_media_group.filters import MediaGroupFilter
from typing import List

from dotenv import load_dotenv

import tempfile
import os

# Mock func
def upscale_image(image_path):
    return image_path

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply("Привет! Отправь мне изображение, и я его обработаю.")



# # Обработчик альбомов
# @dp.message_handler(MediaGroupFilter(is_media_group=True), content_types=types.ContentType.PHOTO)
# @media_group_handler
# async def album_handler(messages: List[types.Message]):
#     processed_photos = []
#     for message in messages:
#         highest_quality_photo = message.photo[-1]
#         file_info = await bot.get_file(highest_quality_photo.file_id)
#         file_path = await bot.download_file(file_info.file_path)
#         processed_image_path = upscale_image(file_path)
#         processed_photos.append(InputMediaPhoto(open(processed_image_path, 'rb')))

#     await bot.send_media_group(messages[0].chat.id, processed_photos)

        

# Обработчик отдельных фотографий
@dp.message_handler(content_types=ContentTypes.PHOTO)
async def handle_docs_photo(message: types.Message):
    highest_quality_photo = message.photo[-1]

    with tempfile.TemporaryDirectory() as temp_dir:
        
        file_info = await bot.get_file(highest_quality_photo.file_id)
        file_path = os.path.join(temp_dir, file_info.file_path.split('/')[-1])
        await bot.download_file(file_info.file_path, file_path)

        processed_image_path = upscale_image(file_path)

        with open(processed_image_path, 'rb') as photo:
            await message.reply_photo(photo, caption="Вот обработанное изображение:")


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)