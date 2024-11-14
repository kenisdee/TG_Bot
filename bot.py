import io
import logging

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
    logger.info("Удаление webhook, если он активен")
    try:
        # Удаляем вебхук, если он установлен
        bot.remove_webhook()
    except Exception as e:
        logger.error(f"Ошибка при удалении вебхука: {e}")


# Вызываем функцию для удаления вебхука
delete_webhook()

# Словарь для хранения состояний пользователей
user_states = {}

# Набор символов для создания ASCII-арта
DEFAULT_ASCII_CHARS = '@%#*+=-:. '


def resize_image(image, new_width=100):
    """
    Изменяет размер изображения, сохраняя пропорции.

    Args:
        image (PIL.Image.Image): Исходное изображение.
        new_width (int): Новая ширина изображения.

    Returns:
        PIL.Image.Image: Измененное изображение.
    """
    logger.info(f"Изменение размера изображения по ширине: {new_width}")
    try:
        # Получаем текущие размеры изображения
        width, height = image.size
        # Вычисляем отношение высоты к ширине
        ratio = height / width
        # Вычисляем новую высоту, сохраняя пропорции
        new_height = int(new_width * ratio)
        # Изменяем размер изображения
        return image.resize((new_width, new_height))
    except Exception as e:
        logger.error(f"Ошибка при изменении размера изображения: {e}")
        return image


def grayify(image):
    """
    Преобразует изображение в оттенки серого.

    Args:
        image (PIL.Image.Image): Исходное изображение.

    Returns:
        PIL.Image.Image: Изображение в оттенках серого.
    """
    logger.info("Преобразование изображения в оттенки серого")
    try:
        # Преобразуем изображение в оттенки серого
        return image.convert("L")
    except Exception as e:
        logger.error(f"Ошибка при преобразовании изображения в оттенки серого: {e}")
        return image


def image_to_ascii(image_stream, new_width=40, ascii_chars=DEFAULT_ASCII_CHARS):
    """
    Преобразует изображение в ASCII-арт.

    Args:
        image_stream (io.BytesIO): Поток данных изображения.
        new_width (int): Новая ширина изображения для ASCII-арта.
        ascii_chars (str): Набор символов для ASCII-арта.

    Returns:
        str: ASCII-арт изображения.
    """
    logger.info(f"Преобразование изображения в формат ASCII с указанием ширины: {new_width} and chars: {ascii_chars}")
    try:
        # Переводим в оттенки серого
        image = Image.open(image_stream).convert('L')

        # меняем размер сохраняя отношение сторон
        width, height = image.size
        aspect_ratio = height / width
        new_height = int(aspect_ratio * new_width * 0.55)  # 0,55 так как буквы выше чем шире
        img_resized = image.resize((new_width, new_height))

        # Преобразуем пиксели в ASCII-символы
        img_str = pixels_to_ascii(img_resized, ascii_chars)
        img_width = img_resized.width

        # Ограничиваем количество символов для сообщения в Telegram
        max_characters = 4000 - (new_width + 1)
        max_rows = max_characters // (new_width + 1)

        ascii_art = ""
        for i in range(0, min(max_rows * img_width, len(img_str)), img_width):
            ascii_art += img_str[i:i + img_width] + "\n"

        return ascii_art
    except Exception as e:
        logger.error(f"Ошибка при преобразовании изображения в ASCII-арт: {e}")
        return "Произошла ошибка при обработке изображения."


