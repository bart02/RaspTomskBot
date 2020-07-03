import datetime  # for block bot at night
from time import time  # for block update (1 minute) in timestamp

import logging

# python telegram bot's imports
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
from telegram.ext.dispatcher import run_async

import api
from db import DB


# INITIALIZE
# initialize the logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# CONST
TZ = datetime.timezone(datetime.timedelta(hours=7))  # timezone +7

s = api.session()
db = DB('db.json')

@run_async
def help(bot, update):
    update.message.reply_text("Для поиска остановки наберите /bus <название остановки>.", parse_mode="Markdown")


@run_async
def start(bot, update):
    update.message.reply_text("Приветствуем вас, для поиска остановки наберите /bus <название остановки>.",
                              parse_mode="Markdown")


@run_async
def bus(bot, update, args):
    if datetime.datetime.now(TZ).time() > datetime.time(23, 00) or datetime.datetime.now(TZ).time() < datetime.time(6, 00):
        update.message.reply_text("К сожалению, общественный транспорт сейчас не ходит.\n"
                                  "Время движения транспорта в Томске *с 6:00 до 22:30*.",
                                  parse_mode="Markdown")
        taxi_ad(update)
        return

    if not args:
        update.message.reply_text("Для поиска остановки наберите /bus <название остановки>.",
                                  parse_mode="Markdown")
        return
    args = ' '.join(args)

    if len(args) < 3:
        update.message.reply_text("Введите больше 3-ех бкув.",
                                  parse_mode="Markdown")
        return

    liststop, buttons = find_stop(args)

    if liststop:
        reply_markup = InlineKeyboardMarkup(buttons)
        update.message.reply_text('Возможно вы имели ввиду:\n' + liststop + "\nВыберите правильную остановку.",
                                  reply_markup=reply_markup, parse_mode="Markdown")
    else:
        update.message.reply_text("Остановок с таким именем не найдено.",
                                  parse_mode="Markdown")


@run_async
def button(bot, update):
    info = update.callback_query
    if update.callback_query.data in db.db:
        query = db.db[info.data]
        if time() - query['time'] > 60:
            text = 'Остановка `{}`\n\n'.format(query['name'])
            bus = s.get_stops_arrivals(query['ids'])
            # print(bus)
            for num, desc in bus.items():
                text += 'Автобус: *{}*{} следующий на `{}`\n'.format(num[0], num[1], desc['to'])
                for bus in desc['units']:
                    text += '{} {}\n'.format(bus['time'], '♿' if bus['inv'] else '')
                text += '\n'

            query['time'] = time()

            reply_markup = InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔄 Обновить", callback_data=db.append(query) )]])
            bot.edit_message_text(text=text,
                                  reply_markup=reply_markup,
                                  chat_id=info.message.chat_id,
                                  message_id=info.message.message_id,
                                  parse_mode="Markdown")

            db.delete(info.data)
        else:
            bot.answer_callback_query(update.callback_query.id, text='Обновление возможно не чаще ондого раза в минуту')
    else:
        info.message.edit_reply_markup()
        bot.answer_callback_query(info.id, text='Ошибка! Выполните поиск заново.')


def find_stop(search):
    buttons = []  # list for all buttons
    liststop = ""
    buttonstr = []  # list for one str of buttons
    buttons_q = 0
    stops = s.search_stop(search)
    for stop in stops:
        buttons_q += 1
        liststop += '{}. `{}`\n'.format(buttons_q, stop['st_title'])
        buttonstr.append(InlineKeyboardButton(str(buttons_q) + ". ", callback_data=db.append({'ids': stop['st_id'], 'name': 'Новосибирская', 'time': 0})))
        if buttons_q % 7 == 0:
            buttons.append(buttonstr)
            buttonstr = []
    if buttonstr:
        buttons.append(buttonstr)
    return liststop, buttons


def taxi_ad(update):
    update.message.reply_text("Но вы можете воспользоваться такси.\n\n"
                              "Используйте промо-код Gett `GTYURJM` и получайте в подарок до 1500 рублей на первые 10 поездок с лучшими водителями!\n"
                              "Чтобы воспользоваться подарком, необходимо установить приложение по ссылке: https://goo.gl/NhhgvF и ввести этот промо-код после установки.\n"
                              "Для использования промо-кода необходимо привязать банковскую карту к приложению.",
                              parse_mode="Markdown")


def error(bot, update, error):
    logging.warning('Update "%s" caused error "%s"' % (update, error))


updater = Updater("403179008:AAFONypWB4lrOeL7ciuFmQwf1cQ1NIsdXis")

updater.dispatcher.add_handler(CommandHandler('start', start))
updater.dispatcher.add_handler(CommandHandler('help', help))
updater.dispatcher.add_handler(CommandHandler('bus', bus, pass_args=True))
updater.dispatcher.add_handler(CallbackQueryHandler(button))

updater.dispatcher.add_error_handler(error)

updater.start_polling()
