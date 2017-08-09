import re
import logging

import datetime  # for block bot at night
from time import time  # for block update (1 minute) in timestamp

# python telegram bot's imports
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
from telegram.ext.dispatcher import run_async

# for parse the Tablle rasp.tomsk.ru
import requests as r
from bs4 import BeautifulSoup as bs

from stops import stops  # list with the stops


# INITIALIZE
# initialize the logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# CONST
tz = datetime.timezone(datetime.timedelta(hours=7))  # timezone +7


@run_async
def help(bot, update):
    update.message.reply_text("Для поиска остановки наберите /bus <название остановки>.", parse_mode="Markdown")


@run_async
def start(bot, update):
    update.message.reply_text("Приветствуем вас, для поиска остановки наберите /bus <название остановки>.",
                              parse_mode="Markdown")


@run_async
def bus(bot, update, args):
    if datetime.datetime.now(tz).time() > datetime.time(23, 00) or datetime.datetime.now(tz).time() < datetime.time(6, 00):
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

    if liststop == "Не найдено":
        update.message.reply_text("Остановок с таким именем не найдено.",
                                  parse_mode="Markdown")
    else:
        reply_markup = InlineKeyboardMarkup(buttons)
        update.message.reply_text('Возможно вы имели ввиду:\n' + liststop + "\nВыберите правильную остановку.",
                                  reply_markup=reply_markup, parse_mode="Markdown")


@run_async
def button(bot, update):
    query = update.callback_query
    split = re.split(";", query.data)
    if time() - int(split[2]) > 60:
        text = ""
        bus = parse_time(split[0])
        text += 'Остановка: `' + stops[int(split[1])]['value'] + '`\n\n'
        for b in bus:
            text += 'Номер: ' + b + "\n"
            first = True
            for buses in bus[b]:
                if first:
                    text += 'приедет через ' + buses[1] + "\n"
                    first = False
                else:
                    text += 'следующий через ' + buses[1] + "\n"
            text += '\n'

        split[2] = ''
        reply_markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔄 Обновить", callback_data=';'.join(split) + str(int(time())))]])
        bot.edit_message_text(text=text,
                              reply_markup=reply_markup,
                              chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              parse_mode="Markdown")
    else:
        bot.answer_callback_query(update.callback_query.id, text='Обновление возможно не чаще ондого раза в минуту')


def find_stop(search):
    buttons = []  # list for all buttons
    liststop = ""
    buttonstr = []  # list for one str of buttons
    buttons_q = 0
    stopnum = 0
    for stop in stops:
        split = re.split("\(", stop['value'].lower())
        find = re.search(search.lower(), split[0])
        if find is None:
            stopnum += 1
            continue
        else:
            buttons_q += 1
            liststop += str(buttons_q) + ". `" + stop['value'] + "`\n"
            buttonstr.append(InlineKeyboardButton(str(buttons_q) + ". ", callback_data=stop['code'] + ';' + str(stopnum) + ';0'))
            if buttons_q % 7 == 0:
                buttons.append(buttonstr)
                buttonstr = []
        stopnum += 1
    if buttonstr:
        buttons.append(buttonstr)
    if buttons_q == 0:
        liststop = "Не найдено"
    return liststop, buttons


def parse_time(codestop):
    param = {
        '__EVENTVALIDATION': 'gzSSPkf24omwbE4k3zRVvYY+qef1mTyLMerkfhjel5dk1CIy9aOuqw5hsd4soGmKCXnNUN/GKFpXeJgSxmgkW7XokZEkoTzgaVftE9PPxmOOpxzcZ01W44hZPvgSraVNfAFTrN4p1ds+hme5DeS3JOoNchIlddI5w7v13qN28E2VhcSEFbf/5CbSQ7CbeTJ2dZ2LKkTsAXzCxSqj7owrMA==',
        '__VIEWSTATE': '2MXdsfbpxHxrNI46UCoOYltu7lnN6i8AczgENEarISmZ7xO7FfIGTOpq+hK9XlwI1UcKJcOO7Abha+6gzFfowbqewOdXPKo17ILJUFQLE7hcJcMTAVbZpPe6UszKh8palpBqZu1A2Tcn+v3ENWdAYK59VXKB5kv2WjHy+qfVVy5XGemZipUbr6kjn/CTh9zEcVN8+QDFwrVUrwHsR/4kw1QRaTTNY+wHR4yEBQ1J2gVPcqqPix6x7hEUH2QCVLFSGjkFMilmYNU6z7upg4k/XqDbjnRoowmXRU+VyNHQAZ0=',
        'OriginCode': codestop}
    glonass = r.post('http://service.glonass.tomsk.ru/tablo/', param)
    soup = bs(glonass.text, "html.parser")
    tablo = soup.find('table', {'id': 'Tablo'})
    routes = tablo.findAll('tr')[1:]
    buses = []
    bus = {}
    numbus = ""
    for ro in routes:
        i = False
        td = ro.findAll('td')
        for t in td:
            if 'rowspan' in t.attrs or re.match('[АТМ]{1,2}\d+', t.text) is not None:
                if numbus != "":
                    bus.update({numbus: buses})
                    buses = []
                numbus = t.text
            else:
                if not i:
                    stop = t.text
                    i = True
                else:
                    buses.append([stop, t.text])
    bus.update({numbus: buses})
    return bus


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
updater.dispatcher.add_handler(CommandHandler('bus', bus, pass_args=True))
updater.dispatcher.add_handler(CallbackQueryHandler(button))
updater.dispatcher.add_handler(CommandHandler('help', help))
updater.dispatcher.add_error_handler(error)

updater.start_polling()
