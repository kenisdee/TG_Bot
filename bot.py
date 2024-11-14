import io
import logging
from functools import wraps

import telebot
from PIL import Image, UnidentifiedImageError, ImageOps
from telebot import types

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# Функция для чтения токена из файла
def get_token():
    """
    Читает токен бота из файла.

    Returns:
        str: Токен бота.
    """
    logger.info("Чтение токена бота из файла")
    try:
        # Открываем файл с токеном
        with open('/путь/к/файлу/token.txt', 'r') as file:
            # Читаем и возвращаем токен, удаляя лишние пробелы
            return file.read().strip()
    except FileNotFoundError:
        logger.error("Файл с токеном не найден")
        raise


# Получаем токен
try:
    # Вызываем функцию для чтения токена
    TOKEN = get_token()
    # Создаем экземпляр бота с использованием токена
    bot = telebot.TeleBot(TOKEN)
except Exception as e:
    logger.error(f"Ошибка при получении токена: {e}")
    raise


# Удаляем вебхук, если он активен
def delete_webhook():
    """
    Удаляет вебхук, если он активен.
    """
    logger.info("Удаление webhook, если он активен")  # Логируем информацию о попытке удаления вебхука
    try:
        # Удаляем вебхук, если он установлен
        bot.remove_webhook()  # Пытаемся удалить вебхук, если он был установлен
    except Exception as e:
        logger.error(f"Ошибка при удалении вебхука: {e}")  # Логируем ошибку, если удаление вебхука не удалось


# Вызываем функцию для удаления вебхука
delete_webhook()

# Словарь для хранения состояний пользователей
user_states = {}

# Набор символов для создания ASCII-арта
DEFAULT_ASCII_CHARS = '@%#*+=-:. '


# Декоратор для логирования
def log_function(func):
    # Декоратор для логирования вызовов функций и обработки ошибок
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Логируем вызов функции
        logger.info(f"Вызов функции {func.__name__}")
        try:
            # Вызываем исходную функцию и возвращаем её результат
            return func(*args, **kwargs)
        except Exception as e:
            # Логируем ошибку, если она возникла
            logger.error(f"Ошибка в функции {func.__name__}: {e}")
            # Поднимаем исключение дальше
            raise

    # Возвращаем обёрнутую функцию
    return wrapper


# Функция для обработки ошибок
def handle_error(message, error_message):
    # Логируем ошибку с использованием переданного сообщения об ошибке
    logger.error(error_message)
    # Отправляем сообщение пользователю о том, что произошла ошибка при обработке изображения
    bot.send_message(message.chat.id, "Произошла ошибка при обработке изображения.")


# Функция для изменения размера изображения
@log_function
def resize_image(image, new_width=100):
    # Получаем текущие размеры изображения
    width, height = image.size
    # Вычисляем соотношение сторон
    ratio = height / width
    # Вычисляем новую высоту, сохраняя пропорции
    new_height = int(new_width * ratio)
    # Изменяем размер изображения и возвращаем его
    return image.resize((new_width, new_height))


# Функция для преобразования изображения в оттенки серого
@log_function
def grayify(image):
    # Преобразуем изображение в оттенки серого и возвращаем его
    return image.convert("L")


# Функция для преобразования изображения в ASCII-арт
@log_function
def image_to_ascii(image_stream, new_width=40, ascii_chars=DEFAULT_ASCII_CHARS):
    # Открываем изображение из потока и преобразуем его в оттенки серого
    image = Image.open(image_stream).convert('L')
    # Получаем размеры изображения
    width, height = image.size
    # Вычисляем соотношение сторон
    aspect_ratio = height / width
    # Вычисляем новую высоту, сохраняя соотношение сторон
    new_height = int(aspect_ratio * new_width * 0.55)
    # Изменяем размер изображения
    img_resized = image.resize((new_width, new_height))
    # Преобразуем пиксели изображения в ASCII-символы
    img_str = pixels_to_ascii(img_resized, ascii_chars)
    # Получаем ширину изображения после изменения размера
    img_width = img_resized.width
    # Вычисляем максимальное количество символов, которое можно отправить в одном сообщении
    max_characters = 4000 - (new_width + 1)
    # Вычисляем максимальное количество строк, которое можно отправить
    max_rows = max_characters // (new_width + 1)
    # Инициализируем строку для ASCII-арта
    ascii_art = ""
    # Формируем ASCII-арт, добавляя по одной строке за раз
    for i in range(0, min(max_rows * img_width, len(img_str)), img_width):
        ascii_art += img_str[i:i + img_width] + "\n"
    # Возвращаем готовый ASCII-арт
    return ascii_art


