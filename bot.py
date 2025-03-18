import logging
import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, MessageHandler, CallbackContext, CallbackQueryHandler, filters
import requests

TOKEN = "7920636690:AAFj5XUo8GepoQ6MLnoqBKUEP4wsr_9b8rc"  # Вставь токен бота
ADMINS_GROUP_ID = -1002699386364  # ID группы для админов
PUBLIC_GROUP_ID = -1002655152911  # ID группы "Подслушано"

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Функция для поддержания активности бота
async def keep_alive():
    while True:
        await asyncio.sleep(30)
        requests.get("https://your-railway-url.com")  # Пример для Railway

async def handle_message(update: Update, context: CallbackContext):
    """Получает анонимное сообщение и отправляет его в админскую группу с кнопками 'Опубликовать' и 'Отклонить'."""
    message_text = update.message.text
    logger.info(f"Получено анонимное сообщение: {message_text}")

    # Кнопки для публикации или отклонения сообщения
    keyboard = [
        [
            InlineKeyboardButton("✅ Опубликовать", callback_data=f"publish_{update.message.message_id}"),
            InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{update.message.message_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Отправка сообщения в админскую группу с кнопками
    try:
        await context.bot.send_message(
            chat_id=ADMINS_GROUP_ID,
            text=f"📩 *Новое сообщение:*\n\n{message_text}",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
        logger.info("Сообщение отправлено в админскую группу с кнопками")
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения в админскую группу: {e}")

async def publish_message(update: Update, context: CallbackContext):
    """Обрабатывает нажатие кнопки 'Опубликовать' и отправляет сообщение в основную группу."""
    query = update.callback_query
    await query.answer()

    # Извлекаем ID сообщения, которое надо переслать
    message_id = int(query.data.split("_")[1])
    logger.info(f"Опубликовано сообщение с ID: {message_id}")

    # Получаем текст сообщения из callback_query
    try:
        original_message_text = query.message.text
        logger.info(f"Текст сообщения для публикации: {original_message_text}")
    except Exception as e:
        logger.error(f"Ошибка при получении текста сообщения: {e}")
        await query.edit_message_text(text="❌ Ошибка при получении текста сообщения.")
        return

    # Отправляем текст в основную группу "Подслушано"
    try:
        await context.bot.send_message(
            chat_id=PUBLIC_GROUP_ID,
            text=f"📢 *Сообщение:*\n\n{original_message_text}",
            parse_mode="Markdown"
        )
        logger.info(f"Сообщение отправлено в группу 'Подслушано'")
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения в группу 'Подслушано': {e}")
        await query.edit_message_text(text="❌ Ошибка при публикации сообщения.")

    # Редактируем сообщение в админской группе, убирая кнопки
    await query.edit_message_text(text="✅ Сообщение опубликовано!")

async def reject_message(update: Update, context: CallbackContext):
    """Обрабатывает нажатие кнопки 'Отклонить' и удаляет сообщение из админской группы."""
    query = update.callback_query
    await query.answer()

    # Извлекаем ID сообщения, которое отклоняем
    message_id = int(query.data.split("_")[1])
    logger.info(f"Отклонено сообщение с ID: {message_id}")

    # Удаляем сообщение из админской группы
    try:
        await context.bot.delete_message(chat_id=query.message.chat_id, message_id=message_id)
        logger.info(f"Сообщение удалено из админской группы")
    except Exception as e:
        logger.error(f"Ошибка при удалении сообщения из админской группы: {e}")

    # Редактируем сообщение в админской группе, убирая кнопки
    await query.edit_message_text(text="❌ Сообщение отклонено!")

# Инициализация бота
application = Application.builder().token(TOKEN).build()

# Обработчик входящих сообщений (принимает анонимные сообщения)
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Обработчик кнопки "Опубликовать"
application.add_handler(CallbackQueryHandler(publish_message, pattern="^publish_"))

# Обработчик кнопки "Отклонить"
application.add_handler(CallbackQueryHandler(reject_message, pattern="^reject_"))

# Запуск бота
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(keep_alive())  # Запускаем keep_alive
    loop.run_until_complete(application.run_polling())  # Запускаем основной процесс бота
