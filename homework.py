import logging
import os
import time

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()


PRAKTIKUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
SERVER_ROUND_TRIP_TIMEOUT = 60 * 10
SERVER_ERROR_REPEAT_TIMEOUT = SERVER_ROUND_TRIP_TIMEOUT
API_URL_PRAKTIKUM = (
    'https://praktikum.yandex.ru/api/user_api/homework_statuses/'
)

bot = telegram.Bot(token=TELEGRAM_TOKEN)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
)


def parse_homework_status(homework):
    statuses = {
        'approved': 'Ревьюеру всё понравилось, работа зачтена!',
        'rejected': 'К сожалению, в работе нашлись ошибки.'
    }
    homework_name = homework.get('homework_name')
    status = homework.get('status')

    if homework_name is None and status is None:
        return 'Неверный ответ сервера.'
    else:
        if status in statuses.keys():
            return ('У вас проверили работу '
                    f'"{homework_name}"!\n\n{statuses[status]}')
        elif status == 'reviewing':
            return f'Работа "{homework_name}" ушла на проверку'
    return 'Неверный ответ сервера.'


def get_homeworks(current_timestamp=None):
    homework_statuses = []
    headers = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
    if current_timestamp is None:
        current_timestamp = int(time.time())
    params = {'from_date': current_timestamp}
    try:
        homework_statuses = requests.get(
            API_URL_PRAKTIKUM,
            headers=headers, params=params
        )
    except Exception as e:
        logging.error(f'Unable to get data from API: {e}')
        send_message(f'Unable to get data from API: {e}')

    return homework_statuses.json()


def send_message(message):
    logging.info('Отправляем сообщение')
    return bot.send_message(CHAT_ID, message)


def main():
    current_timestamp = int(time.time())
    logging.debug('Бот стартовал')
    status = ''
    while True:
        try:
            homeworks = get_homeworks(current_timestamp)
            if len(homeworks.get('homeworks')) > 0:
                current_homework = homeworks.get('homeworks')[0]
                if current_homework is not None:
                    message = parse_homework_status(current_homework)
                    logging.debug(message)
                    current_timestamp = current_homework.get('current_date')
                    if status != message:
                        send_message(message)
                        status = message

            time.sleep(SERVER_ROUND_TRIP_TIMEOUT)

        except Exception as e:
            logging.error(f'Бот упал с ошибкой: {e}')
            send_message(f'Бот упал с ошибкой: {e}')
            time.sleep(SERVER_ERROR_REPEAT_TIMEOUT)


if __name__ == '__main__':
    main()
