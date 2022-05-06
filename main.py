import json

import requests
import telegram
import yandex_music
from bs4 import BeautifulSoup
from telegram import ReplyKeyboardMarkup
from telegram.ext import CommandHandler
from telegram.ext import Updater, MessageHandler, Filters

TOKEN = '5235499125:AAEIV0Xurji0IJTAnPUTWYx7u8z_sFtzb3U'

start_keyboard = [['.Показать ваш плейлист'], ['.Создать ссылку на плейлист'], ['.'], ['.']]
add_keyboard = [['.Показать ваш плейлист'], ['.Создать ссылку на плейлист'], ['✅Добавить в плейлист✅'],
                ['.Показать текст']]
delete_keyboard = [['.Показать ваш плейлист'], ['.Создать ссылку на плейлист'], ['❌Удалить из плейлиста❌'],
                   ['.Показать текст']]

start_markup = ReplyKeyboardMarkup(start_keyboard, one_time_keyboard=False)
add_markup = ReplyKeyboardMarkup(add_keyboard, one_time_keyboard=False)
delete_markup = ReplyKeyboardMarkup(delete_keyboard, one_time_keyboard=False)

charts = []

modes = {}  # 0 - обычный, 1 - режим выбора, 2 - режим выбора из альбома по сслыке, 3 - режим выбора из чарта
users_data = {}

YANDEX_TOKEN = 'AQAAAABFn9XwAAG8XpXLLwrUT0RRlhygDi0DdUM'


class Song_List:
    def __init__(self):
        self.filename = 'data.json'

    def create_deep_link(self, chat_id):
        return f'https://t.me/krotow_bot?start=playlist_user_id_{chat_id}'

    def add_song_to_list(self, name: str, chat_id: int):
        with open(self.filename, 'r') as file:
            dict = json.load(file)
        if str(chat_id) in dict.keys():
            if name not in dict[str(chat_id)]:
                dict[str(chat_id)].append(name)
        else:
            dict[str(chat_id)] = [name]
        with open(self.filename, 'w') as file:
            json.dump(dict, file, ensure_ascii=False)

    def get_song_list(self, chat_id):
        with open(self.filename, 'r') as file:
            dict = json.load(file)
        return dict[str(chat_id)] if str(chat_id) in dict.keys() else 'Пусто'

    def delete_song(self, chat_id, name):
        with open(self.filename, 'r') as file:
            dict = json.load(file)
        del dict[str(chat_id)][dict[str(chat_id)].index(name)]
        if not dict[str(chat_id)]:
            del dict[str(chat_id)]
        with open(self.filename, 'w') as file:
            json.dump(dict, file, ensure_ascii=False)


class Search:
    def __init__(self):
        pass

    def search(self, name, chat_id):
        track_id, album_id, search_result = self.get_ides(name)
        inf = client.tracks_download_info(track_id)[0]
        client.tracks(f'{track_id}:{album_id}')[0].download(f'tracks/{chat_id}.mp3', codec=inf['codec'],
                                                            bitrate_in_kbps=inf['bitrate_in_kbps'])

        try:
            artist_name = search_result['best']['result']['artists'][0]['name']
            song_name = search_result['best']['result']['title']
            return artist_name, song_name
        except KeyError:
            return "Такую песню я не знаю"
        except TypeError:
            return "Такую песню я не знаю"

    def get_ides(self, name):
        search_result = json.loads(client.search(name).to_json())
        track_id = search_result['best']['result']['id_']
        album_id = search_result['best']['result']['albums'][0]['id_']
        return track_id, album_id, search_result


SONGLIST = Song_List()
SEARCH = Search()
client = yandex_music.Client(YANDEX_TOKEN)


def delete_song_from_list(update, chat_id, name):
    SONGLIST.delete_song(chat_id, name)
    update.message.reply_text('Успешно', reply_markup=start_markup)
    global modes, users_data
    modes[chat_id] = 0
    users_data[chat_id]['last'] = ''


def print_song_list(update, chat_id=None):
    if not chat_id:
        chat_id = update.message.chat_id
    spisok = SONGLIST.get_song_list(chat_id)
    if spisok == 'Пусто':
        update.message.reply_text(spisok, reply_markup=start_markup)
    else:
        spisok = list(enumerate(spisok, start=1))
        spisok = list(map(lambda x: f'{x[0]} - {x[1]}', spisok))
        spisok = '\n'.join(spisok)
        update.message.reply_text(spisok, reply_markup=start_markup)
        global modes, users_data
        modes[update.message.chat_id] = 1
        if chat_id != update.message.chat_id:
            spisok = SONGLIST.get_song_list(chat_id)
            users_data[update.message.chat_id]['playlist_link'] = spisok


def link(update, context):
    link_ = SONGLIST.create_deep_link(update.message.chat_id)
    update.message.reply_text(link_)


def add_song(update, name):
    SONGLIST.add_song_to_list(name, update.message.chat_id)
    update.message.reply_text('успешно', reply_markup=start_markup)


