import os
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, InputFile
from telegram.ext import CallbackContext, Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
import schedule
import time

TOKEN = '6595098561:AAFLnPj-rPuut5lFJwfJff_G1pWo_k96D20'
folder_path = 'D:/Pictures'
data_file_path = "../downloaded.txt"
queue_delay = 30
channel_id = -1002134624887
allowed_user_ids = {6913094634}
publication_queue = []

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


def check_status(file_name: str) -> bool:
    file_path = '../downloaded.txt'

    with open(file_path, 'a+') as file:
        file.seek(0)
        lines = file.readlines()

        for line in lines:
            name, status = line.strip().split(',')
            if name == file_name:
                if status == 'downloaded':
                    return True
                else:
                    return False

        file.write(file_name + ',uploaded to bot\n')
        return True


def change_status(file_name, new_status):
    with open('../downloaded.txt', 'r') as file:
        lines = file.readlines()
    with open('../downloaded.txt', 'w') as file:
        for i, line in enumerate(lines):
            current_file_name, current_status = map(str.strip, line.split(','))
            if current_file_name == file_name:
                lines[i] = f"{file_name},{new_status}\n"
                logging.info(f"{file_name} status changed to {new_status}.")
                break
        file.writelines(lines)


def handle_text(update: Update, context: CallbackContext) -> None:
    user_text = update.message.text.lower()
    user_id = update.message.from_user.id

    logging.info(f"User {user_id} sent command: {user_text}")

    if user_text == '/start':
        start(update, context)
    elif user_text == 'preview':
        show_media_preview(update, context)
    elif user_text == 'view queue':
        view_queue(update, context)


def show_media_preview(update: Update, context: CallbackContext) -> None:
    media_files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]

    for file in media_files:
        file_path = os.path.join(folder_path, file)

        if check_status(file):
            button_text = f"Upload {file}"
            button_callback = f"upload_{file}"

            keyboard = [[InlineKeyboardButton(button_text, callback_data=button_callback)]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            try:
                with open(file_path, 'rb') as picture:
                    context.bot.send_photo(update.message.chat_id, photo=picture, reply_markup=reply_markup)

                change_status(file_path, "Uploaded to bot")

            except Exception as e:
                logging.error(f"Error sending media preview: {e}")


def add_to_queue(file_name):
    publication_queue.append(file_name)


def job_send_file_to_channel(context):
    logging.info("Проверка очереди публикации.")
    if publication_queue:
        file_name = publication_queue[0]
        file_path = os.path.join(folder_path, file_name)

        try:
            with open(file_path, 'rb') as file:
                context.bot.send_photo(chat_id=channel_id, photo=InputFile(file), timeout=120)

            publication_queue.pop(0)
            logging.info(f"Файл {file_name} отправлен в канал.")
        except Exception as e:
            logging.error(f"Ошибка отправки файла: {e}")
    else:
        logging.info("Нет файлов в очереди публикации.")


def view_queue(update: Update, context: CallbackContext) -> None:
    queue_length = len(publication_queue)
    update.message.reply_text(f"There are {queue_length} images in the publication queue.")


def start(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    logging.info(f"User {user_id} connected and sent command: /start")

    if user_id in allowed_user_ids:
        custom_keyboard = [['Preview', 'View Queue']]
        reply_markup = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
        update.message.reply_text(f"Hello! Your user ID: {user_id}. Use the menu to see media previews.",
                                  reply_markup=reply_markup)

        schedule.every(queue_delay).minutes.do(job_send_file_to_channel, context=context)

    else:
        update.message.reply_text("Sorry, you are not authorized to use this bot.")


def button_callback_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    file_name = query.data.split("_")[1]
    add_to_queue(file_name)
    query.answer(text=f"{file_name} added to the queue.")


def main() -> None:
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text))
    dp.add_handler(MessageHandler(Filters.regex(r'^Preview$'), show_media_preview))
    dp.add_handler(MessageHandler(Filters.regex(r'^View Queue$'), view_queue))
    dp.add_handler(CallbackQueryHandler(button_callback_handler))

    updater.start_polling()

    while True:
        schedule.run_pending()
        time.sleep(1)  # Спать на короткое время, чтобы избежать высокого использования CPU

    updater.idle()


if __name__ == "__main__":
    main()
