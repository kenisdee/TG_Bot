import io

import telebot
from PIL import Image
from telebot import types


# Функция для чтения токена из файла
def get_token():
    """
    Читает токен бота из файла.

    Returns:
        str: Токен бота.
    """
    with open('/Users/kenisdee/TG_Token/token.txt', 'r') as file:
        return file.read().strip()


# Получаем токен
TOKEN = get_token()
bot = telebot.TeleBot(TOKEN)


# Удаляем вебхук, если он активен
def delete_webhook():
    """
    Удаляет вебхук, если он активен.
    """
    bot.remove_webhook()


delete_webhook()

user_states = {}  # тут будем хранить информацию о действиях пользователя

# набор символов из которых составляем изображение
ASCII_CHARS = '@%#*+=-:. '


def resize_image(image, new_width=100):
    """
    Изменяет размер изображения, сохраняя пропорции.

    Args:
        image (PIL.Image.Image): Исходное изображение.
        new_width (int): Новая ширина изображения.

    Returns:
        PIL.Image.Image: Измененное изображение.
    """
    # Получаем текущие размеры изображения
    width, height = image.size
    # Вычисляем отношение высоты к ширине
    ratio = height / width
    # Вычисляем новую высоту, сохраняя пропорции
    new_height = int(new_width * ratio)
    # Изменяем размер изображения
    return image.resize((new_width, new_height))


def grayify(image):
    """
    Преобразует изображение в оттенки серого.

    Args:
        image (PIL.Image.Image): Исходное изображение.

    Returns:
        PIL.Image.Image: Изображение в оттенках серого.
    """
    return image.convert("L")


def image_to_ascii(image_stream, new_width=40):
    """
    Преобразует изображение в ASCII-арт.

    Args:
        image_stream (io.BytesIO): Поток данных изображения.
        new_width (int): Новая ширина изображения для ASCII-арта.

    Returns:
        str: ASCII-арт изображения.
    """
    # Переводим в оттенки серого
    image = Image.open(image_stream).convert('L')

    # меняем размер сохраняя отношение сторон
    width, height = image.size
    aspect_ratio = height / width
    new_height = int(aspect_ratio * new_width * 0.55)  # 0,55 так как буквы выше чем шире
    img_resized = image.resize((new_width, new_height))

    img_str = pixels_to_ascii(img_resized)
    img_width = img_resized.width

    # Ограничиваем количество символов для сообщения в Telegram
    max_characters = 4000 - (new_width + 1)
    max_rows = max_characters // (new_width + 1)

    ascii_art = ""
    for i in range(0, min(max_rows * img_width, len(img_str)), img_width):
        ascii_art += img_str[i:i + img_width] + "\n"

    return ascii_art


def pixels_to_ascii(image):
    """
    Преобразует пиксельные данные изображения в ASCII-символы.

    Args:
        image (PIL.Image.Image): Изображение в оттенках серого.

    Returns:
        str: Строка ASCII-символов, представляющая изображение.
    """
    pixels = image.getdata()
    characters = ""
    for pixel in pixels:
        characters += ASCII_CHARS[pixel * len(ASCII_CHARS) // 256]
    return characters


# Огрубляем изображение
def pixelate_image(image, pixel_size):
    """
    Пикселизирует изображение.

    Args:
        image (PIL.Image.Image): Исходное изображение.
        pixel_size (int): Размер пикселя для пикселизации.

    Returns:
        PIL.Image.Image: Пикселизированное изображение.
    """
    # Уменьшаем изображение до размера, кратного pixel_size
    image = image.resize(
        (image.size[0] // pixel_size, image.size[1] // pixel_size),
        Image.NEAREST
    )
    # Увеличиваем изображение обратно до исходного размера, используя метод ближайшего соседа
    image = image.resize(
        (image.size[0] * pixel_size, image.size[1] * pixel_size),
        Image.NEAREST
    )
    return image


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    """
    Обрабатывает команды /start и /help, отправляя приветственное сообщение.

    Args:
        message (telebot.types.Message): Сообщение от пользователя.
    """
    bot.reply_to(message, "Пришлите мне изображение, и я предложу вам варианты!")


@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    """
    Обрабатывает полученные фотографии, предлагая пользователю варианты действий.

    Args:
        message (telebot.types.Message): Сообщение от пользователя с фотографией.
    """
    bot.reply_to(message, "У меня есть ваша фотография! Пожалуйста, выберите, что бы вы хотели с ней сделать.",
                 reply_markup=get_options_keyboard())
    # Сохраняем ID фотографии в состояние пользователя
    user_states[message.chat.id] = {'photo': message.photo[-1].file_id}


def get_options_keyboard():
    """
    Создает и возвращает клавиатуру с вариантами действий.

    Returns:
        telebot.types.InlineKeyboardMarkup: Клавиатура с вариантами действий.
    """
    # Создаем инлайн-клавиатуру
    keyboard = types.InlineKeyboardMarkup()

    # Добавляем кнопку для пикселизации изображения
    pixelate_btn = types.InlineKeyboardButton("Pixelate", callback_data="pixelate")

    # Добавляем кнопку для преобразования изображения в ASCII-арт
    ascii_btn = types.InlineKeyboardButton("ASCII Art", callback_data="ascii")

    # Добавляем кнопки в клавиатуру
    keyboard.add(pixelate_btn, ascii_btn)

    # Возвращаем созданную клавиатуру
    return keyboard


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    """
    Обрабатывает выбор пользователя из инлайн-клавиатуры.

    Args:
        call (telebot.types.CallbackQuery): Объект, представляющий запрос обратного вызова.
    """
    # Если пользователь выбрал пикселизацию изображения
    if call.data == "pixelate":
        bot.answer_callback_query(call.id, "Пикселизация вашего изображения...")
        pixelate_and_send(call.message)
    # Если пользователь выбрал преобразование в ASCII-арт
    elif call.data == "ascii":
        bot.answer_callback_query(call.id, "Преобразование вашего изображения в формат ASCII art...")
        ascii_and_send(call.message)


def pixelate_and_send(message):
    """
    Пикселизирует изображение и отправляет его пользователю.

    Args:
        message (telebot.types.Message): Сообщение от пользователя.
    """
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
    # Пикселизируем изображение с размером пикселя 20
    pixelated = pixelate_image(image, 20)

    # Создаем новый поток данных для сохранения пикселизированного изображения
    output_stream = io.BytesIO()
    # Сохраняем пикселизированное изображение в поток данных в формате JPEG
    pixelated.save(output_stream, format="JPEG")
    # Перемещаем указатель потока данных в начало
    output_stream.seek(0)
    # Отправляем пикселизированное изображение пользователю
    bot.send_photo(message.chat.id, output_stream)


def ascii_and_send(message):
    """
    Преобразует изображение в ASCII-арт и отправляет его пользователю.

    Args:
        message (telebot.types.Message): Сообщение от пользователя.
    """
    # Получаем ID фотографии из состояния пользователя
    photo_id = user_states[message.chat.id]['photo']

    # Получаем информацию о файле по его ID
    file_info = bot.get_file(photo_id)

    # Скачиваем файл по его пути
    downloaded_file = bot.download_file(file_info.file_path)

    # Создаем поток данных из скачанного файла
    image_stream = io.BytesIO(downloaded_file)

    # Преобразуем изображение в ASCII-арт
    ascii_art = image_to_ascii(image_stream)

    # Отправляем ASCII-арт пользователю с использованием MarkdownV2
    bot.send_message(message.chat.id, f"```\n{ascii_art}\n```", parse_mode="MarkdownV2")


# Запускаем бота
bot.polling(none_stop=True)
