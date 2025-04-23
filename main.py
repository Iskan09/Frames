import os
import telebot
from PIL import Image
import io

# Инициализация бота
TOKEN = '6553315261:AAGxCUTqGfce74Lsq1omWDTvhq2fCWLeqLM'
bot = telebot.TeleBot(TOKEN)

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
        
        # Открываем изображение
        original_image = Image.open(io.BytesIO(downloaded_file))
        
        # Проверяем формат
        if original_image.format not in ['JPEG', 'PNG']:
            bot.reply_to(message, "Пожалуйста, отправьте фото в формате JPEG или PNG.")
            return

        # Получаем список рамок из папки frames
        frames_dir = 'frames'
        if not os.path.exists(frames_dir):
            bot.reply_to(message, "Папка с рамками не найдена.")
            return

        frame_files = [f for f in os.listdir(frames_dir) if f.endswith(('.png', '.jpg', '.jpeg'))]
        
        if not frame_files:
            bot.reply_to(message, "В папке frames нет подходящих рамок.")
            return

        # Счетчик для нумерации рамок
        frame_counter = 1
        
        # Обрабатываем каждую рамку
        for frame_file in frame_files:
            frame_path = os.path.join(frames_dir, frame_file)
            frame = Image.open(frame_path)
            
            # Создаем копию оригинального изображения
            resized_photo = original_image.copy()
            
            # Вычисляем соотношение сторон фото и рамки
            photo_ratio = resized_photo.width / resized_photo.height
            frame_ratio = frame.width / frame.height
            
            # Определяем, какую сторону нужно масштабировать
            if photo_ratio > frame_ratio:
                # Фото шире рамки - масштабируем по высоте
                new_height = frame.height
                new_width = int(new_height * photo_ratio)
            else:
                # Фото выше рамки - масштабируем по ширине
                new_width = frame.width
                new_height = int(new_width / photo_ratio)
            
            # Масштабируем фото с сохранением пропорций
            resized_photo = resized_photo.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Создаем новое изображение с прозрачным фоном
            result = Image.new('RGBA', frame.size, (0, 0, 0, 0))
            
            # Вычисляем позицию для центрирования фото
            x = (frame.width - new_width) // 2
            y = (frame.height - new_height) // 2
            
            # Вставляем фото в центр
            result.paste(resized_photo, (x, y))
            
            # Добавляем рамку
            result.paste(frame, (0, 0), frame)
            
            # Сохраняем результат
            output = io.BytesIO()
            result.save(output, format='PNG')
            output.seek(0)
            
            # Отправляем результат
            bot.send_photo(message.chat.id, photo=output, caption=f"Фото с рамкой №{frame_counter}")
            frame_counter += 1

    except Exception as e:
        bot.reply_to(message, f"Произошла ошибка при обработке фото: {str(e)}")

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