# Функция для преобразования пикселей в ASCII-символы
@log_function
def pixels_to_ascii(image, ascii_chars=DEFAULT_ASCII_CHARS):
    # Получаем данные о пикселях изображения
    pixels = image.getdata()
    # Инициализируем строку для хранения ASCII-символов
    characters = ""
    # Проходим по каждому пикселю
    for pixel in pixels:
        # Вычисляем индекс символа в наборе ASCII-символов
        index = int(pixel * len(ascii_chars) // 256)
        # Добавляем символ в строку
        characters += ascii_chars[index]
    # Возвращаем строку с ASCII-символами
    return characters


# Функция для пикселизации изображения
@log_function
def pixelate_image(image, pixel_size):
    # Уменьшаем изображение до размера, кратного pixel_size, используя метод ближайшего соседа
    image = image.resize(
        (image.size[0] // pixel_size, image.size[1] // pixel_size),
        resample=Image.Resampling.NEAREST
    )
    # Увеличиваем изображение обратно до исходного размера, используя метод ближайшего соседа
    image = image.resize(
        (image.size[0] * pixel_size, image.size[1] * pixel_size),
        resample=Image.Resampling.NEAREST
    )
    # Возвращаем пикселизованное изображение
    return image


# Функция для инверсии цветов изображения
@log_function
def invert_colors(image):
    # Инвертируем цвета изображения с помощью функции invert из модуля ImageOps
    return ImageOps.invert(image)


# Обработчик команд /start и /help
@bot.message_handler(commands=['start', 'help'])
@log_function
def send_welcome(message):
    # Отправляем приветственное сообщение пользователю
    bot.reply_to(message, "Пришлите мне изображение, и я предложу вам варианты!")


# Обработчик получения фотографий
@bot.message_handler(content_types=['photo'])
@log_function
def handle_photo(message):
    # Отправляем ответное сообщение с предложением выбрать действие
    bot.reply_to(message, "У меня есть ваша фотография! Пожалуйста, выберите, что бы вы хотели с ней сделать.",
                 reply_markup=get_options_keyboard())
    # Сохраняем ID фотографии и инициализируем поле для символов ASCII-арта
    user_states[message.chat.id] = {'photo': message.photo[-1].file_id, 'ascii_chars': None}


# Обработчик получения фотографий
@bot.message_handler(content_types=['photo'])
@log_function
def handle_photo(message):
    bot.reply_to(message, "У меня есть ваша фотография! Пожалуйста, выберите, что бы вы хотели с ней сделать.",
                 reply_markup=get_options_keyboard())
    user_states[message.chat.id] = {'photo': message.photo[-1].file_id, 'ascii_chars': None}


# Функция для создания клавиатуры с вариантами действий
@log_function
def get_options_keyboard():
    # Создаем объект клавиатуры
    keyboard = types.InlineKeyboardMarkup()
    # Создаем кнопку для пикселизации изображения
    pixelate_btn = types.InlineKeyboardButton("Пикселизация", callback_data="pixelate")
    # Создаем кнопку для преобразования изображения в ASCII-арт
    ascii_btn = types.InlineKeyboardButton("ASCII-арт", callback_data="ascii")
    # Создаем кнопку для инверсии цветов изображения
    invert_btn = types.InlineKeyboardButton("Инвертировать цвета", callback_data="invert")
    # Добавляем кнопки на клавиатуру
    keyboard.add(pixelate_btn, ascii_btn, invert_btn)
    # Возвращаем созданную клавиатуру
    return keyboard


# Обработчик запросов обратного вызова
@bot.callback_query_handler(func=lambda call: True)
@log_function
def callback_query(call):
    # Проверяем, какой вариант выбрал пользователь
    if call.data == "pixelate":
        # Отвечаем на запрос обратного вызова, чтобы показать индикатор загрузки
        bot.answer_callback_query(call.id, "Пикселизация вашего изображения...")
        # Обрабатываем изображение с помощью функции пикселизации
        process_image(call.message, pixelate_image, 20)
    elif call.data == "ascii":
        # Отвечаем на запрос обратного вызова, чтобы показать индикатор загрузки
        bot.answer_callback_query(call.id, "Преобразование вашего изображения в формат ASCII art...")
        # Запрашиваем у пользователя набор символов для ASCII-арта
        bot.send_message(call.message.chat.id, "Пожалуйста, введите набор символов для ASCII-арта.")
        # Устанавливаем состояние пользователя в ожидание ввода символов
        user_states[call.message.chat.id]['ascii_chars'] = 'waiting'
    elif call.data == "invert":
        # Отвечаем на запрос обратного вызова, чтобы показать индикатор загрузки
        bot.answer_callback_query(call.id, "Инверсия цветов вашего изображения...")
        # Обрабатываем изображение с помощью функции инверсии цветов
        process_image(call.message, invert_colors)


# Обработчик ввода символов для ASCII-арта
@bot.message_handler(func=lambda message: user_states.get(message.chat.id, {}).get('ascii_chars') == 'waiting')
@log_function
def get_ascii_chars(message):
    # Сохраняем введенные пользователем символы для ASCII-арта
    user_states[message.chat.id]['ascii_chars'] = message.text
    # Вызываем функцию для обработки ASCII-арта с использованием введенных символов
    process_ascii_art(message)


# Функция для обработки изображения и отправки результата
@log_function
def process_image(message, image_processing_func, *args):
    try:
        # Получаем ID фотографии из состояния пользователя
        photo_id = user_states[message.chat.id]['photo']
        # Получаем информацию о файле по его ID
        file_info = bot.get_file(photo_id)
        # Скачиваем файл изображения
        downloaded_file = bot.download_file(file_info.file_path)

        # Открываем изображение из потока байтов
        with io.BytesIO(downloaded_file) as image_stream:
            image = Image.open(image_stream)
            # Обрабатываем изображение с помощью переданной функции и аргументов
            processed_image = image_processing_func(image, *args)

            # Создаем поток байтов для сохранения обработанного изображения
            with io.BytesIO() as output_stream:
                # Сохраняем обработанное изображение в поток
                processed_image.save(output_stream, format="JPEG")
                # Перемещаем указатель потока в начало
                output_stream.seek(0)
                # Отправляем обработанное изображение пользователю
                bot.send_photo(message.chat.id, output_stream)
    except UnidentifiedImageError:
        # Обрабатываем ошибку, если изображение не удалось открыть
        handle_error(message, "Ошибка при открытии изображения")
    except Exception as e:
        # Обрабатываем любые другие ошибки, возникшие при обработке и отправке изображения
        handle_error(message, f"Ошибка при обработке и отправке изображения: {e}")


# Функция для обработки ASCII-арта и отправки результата
@log_function
def process_ascii_art(message):
    try:
        # Получаем ID фотографии из состояния пользователя
        photo_id = user_states[message.chat.id]['photo']
        # Получаем набор символов для ASCII-арта из состояния пользователя
        ascii_chars = user_states[message.chat.id]['ascii_chars']
        # Получаем информацию о файле по его ID
        file_info = bot.get_file(photo_id)
        # Скачиваем файл изображения
        downloaded_file = bot.download_file(file_info.file_path)

        # Открываем скачанный файл как поток байтов
        with io.BytesIO(downloaded_file) as image_stream:
            # Преобразуем изображение в ASCII-арт с использованием указанных символов
            ascii_art = image_to_ascii(image_stream, ascii_chars=ascii_chars)
            # Отправляем ASCII-арт пользователю в виде форматированного сообщения
            bot.send_message(message.chat.id, f"```\n{ascii_art}\n```", parse_mode="MarkdownV2")
    except UnidentifiedImageError:
        # Обрабатываем ошибку, если изображение не удалось открыть
        handle_error(message, "Ошибка при открытии изображения")
    except Exception as e:
        # Обрабатываем любые другие ошибки, возникшие при обработке и отправке ASCII-арта
        handle_error(message, f"Ошибка при преобразовании изображения в ASCII-арт и отправке: {e}")


# Запускаем бота
try:
    # Запускаем бота в режиме опроса сервера Telegram на наличие новых сообщений
    bot.polling(none_stop=True)
except Exception as e:
    # В случае ошибки при запуске бота, логируем ошибку
    logger.error(f"Ошибка при запуске бота: {e}")
