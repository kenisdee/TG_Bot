import io
import logging
import random
import threading
import time
from datetime import datetime
from functools import wraps

import telebot
from PIL import Image, UnidentifiedImageError, ImageOps
from telebot import types

from lists import JOKES, COMPLIMENTS

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
    # Логируем информацию о попытке чтения токена
    logger.info("Чтение токена бота из файла")
    try:
        # Открываем файл с токеном
        with open('/путь/к/файлу/token.txt', 'r') as file:
            # Читаем и возвращаем токен, удаляя лишние пробелы
            return file.read().strip()
    except FileNotFoundError:
        # Логируем ошибку, если файл не найден
        logger.error("Файл с токеном не найден")
        raise


# Получаем токен
try:
    # Вызываем функцию для чтения токена
    TOKEN = get_token()
    # Создаем экземпляр бота с использованием токена
    bot = telebot.TeleBot(TOKEN)
except Exception as e:
    # Логируем ошибку, если чтение токена не удалось
    logger.error(f"Ошибка при получении токена: {e}")
    raise


# Удаляем вебхук, если он активен
def delete_webhook():
    """
    Удаляет вебхук, если он активен.
    """
    # Логируем информацию о попытке удаления вебхука
    logger.info("Удаление webhook, если он активен")
    try:
        # Удаляем вебхук, если он установлен
        bot.remove_webhook()  # Пытаемся удалить вебхук, если он был установлен
    except Exception as e:
        # Логируем ошибку, если удаление вебхука не удалось
        logger.error(f"Ошибка при удалении вебхука: {e}")


delete_webhook()

# Словарь для хранения состояний пользователей
user_states = {}

# Набор символов для создания ASCII-арта
DEFAULT_ASCII_CHARS = '@%#*+=-:. '

# Словарь для сопоставления названий функций с действиями пользователя
function_to_action = {
    'pixelate_image': 'пикселизирует изображение',
    'image_to_ascii': 'преобразует изображение в ASCII-арт',
    'invert_colors': 'инвертирует цвета изображения',
    'mirror_image': 'отражает изображение',
    'send_welcome': 'отправляет приветственное сообщение',
    'handle_photo': 'отправляет фотографию',
    'get_options_keyboard': 'получает клавиатуру с вариантами действий',
    'callback_query': 'обрабатывает запрос обратного вызова',
    'get_ascii_chars': 'вводит символы для ASCII-арта',
    'process_image': 'обрабатывает изображение',
    'process_ascii_art': 'обрабатывает ASCII-арт',
    'convert_to_heatmap': 'преобразует изображение в тепловую карту',
    'resize_for_sticker': 'изменяет размер изображения для стикера',
    'send_random_joke': 'получает случайную шутку',
    'send_random_compliment': 'получает случайный комплимент',
    'show_commands': 'получает список команд',
    'get_commands_keyboard': 'получает клавиатуру с командами',
    'flip_coin': 'подбрасывает монетку',
    'handle_resize_sticker': 'изменяет размер изображения для стикера',
    'handle_heatmap': 'преобразует изображение в тепловую карту',
    'handle_mirror_vertical': 'отражает изображение по вертикали',
    'handle_mirror_horizontal': 'отражает изображение по горизонтали',
    'handle_ascii': 'обрабатывает ASCII-арт',
    'handle_pixelate': 'пикселизирует изображение',
    'grayify': 'преобразует изображение в оттенки серого',
    'pixels_to_ascii': 'преобразует пиксели изображения в ASCII-символы'
}


