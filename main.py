import json

import yandex_music
from telegram import ReplyKeyboardMarkup
from telegram.ext import CommandHandler
from telegram.ext import Updater, MessageHandler, Filters

TOKEN = '5235499125:AAEIV0Xurji0IJTAnPUTWYx7u8z_sFtzb3U'

start_keyboard = [['.Показать ваш плейлист'], ['.Создать ссылку на плейлист'], ['.'], ['.']]
start_markup = ReplyKeyboardMarkup(start_keyboard, one_time_keyboard=False)


class Song_List:
    def __init__(self):
        self.filename = 'data.json'

    def create_deep_link(self, chat_id):
        return f'https://t.me/krotow_bot?start=playlist_user_id_{chat_id}'

    def open_deep_link(self, link):
        chat_id = link[17:]
        with open(self.filename, 'r') as file:
            dict = json.load(file)
        if str(chat_id) in dict.keys():
            return dict[str(chat_id)]

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


class Search:
    def __init__(self):
        pass

    def search(self, name, chat_id):
        search_result = json.loads(client.search(name).to_json())
        track_id = search_result['best']['result']['id_']
        album_id = search_result['best']['result']['albums'][0]['id_']
        inf = client.tracks_download_info(track_id)[0]
        client.tracks(f'{track_id}:{album_id}')[0].download(f'tracks/{chat_id}.mp3', codec=inf['codec'], bitrate_in_kbps=inf['bitrate_in_kbps'])

        try:
            artist_name = search_result['best']['result']['artists'][0]['name']
            song_name = search_result['best']['result']['title']
            print(artist_name, song_name)
            return f"{artist_name} - {song_name}"
        except KeyError:
            return "Такую песню я не знаю"
        except TypeError:
            return "Такую песню я не знаю"
        # links = client.tracks_download_info(search_result['best']['result']['id'])
        # print(links)


SONGLIST = Song_List()
SEARCH = Search()
client = yandex_music.Client()


def print_song_list(update, context):
    spisok = SONGLIST.get_song_list(update.message.chat_id)
    spisok = list(enumerate(spisok, start=1))
    spisok = list(map(lambda x: f'{x[0]} - {x[1]}', spisok))
    spisok = '\n'.join(spisok)
    update.message.reply_text(spisok)


def add_song(update, context):
    if context.args:
        name = ' '.join(context.args)
        SONGLIST.add_song_to_list(name, update.message.chat_id)
        update.message.reply_text('успешно')
    else:
        update.message.reply_text('Пожалуйста, введите название песни')


def link(update, context):
    link_ = SONGLIST.create_deep_link(update.message.chat_id)
    update.message.reply_text(link_)


def echo(update, context):
    if update.message.text == '.Показать ваш плейлист':
        print_song_list(update, context)
    elif update.message.text == '.Создать ссылку на плейлист':
        link(update, context)
    else:
        if not update.message.text[0] == '/':
            name = SEARCH.search(update.message.text, update.message.chat_id)
            with open(f'tracks/{update.message.chat_id}.mp3', 'rb') as r:
                update.message.reply_text(name)
                update.message.reply_voice(r)



def start(update, context):
    if context.args:
        if "playlist_user_id" in context.args[0]:
            spisok = SONGLIST.open_deep_link(context.args[0])
            if spisok:
                update.message.reply_text(spisok, reply_markup=start_markup)
            else:
                update.message.reply_text("Такого пользователя нет", reply_markup=start_markup)

    else:
        update.message.reply_text("Это Музыкальный бот. Напишите название песни", reply_markup=start_markup)


def main():
    updater = Updater(TOKEN, use_context=True)

    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("add_song", add_song))
    dp.add_handler(CommandHandler("print_songs", print_song_list))

    dp.add_handler(MessageHandler(Filters.text, echo))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
