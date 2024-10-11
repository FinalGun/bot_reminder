import logging
import os
import sys
import sqlite3 as sl
import threading
import time
from datetime import datetime
import requests

from telebot import TeleBot
from dotenv import load_dotenv

from filters_messages import (filter_message_for_delete,
                              filter_message_for_search,
                              filter_message_for_add
                              )

load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

bot = TeleBot(token=TELEGRAM_TOKEN)

con = sl.connect('dates.db', check_same_thread=False)

logger = logging.getLogger(__name__)

with con:
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS dates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date VARCHAR(40),
            time VARCHAR(40),
            text VARCHAR(500)
        );
    """
    )


def send_message(chat_id, text):
    global bot
    try:
        bot.send_message(chat_id, text)
        logger.debug(f'Сообщение отправлено {chat_id}: {text}')
    except Exception as error:
        logger.error(f'Ошибка отправки сообщения {chat_id}: {error}')


@bot.message_handler(commands=['start'])
def start(message):
    send_message(
        chat_id=message.chat.id,
        text='Привет, я бот напоминалка. Я умею запоминать событие и '
        'напоминать о нем в нужное время. Для добавления события '
        'отправьте сообщение в формате: "add число-месяц;часы:минуты;<ваше '
        'событие>. Пример: "add 21-03;00:00;Пуф Дусин".'
        'Для просмотра всех событий используйте команду '
        '/all_events. Для удаления события отправьте сообщение в '
        'формате "del <id события>". Для поиска событий по дате отправьте '
        'сообщение в формате "date число-месяц".',
    )


@bot.message_handler(commands=['all_events'])
def get_all_events(message):
    with con:
        data = con.execute(
            'SELECT * FROM dates',
        ).fetchall()
    if data:
        messages_list = []
        for event in data:
            id, date, time_, text = event
            event_message = f'id: {id}. Дата: {date}. Время: {time_}. Событие: {text}'
            messages_list.append(event_message)
        send_message(message.chat.id, str.join('\n', messages_list))
    else:
        send_message(message.chat.id, 'Событий нет.')


@bot.message_handler(commands=['opinion'])
def opinion(message):
    send_message(
        message.chat.id, requests.get('https://yesno.wtf/api/').json()['image']
    )


@bot.message_handler(commands=['yes'])
def opinion(message):
    send_message(
        message.chat.id, requests.get(
            'https://yesno.wtf/api/?force=yes').json()['image']
    )


@bot.message_handler(commands=['no'])
def opinion(message):
    send_message(
        message.chat.id, requests.get('https://yesno.wtf/api/?force=no').json()['image']
    )


@bot.message_handler(func=filter_message_for_delete)
def delete_event(message):
    event_id = int(message.text.split(' ')[1])
    with con:
        con.execute(
            'DELETE FROM dates WHERE id = :event_id;',
            {'event_id': event_id},
        )
    send_message(message.chat.id, 'Event deleted.')


@bot.message_handler(func=filter_message_for_search)
def search_by_date(message):
    with con:
        data = (
            con.execute(
                'SELECT * FROM dates WHERE date = :event_date;',
                {'event_date': message.text.split(' ')[1]},
            )
        ).fetchall()
    if data:
        for event in data:
            id, date, time_, text = event
            send_message(
                message.chat.id,
                f'id: {id}. Дата: {date}. Время: {time_}. Событие:' f' {text}',
            )
    else:
        send_message(message.chat.id, 'Событий нет.')


@bot.message_handler(func=filter_message_for_add)
def create_event(message):
    parts = message.text.replace('add ', '').split(';')
    if len(parts) != 3 or parts[0][2] != '-' or parts[1][2] != ':':
        send_message(
            message.chat.id,
            'Invalid input. Use format: ' '"число-месяц;часы:минуты;text"',
        )
        return
    con = sl.connect('dates.db')
    sql = 'INSERT INTO dates (date, time, text) values(?, ?, ?)'
    data = [
        (
            parts[0],
            parts[1],
            parts[2],
        )
    ]
    with con:
        con.executemany(sql, data)
        last_id = con.execute('SELECT last_insert_rowid()').fetchall()[0]
    send_message(message.chat.id, f'Событие добавлено! ID: {last_id[0]}')


def main():
    while True:
        try:
            bot.polling()
        except Exception as error:
            logger.error(f'Ошибка при опросе сервера ТГ: {error}')
            time.sleep(60)


def send_daily_reminder():
    while True:
        now_date = datetime.now().strftime('%d-%m')
        now_time = datetime.now().strftime('%H:%M')
        with con:
            data = (
                con.execute(
                    'SELECT * FROM dates WHERE date = :event_date;',
                    {'event_date': now_date},
                )
            ).fetchall()
        if data:
            for event in data:
                id, date, time_, text = event
                if time_ == now_time:
                    send_message(
                        chat_id=TELEGRAM_CHAT_ID,
                        text=f'Напоминание: id: {id}. Дата: {date}. Время:'
                        f' {time_}. '
                        f'Событие:'
                        f' {text}',
                    )
        time.sleep(59)


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(lineno)s'
        ' - %(levelname)s - %(message)s',
        level=logging.DEBUG,
        handlers=[
            logging.StreamHandler(stream=sys.stdout),
            logging.FileHandler(f'{__file__}.log', mode='w'),
        ],
    )
    thread1 = threading.Thread(target=main)
    thread2 = threading.Thread(target=send_daily_reminder)
    thread1.start()
    thread2.start()
    thread1.join()
    thread2.join()