def pixels_to_ascii(image, ascii_chars=DEFAULT_ASCII_CHARS):
    """
    Преобразует пиксельные данные изображения в ASCII-символы.

    Args:
        image (PIL.Image.Image): Изображение в оттенках серого.
        ascii_chars (str): Набор символов для ASCII-арта.

    Returns:
        str: Строка ASCII-символов, представляющая изображение.
    """
    logger.info(f"Преобразование пикселей в символы ASCII с использованием символов chars: {ascii_chars}")
    try:
        # Получаем данные пикселей
        pixels = image.getdata()
        characters = ""
        for pixel in pixels:
            # Убеждаемся, что индекс является целым числом
            index = int(pixel * len(ascii_chars) // 256)
            characters += ascii_chars[index]
        return characters
    except Exception as e:
        logger.error(f"Ошибка при преобразовании пикселей в символы ASCII: {e}")
        return ""


def pixelate_image(image, pixel_size):
    """
    Пикселизирует изображение.

    Args:
        image (PIL.Image.Image): Исходное изображение.
        pixel_size (int): Размер пикселя для пикселизации.

    Returns:
        PIL.Image.Image: Пикселизированное изображение.
    """
    logger.info(f"Растровое изображение с размером в пиксель: {pixel_size}")
    try:
        # Уменьшаем изображение до размера, кратного pixel_size
        image = image.resize(
            (image.size[0] // pixel_size, image.size[1] // pixel_size),
            resample=Image.Resampling.NEAREST
        )
        # Увеличиваем изображение обратно до исходного размера, используя метод ближайшего соседа
        image = image.resize(
            (image.size[0] * pixel_size, image.size[1] * pixel_size),
            resample=Image.Resampling.NEAREST
        )
        return image
    except Exception as e:
        logger.error(f"Ошибка при пикселизации изображения: {e}")
        return image


def invert_colors(image):
    """
    Инвертирует цвета изображения.

    Args:
        image (PIL.Image.Image): Исходное изображение.

    Returns:
        PIL.Image.Image: Изображение с инвертированными цветами.
    """
    logger.info("Инвертирование цветов изображения")
    try:
        # Инвертируем цвета изображения
        return ImageOps.invert(image)
    except Exception as e:
        logger.error(f"Ошибка при инвертировании цветов изображения: {e}")
        return image


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    """
    Обрабатывает команды /start и /help, отправляя приветственное сообщение.

    Args:
        message (telebot.types.Message): Сообщение от пользователя.
    """
    logger.info(f"Обработка команды /start или /help от пользователя: {message.chat.id}")
    try:
        # Отправляем приветственное сообщение
        bot.reply_to(message, "Пришлите мне изображение, и я предложу вам варианты!")
    except Exception as e:
        logger.error(f"Ошибка при отправке приветственного сообщения: {e}")


@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    """
    Обрабатывает полученные фотографии, предлагая пользователю варианты действий.

    Args:
        message (telebot.types.Message): Сообщение от пользователя с фотографией.
    """
    logger.info(f"Обработка фотографий от пользователя: {message.chat.id}")
    try:
        # Отправляем сообщение с предложением выбора действия
        bot.reply_to(message, "У меня есть ваша фотография! Пожалуйста, выберите, что бы вы хотели с ней сделать.",
                     reply_markup=get_options_keyboard())
        # Сохраняем ID фотографии в состояние пользователя
        user_states[message.chat.id] = {'photo': message.photo[-1].file_id, 'ascii_chars': None}
    except Exception as e:
        logger.error(f"Ошибка при обработке фотографии: {e}")


def get_options_keyboard():
    """
    Создает и возвращает клавиатуру с вариантами действий.

    Returns:
        telebot.types.InlineKeyboardMarkup: Клавиатура с вариантами действий.
    """
    logger.info("Создание параметров клавиатуры")
    try:
        # Создаем инлайн-клавиатуру
        keyboard = types.InlineKeyboardMarkup()

        # Добавляем кнопку для пикселизации изображения
        pixelate_btn = types.InlineKeyboardButton("Пикселизация", callback_data="pixelate")

        # Добавляем кнопку для преобразования изображения в ASCII-арт
        ascii_btn = types.InlineKeyboardButton("ASCII Art", callback_data="ascii")

        # Добавляем кнопку для инверсии цветов
        invert_btn = types.InlineKeyboardButton("Инвертировать цвета", callback_data="invert")

        # Добавляем кнопки в клавиатуру
        keyboard.add(pixelate_btn, ascii_btn, invert_btn)

        # Возвращаем созданную клавиатуру
        return keyboard
    except Exception as e:
        logger.error(f"Ошибка при создании клавиатуры: {e}")
        return types.InlineKeyboardMarkup()


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    """
    Обрабатывает выбор пользователя из инлайн-клавиатуры.

    Args:
        call (telebot.types.CallbackQuery): Объект, представляющий запрос обратного вызова.
    """
    logger.info(f"Обработка запроса обратного вызова от пользователя: {call.message.chat.id}, data: {call.data}")
    try:
        # Если пользователь выбрал пикселизацию изображения
        if call.data == "pixelate":
            bot.answer_callback_query(call.id, "Пикселизация вашего изображения...")
            process_image(call.message, pixelate_image, 20)
        # Если пользователь выбрал преобразование в ASCII-арт
        elif call.data == "ascii":
            bot.answer_callback_query(call.id, "Преобразование вашего изображения в формат ASCII art...")
            bot.send_message(call.message.chat.id, "Пожалуйста, введите набор символов для ASCII-арта.")
            user_states[call.message.chat.id]['ascii_chars'] = 'waiting'
        # Если пользователь выбрал инверсию цветов
        elif call.data == "invert":
            bot.answer_callback_query(call.id, "Инверсия цветов вашего изображения...")
            process_image(call.message, invert_colors)
    except Exception as e:
        logger.error(f"Ошибка при обработке запроса обратного вызова: {e}")


@bot.message_handler(func=lambda message: user_states.get(message.chat.id, {}).get('ascii_chars') == 'waiting')
def get_ascii_chars(message):
    """
    Обрабатывает ввод пользователя для набора символов для ASCII-арта.

    Args:
        message (telebot.types.Message): Сообщение от пользователя.
    """
    logger.info(f"Обработка символов ASCII, вводимых пользователем: {message.chat.id}")
    try:
        # Сохраняем введенные пользователем символы
        user_states[message.chat.id]['ascii_chars'] = message.text
        # Вызываем функцию для обработки ASCII-арта
        process_ascii_art(message)
    except Exception as e:
        logger.error(f"Ошибка при обработке ввода символов ASCII: {e}")


def process_image(message, image_processing_func, *args):
    """
    Обрабатывает изображение с помощью указанной функции и отправляет результат пользователю.

    Args:
        message (telebot.types.Message): Сообщение от пользователя.
        image_processing_func (function): Функция для обработки изображения.
        *args: Дополнительные аргументы для функции обработки изображения.
    """
    logger.info(f"Обработка изображения пользователем: {message.chat.id}")
    try:
        # Получаем ID фотографии из состояния пользователя
        photo_id = user_states[message.chat.id]['photo']
        # Получаем информацию о файле по его ID
        file_info = bot.get_file(photo_id)
        # Скачиваем файл по его пути
        downloaded_file = bot.download_file(file_info.file_path)

        # Создаем поток данных из скачанного файла
        image_stream = io.BytesIO(downloaded_file)
        # Открываем изображение из потока данных
        image = Image.open(image_stream)
        # Обрабатываем изображение с помощью указанной функции
        processed_image = image_processing_func(image, *args)

        # Создаем новый поток данных для сохранения обработанного изображения
        output_stream = io.BytesIO()
        # Сохраняем обработанное изображение в поток данных в формате JPEG
        processed_image.save(output_stream, format="JPEG")
        # Перемещаем указатель потока данных в начало
        output_stream.seek(0)
        # Отправляем обработанное изображение пользователю
        bot.send_photo(message.chat.id, output_stream)
    except UnidentifiedImageError:
        logger.error("Ошибка при открытии изображения")
        bot.send_message(message.chat.id, "Не удалось открыть изображение. Пожалуйста, попробуйте другое изображение.")
    except Exception as e:
        logger.error(f"Ошибка при обработке и отправке изображения: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при обработке изображения.")


def process_ascii_art(message):
    """
    Преобразует изображение в ASCII-арт и отправляет его пользователю.

    Args:
        message (telebot.types.Message): Сообщение от пользователя.
    """
    logger.info(f"Преобразование изображения в формат ASCII и отправка пользователю: {message.chat.id}")
    try:
        # Получаем ID фотографии из состояния пользователя
        photo_id = user_states[message.chat.id]['photo']
        # Получаем набор символов из состояния пользователя
        ascii_chars = user_states[message.chat.id]['ascii_chars']

        # Получаем информацию о файле по его ID
        file_info = bot.get_file(photo_id)

        # Скачиваем файл по его пути
        downloaded_file = bot.download_file(file_info.file_path)

        # Создаем поток данных из скачанного файла
        image_stream = io.BytesIO(downloaded_file)

        # Преобразуем изображение в ASCII-арт с использованием пользовательского набора символов
        ascii_art = image_to_ascii(image_stream, ascii_chars=ascii_chars)

        # Отправляем ASCII-арт пользователю с использованием MarkdownV2
        bot.send_message(message.chat.id, f"```\n{ascii_art}\n```", parse_mode="MarkdownV2")
    except UnidentifiedImageError:
        logger.error("Ошибка при открытии изображения")
        bot.send_message(message.chat.id, "Не удалось открыть изображение. Пожалуйста, попробуйте другое изображение.")
    except Exception as e:
        logger.error(f"Ошибка при преобразовании изображения в ASCII-арт и отправке: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при обработке изображения.")


# Запускаем бота
try:
    # Запускаем бота в режиме опроса
    bot.polling(none_stop=True)
except Exception as e:
    logger.error(f"Ошибка при запуске бота: {e}")
