# Многофункциональный Telegram-бот

Этот проект представляет собой Telegram-бота, который может обрабатывать изображения, отправленные пользователем, и выполнять с ними две операции: пикселизацию и преобразование в ASCII-арт. Бот использует библиотеку `pyTelegramBotAPI` для взаимодействия с Telegram API и библиотеку `Pillow` для обработки изображений.

## Содержание

- [Установка](#установка)
- [Основные функции](#основные-функции)
- [Структура проекта](#структура-проекта)
- [Основные функции в bot.py](#основные-функции-в-botpy)
- [Контакты](#контакты)

## Установка

1. **Клонируйте репозиторий:**

   ```bash
   https://github.com/kenisdee/TG_Bot.git

2. **Перейдите в директорию проекта:**

   ```bash
   cd TG_Bot

3. **Создайте виртуальное окружение:**

   ```bash
   python3 -m venv venv

4. **Активируйте виртуальное окружение:**

   ```bash
   source venv/bin/activate

5. **Установите зависимости:**

   ```bash
   pip3 install -r requirements.txt
   
6. **Настройка токена бота:**

Создайте файл token.txt в любой директории.

Поместите туда токен вашего бота, полученный от BotFather в Telegram.

Замените "/путь/к/файлу/token.txt" в функции get_token на свой путь.

7. **Запустите бота:**

   ```bash
   python3 bot.py

## Основные функции

1. **Пикселизация изображения**: Бот уменьшает изображение до размера, кратного заданному размеру пикселя, а затем увеличивает его обратно до исходного размера, используя метод ближайшего соседа. Это создает эффект пикселизации.

2. **Преобразование в ASCII-арт**: Бот преобразует изображение в текст, используя набор символов, выбранный пользователем. Изображение сначала преобразуется в оттенки серого, затем уменьшается до нужного размера, и каждый пиксель заменяется соответствующим символом из набора.

## Структура проекта

- **bot.py**: Основной файл бота, содержащий логику обработки команд, фотографий и обратных вызовов.
- **requirements.txt**: Файл, содержащий список зависимостей проекта.


## Основные функции в `bot.py`

### Импорты и настройки

- **telebot**: Используется для взаимодействия с Telegram API.
- **Pillow (PIL)**: Предоставляет инструменты для работы с изображениями.
- **TOKEN**: Строковая переменная, куда вы должны поместить токен вашего бота.
- **bot = telebot.TeleBot(TOKEN)**: Создает экземпляр бота для взаимодействия с Telegram.

### Хранение состояний пользователей

- **user_states**: Используется для отслеживания действий или состояний пользователей. Например, какое изображение было отправлено.

### Пикселизация

**pixelate_image(image, pixel_size):**

- Принимает изображение и размер пикселя. Уменьшает изображение до размера, где один пиксель представляет большую область, затем увеличивает обратно, создавая пиксельный эффект.

### Преобразование в ASCII-арт

**Подготовка изображения:**

- **resize_image(image, new_width=100)**: Изменяет размер изображения с сохранением пропорций.
- **grayify(image)**: Преобразует цветное изображение в оттенки серого.
- **image_to_ascii(image_stream, new_width=40)**: Основная функция для преобразования изображения в ASCII-арт. Изменяет размер, преобразует в градации серого и затем в строку ASCII-символов.
- **pixels_to_ascii(image)**: Конвертирует пиксели изображения в градациях серого в строку ASCII-символов, используя предопределенную строку ASCII_CHARS.

### Взаимодействие с пользователем

#### Обработчики сообщений

- **@bot.message_handler(commands=['start', 'help'])**: Реагирует на команды `/start` и `/help`, отправляя приветственное сообщение.
- **@bot.message_handler(content_types=['photo'])**: Реагирует на изображения, отправляемые пользователем, и предлагает варианты обработки.

#### Клавиатура для взаимодействия

- **get_options_keyboard()**: Создает клавиатуру с кнопками для выбора пользователем, как обработать изображение: через пикселизацию или преобразование в ASCII-арт.

### Обработка запросов

#### Обработка колбэков

- **@bot.callback_query_handler(func=lambda call: True)**: Определяет действия в ответ на выбор пользователя (например, пикселизация или ASCII-арт) и вызывает соответствующую функцию обработки.

### Отправка результатов

#### Функции отправки

- **pixelate_and_send(message)**: Пикселизирует изображение и отправляет его обратно пользователю.
- **ascii_and_send(message)**: Преобразует изображение в ASCII-арт и отправляет результат в виде текстового сообщения.

## Контакты

Для связи с автором проекта, пожалуйста, используйте следующие контактные данные:

Email: kenisdee@ya.ru

GitHub: https://github.com/kenisdee