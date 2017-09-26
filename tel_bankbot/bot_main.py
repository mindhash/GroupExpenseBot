"""
Bank Bot Main .
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""
from telegram import Emoji, ForceReply, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, filters
from wit import Wit
from bankwit import Parse

import logging
import data_store

# Enable logging
logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO)

logger = logging.getLogger(__name__)

json_dict = {
            'force_reply': True,
            'selective': True,
        }

# Define the different states a chat can be in
MENU, AWAIT_PAID_INPUT, AWAIT_RECVD_INPUT, AWAIT_MEMBER_INPUT, AWAIT_CONFIRMATION, AWAIT_INPUT = range(6)

# States are saved in a dict that maps chat_id -> state
state = dict()

# Sometimes you need to save data temporarily
context = dict()




# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.
def start(bot, update):
    bot.sendMessage(update.message.chat_id, text='Hi!')

def help(bot, update):
    bot.sendMessage(update.message.chat_id, text='Help!')

def process_input(bot, update):
     #bot.sendMessage(update.message.chat_id, text=update.message.text)
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    user_name = "@" + update.message.from_user.first_name
    chat_state = state.get(user_id, MENU)
    #logger.info("Chat state %s", chat_state)

     # Check if we are waiting for input
    if chat_state == AWAIT_MEMBER_INPUT:
      context[user_id] = update.message.text
      # call member addition
      bot.sendMessage(chat_id, text="Member(s) added: %s" % context[user_id])

    if chat_state == AWAIT_PAID_INPUT:
      context[user_id] = update.message.text
      # call member addition
      input_data = Parse(update.message.text)
      logger.info("input data  %s", input_data)
      logger.info("chat_id  %s", chat_id)

      txn_type = "exp"
      participants = []

      if "amount" in input_data:
        amount = input_data["amount"]

      if "participants" in input_data:
        member_list  = input_data["participants"]
        if member_list:
          participants = filter(None,member_list.split(" "))

      if amount:
        data_store.update(str(chat_id), user_name,amount , txn_type ,participants)

        msg = "Noted: $"+ str(amount) + " " + txn_type
        if participants:
          msg += "\nParticipants: "
          for p in participants:
            msg += p + " "
        bot.sendMessage(chat_id, text=msg)
      else:
        bot.sendMessage(chat_id, text="Sorry. I could not understand input")

    if chat_state == AWAIT_RECVD_INPUT:
      context[user_id] = update.message.text
      # call member addition
      bot.sendMessage(chat_id, text="Noted: %s" % context[user_id])

def add_cmd(bot, update):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    user_state = state.get(chat_id, MENU)
    if user_state == MENU:
      state[user_id] = AWAIT_MEMBER_INPUT  # set the state
      bot.sendMessage(chat_id=chat_id, text="Enter the user or member name(s). e.g. @poko @doko @noko", reply_to_message_id=update.message.message_id,reply_markup=ForceReply.de_json(json_dict))

def paid_cmd(bot, update):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    message_id = update.message.message_id
    user_state = state.get(chat_id, MENU)

    if user_state == MENU:
      state[user_id] = AWAIT_PAID_INPUT  # set the state
      bot.sendMessage(chat_id=chat_id, text="Alright. What did you pay for? How much? Tag members, share comments as necessary. e.g.- Paid $34 for lunch @poko @doko ", reply_to_message_id=message_id,reply_markup=ForceReply.de_json(json_dict))

def recvd_cmd(bot, update):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    message_id = update.message.message_id
    user_state = state.get(chat_id, MENU)

    if user_state == MENU:
      state[user_id] = AWAIT_RECVD_INPUT  # set the state
      bot.sendMessage(chat_id=chat_id, text="Please share more details. Tag members as necessary. e.g.- $34 from @poko @doko ", reply_to_message_id=message_id,reply_markup=ForceReply.de_json(json_dict))

def balance_cmd(bot,update):
    chat_id = update.message.chat_id
    logger.info("chat_id  %s", chat_id)
    user_state = state.get(chat_id, MENU)
    if user_state == MENU:
      s= data_store.chat_summary(str(chat_id))

    if s:
      bot.sendMessage(chat_id=chat_id, text=s)
    else:
      bot.sendMessage(chat_id=chat_id, text="No records yet")

def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))

def main():
    # Create the EventHandler and pass it your bot's token.
    updater = Updater("83699434:AAEUZyUyK2S3a2BsMDzFLFr44N8ZDyRZ2mA")

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.addHandler(CommandHandler("start", start))
    dp.addHandler(CommandHandler("help", help))
    #dp.addHandler(CommandHandler("add", add_cmd))
    #dp.addHandler(CommandHandler("remove", removecmd))
    dp.addHandler(CommandHandler("paid", paid_cmd))
    #dp.addHandler(CommandHandler("recvd", recvd_cmd))
    dp.addHandler(CommandHandler("balance", balance_cmd))

    # on noncommand i.e message - echo the message on Telegram
    dp.addHandler(MessageHandler([filters.TEXT], process_input))

    # log all errors
    dp.addErrorHandler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until the you presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()

if __name__ == '__main__':
    main()