# Декоратор для логирования вызовов функций и обработки ошибок
def log_function(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Извлекаем user_id из kwargs или args
        user_id = kwargs.get('user_id')
        if not user_id:
            for arg in args:
                if isinstance(arg, types.Message):
                    user_id = arg.chat.id
                    break
                elif isinstance(arg, types.CallbackQuery):
                    user_id = arg.message.chat.id
                    break

        # Если user_id все еще None, устанавливаем его в "Unknown"
        if not user_id:
            user_id = "Unknown"

        action = function_to_action.get(func.__name__, f"выполняет неизвестное действие ({func.__name__})")
        start_time = time.time()  # Засекаем время начала обработки
        start_time_str = datetime.fromtimestamp(start_time).strftime(
            '%d-%m-%Y %H:%M:%S')  # Преобразуем в формат день-месяц-год
        logger.info(
            f"Начало операции: Пользователь с ID {user_id} {action} в {start_time_str}")  # Логируем начало операции

        try:
            result = func(*args, **kwargs)
            end_time = time.time()  # Засекаем время окончания обработки
            end_time_str = datetime.fromtimestamp(end_time).strftime(
                '%d-%m-%Y %H:%M:%S')  # Преобразуем в формат день-месяц-год
            # Логируем конец операции и время выполнения
            logger.info(
                f"Конец операции: Пользователь с ID {user_id} {action} в {end_time_str}, время выполнения: {end_time - start_time} сек")
            # Возвращаем результат выполнения функции
            return result
        except Exception as e:
            # Логируем ошибку, если она произошла
            logger.error(f"Ошибка в функции {func.__name__} пользователя с ID {user_id}: {e}")
            raise

    # Возвращаем обертку для функции
    return wrapper


# Функция для обработки ошибок
def handle_error(message, error_message):
    # Логируем ошибку с использованием переданного сообщения об ошибке
    logger.error(f"Ошибка для пользователя с ID {message.chat.id}: {error_message}")
    # Отправляем сообщение пользователю о том, что произошла ошибка при обработке изображения
    bot.send_message(message.chat.id, "Произошла ошибка при обработке изображения.")


# Функция для изменения размера изображения
@log_function
def resize_image(image, new_width=100, user_id=None):
    """
    Изменяет размер изображения, сохраняя пропорции.

    Args:
        image (PIL.Image): Исходное изображение.
        new_width (int): Новая ширина изображения.
        user_id (int): ID пользователя.

    Returns:
        PIL.Image: Изображение с измененным размером.
    """
    # Получаем текущие размеры изображения
    width, height = image.size
    # Вычисляем соотношение сторон
    ratio = height / width
    # Вычисляем новую высоту, сохраняя пропорции
    new_height = int(new_width * ratio)
    # Изменяем размер изображения и возвращаем его с новыми размерами
    return image.resize((new_width, new_height))


# Функция для преобразования изображения в оттенки серого
@log_function
def grayify(image, user_id=None):
    """
    Преобразует изображение в оттенки серого.

    Args:
        image (PIL.Image): Исходное изображение.
        user_id (int): ID пользователя.

    Returns:
        PIL.Image: Изображение в оттенках серого.
    """
    # Преобразуем изображение в оттенки серого и возвращаем его в оттенках серого
    return image.convert("L")


# Функция для преобразования изображения в ASCII-арт
@log_function
def image_to_ascii(image_stream, new_width=40, ascii_chars=DEFAULT_ASCII_CHARS, user_id=None):
    """
    Преобразует изображение в ASCII-арт.

    Args:
        image_stream (io.BytesIO): Поток байтов с изображением.
        new_width (int): Новая ширина изображения.
        ascii_chars (str): Набор символов для ASCII-арта.
        user_id (int): ID пользователя.

    Returns:
        str: ASCII-арт изображения.
    """

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
    img_str = pixels_to_ascii(img_resized, ascii_chars, user_id=user_id)
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
    # Возвращаем сформированный ASCII-арт
    return ascii_art


# Функция для преобразования пикселей в ASCII-символы
@log_function
def pixels_to_ascii(image, ascii_chars=DEFAULT_ASCII_CHARS, user_id=None):
    """
    Преобразует пиксели изображения в ASCII-символы.

    Args:
        image (PIL.Image): Изображение в оттенках серого.
        ascii_chars (str): Набор символов для ASCII-арта.
        user_id (int): ID пользователя.

    Returns:
        str: Строка с ASCII-символами.
    """
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
def pixelate_image(image, pixel_size, user_id=None):
    """
    Пикселизирует изображение.

    Args:
        image (PIL.Image): Исходное изображение.
        pixel_size (int): Размер пикселя.
        user_id (int): ID пользователя.

    Returns:
        PIL.Image: Пикселизованное изображение.
    """
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
def invert_colors(image, user_id=None):
    """
    Инвертирует цвета изображения.

    Args:
        image (PIL.Image): Исходное изображение.
        user_id (int): ID пользователя.

    Returns:
        PIL.Image: Изображение с инвертированными цветами.
    """
    # Инвертируем цвета изображения с помощью функции invert из модуля ImageOps
    return ImageOps.invert(image)


# Функция для отражения изображения
@log_function
def mirror_image(image, direction, user_id=None):
    """
    Отражает изображение по горизонтали или вертикали.

    Args:
        image (PIL.Image): Исходное изображение.
        direction (str): Направление отражения ('horizontal' или 'vertical').
        user_id (int): ID пользователя.

    Returns:
        PIL.Image: Отраженное изображение.
    """
    if direction == 'horizontal':
        # Возвращаем изображение, отраженное по горизонтали
        return ImageOps.mirror(image)
    elif direction == 'vertical':
        # Возвращаем изображение, отраженное по вертикали
        return ImageOps.flip(image)
    else:
        # Выбрасываем исключение, если направление неверное
        raise ValueError("Неверное направление отражения. Используйте 'horizontal' или 'vertical'.")


# Функция для преобразования изображения в тепловую карту
@log_function
def convert_to_heatmap(image, user_id=None):
    """
    Преобразует изображение в тепловую карту.

    Args:
        image (PIL.Image): Исходное изображение.
        user_id (int): ID пользователя.

    Returns:
        PIL.Image: Изображение в виде тепловой карты.
    """
    # Преобразуем изображение в оттенки серого
    gray_image = grayify(image, user_id=user_id)
    # Применяем цветовую палитру для создания тепловой карты
    heatmap_image = ImageOps.colorize(gray_image, black="blue", white="red")
    # Возвращаем изображение в виде тепловой карты
    return heatmap_image


# Функция для изменения размера изображения для стикера
@log_function
def resize_for_sticker(image, max_size=256, user_id=None):
    """
    Изменяет размер изображения, сохраняя пропорции, чтобы его максимальное измерение не превышало заданного максимума.

    Args:
        image (PIL.Image): Исходное изображение.
        max_size (int): Максимальный размер изображения (по умолчанию 256 пикселей).
        user_id (int): ID пользователя.

    Returns:
        PIL.Image: Изображение с измененным размером.
    """
    # Получаем текущие размеры изображения
    width, height = image.size
    # Вычисляем соотношение сторон
    ratio = min(max_size / width, max_size / height)
    # Вычисляем новые размеры, сохраняя пропорции
    new_width = int(width * ratio)
    new_height = int(height * ratio)
    # Изменяем размер изображения и возвращаем его
    return image.resize((new_width, new_height),
                        resample=Image.Resampling.BICUBIC)


# Обработчик команд /start и /help
@bot.message_handler(commands=['start', 'help'])
@log_function
def send_welcome(message, user_id=None):
    """
    Обрабатывает команды /start и /help.

    Args:
        message (telebot.types.Message): Сообщение от пользователя.
        user_id (int): ID пользователя.
    """
    if message.text == '/start':
        # Отправляем приветственное сообщение пользователю
        bot.reply_to(message, "Пришлите мне изображение, и я предложу вам варианты!",
                     reply_markup=get_commands_keyboard(user_id=message.chat.id))
    elif message.text == '/help':
        # Отправляем текст справки пользователю
        help_text = get_help_text()
        bot.reply_to(message, help_text)


# Обработчик команды /random_joke
@bot.message_handler(commands=['random_joke'])
@bot.message_handler(func=lambda message: message.text == "Случайная шутка")
@log_function
def send_random_joke(message, user_id=None):
    """
    Отправляет пользователю случайную шутку из списка JOKES.

    Args:
        message (telebot.types.Message): Сообщение от пользователя.
        user_id (int): ID пользователя.
    """
    # Выбираем случайную шутку из списка
    joke = random.choice(JOKES)
    # Отправляем шутку пользователю
    bot.reply_to(message, joke)


# Обработчик команды /random_compliment
@bot.message_handler(commands=['random_compliment'])
@bot.message_handler(func=lambda message: message.text == "Случайный комплимент")
@log_function
def send_random_compliment(message, user_id=None):
    """
    Отправляет пользователю случайный комплимент из списка COMPLIMENTS.

    Args:
        message (telebot.types.Message): Сообщение от пользователя.
        user_id (int): ID пользователя.
    """
    # Выбираем случайный комплимент из списка
    compliment = random.choice(COMPLIMENTS)
    # Отправляем комплимент пользователю
    bot.reply_to(message, compliment)


# Обработчик команды /flip_coin
@bot.message_handler(commands=['flip_coin'])
@bot.message_handler(func=lambda message: message.text == "Подбросить монетку")
@log_function
def flip_coin(message, user_id=None):
    """
    Симулирует подбрасывание монетки и сообщает пользователю результат ("Орел" или "Решка").

    Args:
        message (telebot.types.Message): Сообщение от пользователя.
        user_id (int): ID пользователя.
    """
    # Случайный выбор между "Heads" и "Tails"
    result = random.choice(["Орел", "Решка"])

    # Отправляем результат пользователю
    bot.reply_to(message, f"Результат подбрасывания монетки: {result}")


# Обработчик команды /pixelate
@bot.message_handler(commands=['pixelate'])
@log_function
def handle_pixelate(message, user_id=None):
    """
    Обрабатывает команду /pixelate для пикселизации изображения.

    Args:
        message (telebot.types.Message): Сообщение от пользователя.
        user_id (int): ID пользователя.
    """
    # Отправляем сообщение о начале обработки
    bot.reply_to(message, "Пикселизация вашего изображения...")
    # Обрабатываем изображение с помощью функции пикселизации
    process_image(message, pixelate_image, 20, user_id=message.chat.id)


# Обработчик команды /ascii
@bot.message_handler(commands=['ascii'])
@log_function
def handle_ascii(message, user_id=None):
    """
    Обрабатывает команду /ascii для преобразования изображения в ASCII-арт.

    Args:
        message (telebot.types.Message): Сообщение от пользователя.
        user_id (int): ID пользователя.
    """
    # Отправляем сообщение о начале обработки
    bot.reply_to(message, "Преобразование вашего изображения в формат ASCII art...")
    # Запрашиваем у пользователя набор символов для ASCII-арта
    bot.send_message(message.chat.id, "Пожалуйста, введите набор символов для ASCII-арта.")
    # Устанавливаем состояние пользователя в ожидание ввода символов
    user_states[message.chat.id] = {'ascii_chars': 'waiting'}


# Обработчик команды /invert
@bot.message_handler(commands=['invert'])
@log_function
def handle_invert(message, user_id=None):
    """
    Обрабатывает команду /invert для инверсии цветов изображения.

    Args:
        message (telebot.types.Message): Сообщение от пользователя.
        user_id (int): ID пользователя.
    """
    # Отправляем сообщение о начале обработки
    bot.reply_to(message, "Инверсия цветов вашего изображения...")
    # Обрабатываем изображение с помощью функции инверсии цветов
    process_image(message, invert_colors, user_id=message.chat.id)


# Обработчик команды /mirror_horizontal
@bot.message_handler(commands=['mirror_horizontal'])
@log_function
def handle_mirror_horizontal(message, user_id=None):
    """
    Обрабатывает команду /mirror_horizontal для отражения изображения по горизонтали.

    Args:
        message (telebot.types.Message): Сообщение от пользователя.
        user_id (int): ID пользователя.
    """
    # Отправляем сообщение о начале обработки
    bot.reply_to(message, "Отражение вашего изображения по горизонтали...")
    # Обрабатываем изображение с помощью функции отражения по горизонтали
    process_image(message, mirror_image, 'horizontal', user_id=message.chat.id)


# Обработчик команды /mirror_vertical
@bot.message_handler(commands=['mirror_vertical'])
@log_function
def handle_mirror_vertical(message, user_id=None):
    """
    Обрабатывает команду /mirror_vertical для отражения изображения по вертикали.

    Args:
        message (telebot.types.Message): Сообщение от пользователя.
        user_id (int): ID пользователя.
    """
    # Отправляем сообщение о начале обработки
    bot.reply_to(message, "Отражение вашего изображения по вертикали...")
    # Обрабатываем изображение с помощью функции отражения по вертикали
    process_image(message, mirror_image, 'vertical', user_id=message.chat.id)


# Обработчик команды /heatmap
@bot.message_handler(commands=['heatmap'])
@log_function
def handle_heatmap(message, user_id=None):
    """
    Обрабатывает команду /heatmap для преобразования изображения в тепловую карту.

    Args:
        message (telebot.types.Message): Сообщение от пользователя.
        user_id (int): ID пользователя.
    """
    # Отправляем сообщение о начале обработки
    bot.reply_to(message, "Преобразование вашего изображения в тепловую карту...")
    # Обрабатываем изображение с помощью функции преобразования в тепловую карту
    process_image(message, convert_to_heatmap, user_id=message.chat.id)


# Обработчик команды /resize_sticker
@bot.message_handler(commands=['resize_sticker'])
@log_function
def handle_resize_sticker(message, user_id=None):
    """
    Обрабатывает команду /resize_sticker для изменения размера изображения для стикера.

    Args:
        message (telebot.types.Message): Сообщение от пользователя.
        user_id (int): ID пользователя.
    """
    # Отправляем сообщение о начале обработки
    bot.reply_to(message, "Изменение размера изображения для стикера...")
    # Обрабатываем изображение с помощью функции изменения размера для стикера
    process_image(message, resize_for_sticker, user_id=message.chat.id)


# Обработчик получения фотографий
@bot.message_handler(content_types=['photo'])
@log_function
def handle_photo(message, user_id=None):
    """
    Обрабатывает полученные фотографии и предлагает пользователю варианты действий.

    Args:
        message (telebot.types.Message): Сообщение от пользователя.
        user_id (int): ID пользователя.
    """
    # Отправляем ответное сообщение с предложением выбрать действие
    bot.reply_to(message, "У меня есть ваша фотография! Пожалуйста, выберите, что бы вы хотели с ней сделать.",
                 reply_markup=get_options_keyboard(user_id=message.chat.id))
    # Сохраняем ID фотографии и инициализируем поле для символов ASCII-арта
    user_states[message.chat.id] = {'photo': message.photo[-1].file_id, 'ascii_chars': None}


# Функция для создания клавиатуры с вариантами действий
@log_function
def get_options_keyboard(user_id=None):
    """
    Создает клавиатуру с вариантами действий над изображением.

    Args:
        user_id (int): ID пользователя.

    Returns:
        telebot.types.InlineKeyboardMarkup: Клавиатура с вариантами действий.
    """
    # Создаем объект клавиатуры
    keyboard = types.InlineKeyboardMarkup()
    # Создаем кнопку для пикселизации изображения
    pixelate_btn = types.InlineKeyboardButton("Пикселизация", callback_data="pixelate")
    # Создаем кнопку для преобразования изображения в ASCII-арт
    ascii_btn = types.InlineKeyboardButton("ASCII-арт", callback_data="ascii")
    # Создаем кнопку для инверсии цветов изображения
    invert_btn = types.InlineKeyboardButton("Инвертировать цвета", callback_data="invert")
    # Создаем кнопку для отражения изображения по горизонтали
    mirror_horizontal_btn = types.InlineKeyboardButton("Отразить по горизонтали", callback_data="mirror_horizontal")
    # Создаем кнопку для отражения изображения по вертикали
    mirror_vertical_btn = types.InlineKeyboardButton("Отразить по вертикали", callback_data="mirror_vertical")
    # Создаем кнопку для преобразования изображения в тепловую карту
    heatmap_btn = types.InlineKeyboardButton("Тепловая карта", callback_data="heatmap")
    # Создаем кнопку для изменения размера изображения для стикера
    resize_sticker_btn = types.InlineKeyboardButton("Изменить размер для стикера", callback_data="resize_sticker")
    # Добавляем кнопки на клавиатуру
    keyboard.add(pixelate_btn, ascii_btn, invert_btn, mirror_horizontal_btn, mirror_vertical_btn, heatmap_btn,
                 resize_sticker_btn)
    # Возвращаем созданную клавиатуру
    return keyboard


# Функция для создания клавиатуры с командами
@log_function
def get_commands_keyboard(user_id=None):
    """
    Создает клавиатуру с командами бота.

    Args:
        user_id (int): ID пользователя.

    Returns:
        telebot.types.ReplyKeyboardMarkup: Клавиатура с командами.
    """
    # Создаем объект клавиатуры
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    # Создаем кнопку для отправки случайной шутки
    random_joke_btn = types.KeyboardButton("Случайная шутка")
    # Создаем кнопку для отправки случайного комплимента
    random_compliment_btn = types.KeyboardButton("Случайный комплимент")
    # Создаем кнопку для подбрасывания монетки
    flip_coin_btn = types.KeyboardButton("Подбросить монетку")
    # Создаем кнопку для вывода списка команд
    commands_btn = types.KeyboardButton("Список команд")
    # Добавляем кнопки на клавиатуру
    keyboard.add(random_joke_btn, random_compliment_btn, flip_coin_btn, commands_btn)
    # Возвращаем созданную клавиатуру
    return keyboard


# Обработчик запросов обратного вызова
@bot.callback_query_handler(func=lambda call: True)
@log_function
def callback_query(call, user_id=None):
    """
    Обрабатывает запросы обратного вызова от пользователя.

    Args:
        call (telebot.types.CallbackQuery): Запрос обратного вызова.
        user_id (int): ID пользователя.
    """
    user_id = call.message.chat.id
    # Проверяем, какой вариант выбрал пользователь
    if call.data == "pixelate":
        # Отвечаем на запрос обратного вызова, чтобы показать индикатор загрузки
        bot.answer_callback_query(call.id, "Пикселизация вашего изображения...")
        # Обрабатываем изображение с помощью функции пикселизации
        process_image(call.message, pixelate_image, 20, user_id=user_id)
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
        process_image(call.message, invert_colors, user_id=user_id)
    elif call.data == "mirror_horizontal":
        # Отвечаем на запрос обратного вызова, чтобы показать индикатор загрузки
        bot.answer_callback_query(call.id, "Отражение вашего изображения по горизонтали...")
        # Обрабатываем изображение с помощью функции отражения по горизонтали
        process_image(call.message, mirror_image, 'horizontal', user_id=user_id)
    elif call.data == "mirror_vertical":
        # Отвечаем на запрос обратного вызова, чтобы показать индикатор загрузки
        bot.answer_callback_query(call.id, "Отражение вашего изображения по вертикали...")
        # Обрабатываем изображение с помощью функции отражения по вертикали
        process_image(call.message, mirror_image, 'vertical', user_id=user_id)
    elif call.data == "heatmap":
        # Отвечаем на запрос обратного вызова, чтобы показать индикатор загрузки
        bot.answer_callback_query(call.id, "Преобразование вашего изображения в тепловую карту...")
        # Обрабатываем изображение с помощью функции преобразования в тепловую карту
        process_image(call.message, convert_to_heatmap, user_id=user_id)
    elif call.data == "resize_sticker":
        # Отвечаем на запрос обратного вызова, чтобы показать индикатор загрузки
        bot.answer_callback_query(call.id, "Изменение размера изображения для стикера...")
        # Обрабатываем изображение с помощью функции изменения размера для стикера
        process_image(call.message, resize_for_sticker, user_id=user_id)


# Обработчик ввода символов для ASCII-арта
@bot.message_handler(func=lambda message: user_states.get(message.chat.id, {}).get('ascii_chars') == 'waiting')
@log_function
def get_ascii_chars(message, user_id=None):
    """
    Обрабатывает ввод пользователем символов для ASCII-арта.

    Args:
        message (telebot.types.Message): Сообщение от пользователя.
        user_id (int): ID пользователя.
    """
    # Сохраняем введенные пользователем символы для ASCII-арта
    user_states[message.chat.id]['ascii_chars'] = message.text
    # Вызываем функцию для обработки ASCII-арта с использованием введенных символов
    process_ascii_art(message, user_id=message.chat.id)


# Функция для обработки изображения и отправки результата
@log_function
def process_image(message, image_processing_func, *args, user_id=None):
    """
    Обрабатывает изображение с помощью переданной функции и отправляет результат пользователю.

    Args:
        message (telebot.types.Message): Сообщение от пользователя.
        image_processing_func (function): Функция для обработки изображения.
        *args: Дополнительные аргументы для функции обработки изображения.
        user_id (int): ID пользователя.
    """
    try:
        # Получаем ID фотографии из состояния пользователя
        photo_id = user_states[message.chat.id]['photo']
        # Получаем информацию о файле по его ID
        file_info = bot.get_file(photo_id)
        # Скачиваем файл изображения
        downloaded_file = bot.download_file(file_info.file_path)

        # Открываем скачанный файл как поток байтов
        with io.BytesIO(downloaded_file) as image_stream:
            # Открываем изображение с помощью библиотеки PIL
            image = Image.open(image_stream)
            # Получаем размер изображения
            width, height = image.size
            # Логируем информацию о размере изображения и пользователе
            logger.info(f"Пользователь с ID {user_id} обрабатывает изображение размером {width}x{height} пикселей")

            # Обрабатываем изображение с помощью переданной функции и аргументов
            processed_image = image_processing_func(image, *args, user_id=user_id)

            # Создаем новый поток байтов для сохранения обработанного изображения
            with io.BytesIO() as output_stream:
                # Сохраняем обработанное изображение в формате JPEG
                processed_image.save(output_stream, format="JPEG")
                # Перемещаем указатель потока в начало
                output_stream.seek(0)
                # Отправляем обработанное изображение пользователю
                bot.send_photo(message.chat.id, output_stream)
    except UnidentifiedImageError:
        # Обрабатываем ошибку, если изображение не удалось открыть
        handle_error(message, "Ошибка при открытии изображения")
    except Exception as e:
        # Обрабатываем любые другие ошибки и логируем их
        handle_error(message, f"Ошибка при обработке и отправке изображения: {e}")


# Функция для обработки ASCII-арта и отправки результата
@log_function
def process_ascii_art(message, user_id=None):
    """
    Обрабатывает изображение и преобразует его в ASCII-арт, затем отправляет результат пользователю.

    Args:
        message (telebot.types.Message): Сообщение от пользователя.
        user_id (int): ID пользователя.
    """
    try:
        # Получаем ID фотографии из состояния пользователя
        photo_id = user_states[message.chat.id]['photo']
        # Получаем символы для ASCII-арта из состояния пользователя
        ascii_chars = user_states[message.chat.id]['ascii_chars']
        # Получаем информацию о файле по его ID
        file_info = bot.get_file(photo_id)
        # Скачиваем файл изображения
        downloaded_file = bot.download_file(file_info.file_path)

        # Открываем скачанный файл как поток байтов
        with io.BytesIO(downloaded_file) as image_stream:
            # Открываем изображение с помощью библиотеки PIL
            image = Image.open(image_stream)
            # Получаем размер изображения
            width, height = image.size
            # Логируем информацию о размере изображения и пользователе
            logger.info(
                f"Пользователь с ID {user_id} преобразует изображение размером {width}x{height} пикселей в ASCII-арт с символами: {ascii_chars}")

            # Преобразуем изображение в ASCII-арт
            ascii_art = image_to_ascii(image_stream, ascii_chars=ascii_chars, user_id=user_id)
            # Отправляем ASCII-арт пользователю
            bot.send_message(message.chat.id, f"```\n{ascii_art}\n```", parse_mode="MarkdownV2")
    except UnidentifiedImageError:
        # Обрабатываем ошибку, если изображение не удалось открыть
        handle_error(message, "Ошибка при открытии изображения")
    except Exception as e:
        # Обрабатываем любые другие ошибки и логируем их
        handle_error(message, f"Ошибка при преобразовании изображения в ASCII-арт и отправке: {e}")


# Обработчик команды "Список команд"
@bot.message_handler(func=lambda message: message.text == "Список команд")
@log_function
def show_commands(message, user_id=None):
    """
    Отправляет пользователю список доступных команд бота.

    Args:
        message (telebot.types.Message): Сообщение от пользователя.
        user_id (int): ID пользователя.
    """
    # Формируем сообщение со списком команд и их описаниями
    commands_message = (
        "/start - Начать работу с ботом\n"
        "/help - Получить помощь\n"
        "/pixelate - Пикселизация изображения\n"
        "/ascii - Преобразование изображения в ASCII-арт\n"
        "/invert - Инвертировать цвета изображения\n"
        "/mirror_horizontal - Отразить изображение по горизонтали\n"
        "/mirror_vertical - Отразить изображение по вертикали\n"
        "/heatmap - Преобразование изображения в тепловую карту\n"
        "/resize_sticker - Изменить размер изображения для стикера\n"
        "/random_joke - Случайная шутка\n"
        "/random_compliment - Случайный комплимент\n"
        "/flip_coin - Подбросить монетку и получить результат (\"Орел\" или \"Решка\")\n"
    )
    # Отправляем сообщение с командами пользователю
    bot.send_message(message.chat.id, commands_message)


# Функция для чтения текста справки из файла help.txt
def get_help_text():
    """
    Читает текст справки из файла help.txt.

    Returns:
        str: Текст справки.
    """
    try:
        with open('help.txt', 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        return "Файл справки не найден."


# Функция для проверки состояния чата
def check_chat_state():
    """
    Проверяет состояние чата каждую минуту и сбрасывает историю событий для несуществующих чатов.
    """
    while True:
        time.sleep(60)  # Проверяем состояние чата каждую минуту
        for chat_id in list(user_states.keys()):
            try:
                # Проверяем, существует ли чат
                bot.send_chat_action(chat_id, 'typing')
            except telebot.apihelper.ApiException:
                # Если чат не существует, сбрасываем историю событий
                del user_states[chat_id]
                logger.info(f"Сброс истории событий для чата с ID {chat_id}")


# Запускаем поток для проверки состояния чата
threading.Thread(target=check_chat_state, daemon=True).start()

# Запускаем бота
try:
    # Запускаем бота в режиме опроса сервера Telegram на наличие новых сообщений
    bot.polling(none_stop=True)
except Exception as e:
    # В случае ошибки при запуске бота, логируем ошибку
    logger.error(f"Ошибка при запуске бота: {e}")
