#%%
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    CallbackContext,
    Filters,
)
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)


import logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

import datetime
from collections import defaultdict


class KookLijst(object):
    def __init__(self, chef = None):
        self.chef = chef
        self.guests = {}


class Database(object):
    def __init__(self):
        self._date = datetime.date.today()    
        self._kldata = defaultdict(KookLijst)
    
    def _check_date(self, date):
        if date != self._date:
            self._date = date
            self._kldata = defaultdict(KookLijst)

    def _check_group(self, chat, update):
        if hasattr(chat, "type") and chat.type == "group": 
            return False
        else:
            update.message.reply_text("Voeg me toe aan een groep!")
            return True

    def add_chef(self, date, chat_id, user):
        self._check_date(date)
        self._kldata[chat_id].chef = user

    def add_guest(self, date, chat_id, user, guests=0):
        self._check_date(date)
        self._kldata[chat_id].guests[user.id] = user
        user.guests = guests

    def kook(self, update: Update, context: CallbackContext) -> None:

        if self._check_group(update.effective_chat, update):
            return

        date = update.effective_message.date.date()
        chat_id = update.effective_chat.id
        user = update.effective_user
        self.add_chef(date, chat_id, user)
        self.add_guest(date, chat_id, user)

        reply_markup = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("mee", callback_data='1'),
                InlineKeyboardButton("mee +1", callback_data='2'),
                InlineKeyboardButton("mee +2", callback_data='3'),
            ],
            [InlineKeyboardButton("niet mee", callback_data='0')],
        ])
        update.message.reply_text('Ik eet', reply_markup=reply_markup)


    def button(self, update: Update, context: CallbackContext) -> None:
        query = update.callback_query
        query.answer()

        chat_id = query.message.chat_id
        date = query.message.date.date()
        user = query.from_user

        if query.data == "0":
            self._kldata[chat_id].guests.pop(user.id, None)
        elif query.data == "1":
            self.add_guest(date, chat_id, user, 0)
        elif query.data == "2":
            self.add_guest(date, chat_id, user, 1)
        elif query.data == "3":
            self.add_guest(date, chat_id, user, 2)


    def eet(self, update: Update, context: CallbackContext) -> None:
        if self._check_group(update.effective_chat, update):
            return
        date = update.effective_message.date.date()
        self.add_guest(date, update.effective_chat.id, update.effective_user)

    def eetplus(self, update: Update, context: CallbackContext) -> None:
        if self._check_group(update.effective_chat, update):
            return
        date = update.effective_message.date.date()
        self.add_guest(date, update.effective_chat.id, update.effective_user, int(context.args[0]))
    
    def eetniet(self, update: Update, context: CallbackContext) -> None:
        if self._check_group(update.effective_chat, update):
            return
        self._kldata[update.effective_chat.id].guests.pop(update.effective_user.id, None)

    def wie(self, update: Update, context: CallbackContext, attribute="first_name") -> None:
        if self._check_group(update.effective_chat, update):
            return
        self._check_date(datetime.date.today())
        chat_id = update.effective_chat.id
        chef = self._kldata[chat_id].chef
        chefname = getattr(chef, attribute) if chef is not None else "Niemand"

        guests, names = 0, []
        for key, user in self._kldata[chat_id].guests.items():
            names.append(getattr(user, attribute))
            guests += getattr(user, "guests", 0)

        message = f"{chefname} kookt,\n" + ", ".join(names) + f" en {guests} gasten eten mee."
        update.message.reply_text(message)

    def wielang(self, update: Update, context: CallbackContext) -> None:
        self.wie(update, context, "full_name")

    def hoeveel(self, update: Update, context: CallbackContext) -> None:
        if self._check_group(update.effective_chat, update):
            return
        self._check_date(datetime.date.today())
        chat_id = update.effective_chat.id
        guests = 0
        for key, user in self._kldata[chat_id].guests.items():
            guests += 1 + getattr(user, "guests", 0)
        message = f"{guests} mensen eten mee."
        update.message.reply_text(message)

    def reset(self, update: Update, context: CallbackContext) -> None:
        if self._check_group(update.effective_chat, update):
            return
        self._check_date(datetime.date.today())
        chat_id = update.effective_chat.id
        self._kldata.pop(chat_id, None)
        update.message.reply_text("Eetlijst gewist")

    def start(self, update: Update, context: CallbackContext) -> None:
        message = "Hallo, dit is een bot voor het bijhouden van een eetlijst. Na 24 uur worden alle eetlijsten uit de database verwijderd. Voeg me toe aan een groep om van me gebruik te maken. Zie /help voor een lijst van commando's."
        update.message.reply_text(message)

    def help(self, update: Update, context: CallbackContext) -> None:
        message = "/kook als je kookt\n/eet als je mee-eet\n/eetplus het aantal gasten\n/eetniet als je niet mee-eet\n/wie lijst met mee-eters\n/wielang hele namen van mee-eters\n/hoeveel aantal mee-eters\n/reset wis eetlijst"
        update.message.reply_text(message)


def unknown(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")

def main():

    with open("./api-token", 'r') as f:
        token = f.read()

    updater = Updater(token=token, use_context=True)
    dispatcher = updater.dispatcher

    database = Database()

    dispatcher.add_handler(CommandHandler('start', database.start))
    dispatcher.add_handler(CommandHandler('kook', database.kook))
    dispatcher.add_handler(CommandHandler('eet', database.eet))
    dispatcher.add_handler(CommandHandler('eetplus', database.eetplus))
    dispatcher.add_handler(CommandHandler('eetniet', database.eetniet))
    dispatcher.add_handler(CommandHandler('wie', database.wie))
    dispatcher.add_handler(CommandHandler('wielang', database.wielang))
    dispatcher.add_handler(CommandHandler('hoeveel', database.hoeveel))
    dispatcher.add_handler(CommandHandler('reset', database.reset))
    dispatcher.add_handler(CommandHandler('help', database.help))
    dispatcher.add_handler(CallbackQueryHandler(database.button))
    dispatcher.add_handler(MessageHandler(Filters.command, unknown))


    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()