def top10(context: telegram.ext.CallbackContext):
    global charts, modes
    with open('users.json', 'r') as file:
        chat_ids = json.load(file)['users']

    spisok = list(map(lambda x: f"{x['track']['artists'][0]['name']}  -  {x['track']['title']}",
                      client.chart()['chart']['tracks'][:10]))
    charts = spisok.copy()
    spisok = list(map(lambda x: f"{x[0] + 1} - {x[1]}", list(enumerate(spisok))))
    spisok.insert(0, f'🔥 TOP 🔟 🔥')
    spisok = '\n'.join(spisok)
    for elem in chat_ids:
        context.bot.send_message(chat_id=elem, text=spisok)
        modes[int(elem)] = 3


def echo(update, context):
    print(update.message.text)
    global modes
    global users_data
    if update.message.text == '.Показать ваш плейлист':
        print_song_list(update)
    elif update.message.text == '.Показать текст':
        name = users_data[update.message.chat_id]['last']
        response = SEARCH.get_ides(name)
        track_id, album_id = response[0], response[1]
        lyrics = get_text(track_id, album_id)
        update.message.reply_text(lyrics)

    elif update.message.text == '✅Добавить в плейлист✅':
        name = users_data[update.message.chat_id]['last']

        add_song(update, name)
    elif update.message.text == '❌Удалить из плейлиста❌':
        name = users_data[update.message.chat_id]['last']
        delete_song_from_list(update, update.message.chat_id, name)
    elif update.message.text == '.Создать ссылку на плейлист':
        link(update, context)
    else:
        if update.message.chat_id not in modes.keys():
            modes[update.message.chat_id] = 0
            users_data[update.message.chat_id] = {'last': '', 'playlist': 'self'}
        if modes[update.message.chat_id] == 0:
            if not update.message.text[0] == '/':
                play_song(update, update.message.text)
        elif modes[update.message.chat_id] == 1:
            if update.message.text.isnumeric():
                name = get_name_by_num(update, update.message.text)
                if name:
                    play_song(update, name)
                else:
                    update.message.reply_text("Неправильный номер")
            else:
                modes[update.message.chat_id] = 0
                play_song(update, update.message.text)
        elif modes[update.message.chat_id] == 2:
            if update.message.text.isnumeric():
                if 'playlist_link' in users_data[update.message.chat_id].keys():
                    spisok = users_data[update.message.chat_id]['playlist_link']
                    name = get_name_by_num(update, update.message.text, spisok)
                    if name:
                        play_song(update, name, spisok)
                    else:
                        update.message.reply_text("Неправильный номер")
            else:
                modes[update.message.chat_id] = 0
                play_song(update, update.message.text)
        elif modes[update.message.chat_id] == 3:
            if update.message.text.isnumeric():
                global charts
                name = get_name_by_num(update, update.message.text, charts)
                if name:
                    play_song(update, name, charts)
                else:
                    update.message.reply_text("Неправильный номер")
            else:
                modes[update.message.chat_id] = 0
                play_song(update, update.message.text)


def get_name_by_num(update, num, spisok=None):
    if not spisok:
        spisok = SONGLIST.get_song_list(update.message.chat_id)
    if 0 < int(num) <= len(spisok):
        return spisok[int(num) - 1]


def play_song(update, name, spisok=None):
    name = SEARCH.search(name, update.message.chat_id)
    name = f"{name[0]} - {name[1]}"
    with open(f'tracks/{update.message.chat_id}.mp3', 'rb') as r:
        if not spisok:
            spisok = SONGLIST.get_song_list(update.message.chat_id)
        if name not in spisok:
            update.message.reply_text(name, reply_markup=add_markup)
        elif spisok != 'Пусто' and name in spisok:
            update.message.reply_text(name, reply_markup=delete_markup)

        update.message.reply_voice(r)
    global users_data
    users_data[update.message.chat_id]['last'] = name


def get_text(trackid, albumid):
    url = f'https://music.yandex.ru/album/{albumid}/track/{trackid}'
    html = requests.get(url).text
    soupObj = BeautifulSoup(html)
    lyrics = soupObj.find('div', attrs={"class": "sidebar-track__lyric-text"}).text
    return lyrics


def test_top10(update, context):
    top10(context)


def start(update, context):
    with open('users.json', 'r') as file:
        dict = json.load(file)
    if str(update.message.chat_id) not in dict['users']:
        dict['users'].append(str(update.message.chat_id))
        with open('users.json', 'w') as file:
            json.dump(dict, file, ensure_ascii=False)

    global modes, users_data

    modes[update.message.chat_id] = 0
    users_data[update.message.chat_id] = {'last': '', 'playlist': 'self'}
    if context.args:
        if "playlist_user_id" in context.args[0]:
            chat_id_ = context.args[0][17:]
            print_song_list(update, chat_id_)
            users_data[update.message.chat_id]['playlist'] = 'link'
            modes[update.message.chat_id] = 2
    else:
        update.message.reply_text("Это Музыкальный бот. Напишите название песни", reply_markup=start_markup)


def main():
    global modes
    with open('users.json', 'r') as file:
        users_ids = json.load(file)['users']
    for id in users_ids:
        modes[int(id)] = 0
        users_data[int(id)] = {'last': '', 'playlist': 'self'}

    updater = Updater(TOKEN, use_context=True)

    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))

    dp.add_handler(CommandHandler("top10", test_top10))

    dp.add_handler(MessageHandler(Filters.text, echo))

    interval = 60 * 60 * 24 * 7  # неделя

    updater.job_queue.run_repeating(top10, interval)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
