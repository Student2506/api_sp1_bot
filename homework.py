import logging
import os
import time
# import datetime as dt

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()


PRAKTIKUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

logging.basicConfig(
    level=logging.DEBUG,
    filename='bot_debug.log',
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
)


def parse_homework_status(homework):
    homework_name = homework['homework_name']
    if homework['status'] != 'approved':
        verdict = 'К сожалению, в работе нашлись ошибки.'
    else:
        verdict = 'Ревьюеру всё понравилось, работа зачтена!'
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homeworks(current_timestamp):
    headers = {'Authorization': 'OAuth ' + PRAKTIKUM_TOKEN}
    params = {'from_date': current_timestamp}
    homework_statuses = requests.get(
        'https://praktikum.yandex.ru/api/user_api/homework_statuses/',
        headers=headers, params=params
    )
    return homework_statuses.json()


def send_message(message, chat_id):
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    logging.info('Отправляем сообщение')
    return bot.send_message(chat_id, message)


def main():
    current_timestamp = int(time.time())  # Начальное значение timestamp
    logging.debug('Бот стартовал')
    # current_timestamp = (
    #   int((dt.datetime.now() - dt.timedelta(days=16)).timestamp())
    # )

    statuses = {}
    while True:
        try:
            homeworks = get_homeworks(current_timestamp)
            for homework in homeworks['homeworks']:
                if statuses.get(homework['id']) != homework['status']:
                    message = parse_homework_status(homework)
                    send_message(message, CHAT_ID)
                    statuses[homework['id']] = homework['status']

            time.sleep(5 * 60)  # Опрашивать раз в пять минут

        except Exception as e:
            logging.error(f'Бот упал с ошибкой: {e}')
            send_message(f'Бот упал с ошибкой: {e}', CHAT_ID)
            time.sleep(5)


if __name__ == '__main__':
    main()
