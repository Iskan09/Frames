import os
import telebot
from PIL import Image
import io
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Инициализация бота
TOKEN = ''
bot = telebot.TeleBot(TOKEN)

# Словарь для хранения фотографий пользователей
user_photos = {}

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, 
        "Привет! Отправьте мне фотографию в формате JPEG или PNG. "
    )

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    try:
        # Получаем информацию о фото
        file_info = bot.get_file(message.photo[-1].file_id)
        
        # Проверяем размер файла
        if file_info.file_size > 10 * 1024 * 1024:  # 10 МБ
            bot.reply_to(message, "Извините, размер файла превышает 10 МБ.")
            return

        # Скачиваем фото
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Открываем изображение для проверки формата
        image = Image.open(io.BytesIO(downloaded_file))
        if image.format not in ['JPEG', 'PNG']:
            bot.reply_to(message, "Пожалуйста, отправьте фото в формате JPEG или PNG.")
            return
        
        # Сохраняем фото для конкретного пользователя
        user_photos[message.from_user.id] = {
            'photo_data': downloaded_file,
            'file_info': file_info
        }
        
        # Создаем клавиатуру с кнопками
        keyboard = InlineKeyboardMarkup()
        for i in range(1, 5):
            keyboard.add(InlineKeyboardButton(f"Рамка №{i}", callback_data=f"frame_{i}"))
        
        with open('frames/main.jpg', 'rb') as photo:
            bot.send_photo(message.chat.id, photo, caption="Выберите рамку:", reply_markup=keyboard)
        

    except Exception as e:
        bot.reply_to(message, f"Произошла ошибка при обработке фото: {str(e)}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('frame_'))
def handle_frame_selection(call):
    try:
        # Проверяем, есть ли фото для этого пользователя
        if call.from_user.id not in user_photos:
            bot.answer_callback_query(call.id, "Пожалуйста, сначала отправьте фото")
            return
            
        # Получаем номер рамки из callback_data
        frame_number = int(call.data.split('_')[1])
        
        # Получаем сохраненные данные фото
        user_data = user_photos[call.from_user.id]
        downloaded_file = user_data['photo_data']
        file_info = user_data['file_info']
        
        # Открываем изображение
        original_image = Image.open(io.BytesIO(downloaded_file))
        
        # Получаем список рамок
        frames_dir = 'frames'
        frame_files = sorted([f for f in os.listdir(frames_dir) if f.endswith(('.png', '.jpg', '.jpeg'))])
        
        if not frame_files or frame_number > len(frame_files):
            bot.answer_callback_query(call.id, "Рамка не найдена")
            return
        
        # Выбираем нужную рамку
        frame_path = os.path.join(frames_dir, frame_files[frame_number - 1])
        frame = Image.open(frame_path)
        
        # Создаем копию оригинального изображения
        resized_photo = original_image.copy()
        
        # Вычисляем соотношение сторон фото и рамки
        photo_ratio = resized_photo.width / resized_photo.height
        frame_ratio = frame.width / frame.height
        
        # Определяем, какую сторону нужно масштабировать
        if photo_ratio > frame_ratio:
            new_height = frame.height
            new_width = int(new_height * photo_ratio)
        else:
            new_width = frame.width
            new_height = int(new_width / photo_ratio)
        
        # Масштабируем фото
        resized_photo = resized_photo.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Создаем новое изображение
        result = Image.new('RGBA', frame.size, (0, 0, 0, 0))
        
        # Вычисляем позицию для центрирования
        x = (frame.width - new_width) // 2
        y = (frame.height - new_height) // 2
        
        # Вставляем фото и рамку
        result.paste(resized_photo, (x, y))
        result.paste(frame, (0, 0), frame)
        
        # Сохраняем результат
        output = io.BytesIO()
        result.save(output, format='PNG')
        output.seek(0)
        
        # Отправляем результат
        bot.send_photo(call.message.chat.id, photo=output, caption=f"Фото с рамкой №{frame_number}")
        bot.answer_callback_query(call.id)

    except Exception as e:
        bot.answer_callback_query(call.id, f"Произошла ошибка: {str(e)}")

@bot.message_handler(commands=['help'])
def help(message):
    bot.reply_to(message, 
        "Привет! В этого бота нужно отправить фотографию в формате JPEG или PNG размером не более 10 МБ. Чтобы отправлять фотографии, напишите /start"
    )

# Запуск бота
if __name__ == '__main__':
    print("Бот запущен!")
    # Удаляем вебхук перед запуском
    bot.delete_webhook()
    # Запускаем бота
    bot.polling(none_stop=True)
