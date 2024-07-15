import json
import requests
import telebot
from datetime import datetime, timedelta
import time
from telebot import types
import os
from threading import Thread

# Your API Key for Dextools API
API_KEY = ""
# Your Telegram bot token
TELEGRAM_BOT_TOKEN = ""

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# File names for storing data
DATA_FILE_ETH = 'data_eth.json'
DATA_FILE_SOL = 'data_sol.json'
CHAT_IDS_FILE_ETH = 'chat_ids_eth.json'
CHAT_IDS_FILE_SOL = 'chat_ids_sol.json'


def load_data(filename):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    return {}


def save_data(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)


# Load chat IDs and token data for both blockchains
chat_ids_eth = load_data(CHAT_IDS_FILE_ETH).get("chat_ids", [])
chat_ids_sol = load_data(CHAT_IDS_FILE_SOL).get("chat_ids", [])
token_data_eth = load_data(DATA_FILE_ETH).get("tokens", [])
token_data_sol = load_data(DATA_FILE_SOL).get("tokens", [])


@bot.message_handler(commands=['start'])
def send_welcome(message):
    # Reply keyboard markup
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton('/addeth')
    item2 = types.KeyboardButton('/addsol')
    item3 = types.KeyboardButton('/removeeth')
    item4 = types.KeyboardButton('/removesol')
    markup.add(item1, item2)
    markup.add(item3, item4)

    # Inline keyboard markup for the button under the message
    inline_markup = types.InlineKeyboardMarkup(row_width=1)
    btn = types.InlineKeyboardButton('Contact @Rage1998',
                                     url='https://t.me/Rage1998')
    inline_markup.add(btn)

    # Reply to the user with the welcome message and both markups
    bot.reply_to(message, "Welcome to TradeInAi Dex Bot!\n\n"
                 "Use the following commands to manage your subscriptions:\n"
                 "/addeth - Subscribe to Ethereum token notifications\n"
                 "/removeeth - Unsubscribe from Ethereum token notifications\n"
                 "/addsol - Subscribe to Solana token notifications\n"
                 "/removesol - Unsubscribe from Solana token notifications\n\n"
                 "Powered by @Tradeinai",
                 reply_markup=markup)

    # Send the inline keyboard button below the message
    bot.send_message(message.chat.id,
                     "For advertising inquiries, click below:",
                     reply_markup=inline_markup)


@bot.message_handler(commands=['addeth'])
def add_chat_id_eth(message):
    chat_id = message.chat.id
    if chat_id not in chat_ids_eth:
        chat_ids_eth.append(chat_id)
        save_data(CHAT_IDS_FILE_ETH, {"chat_ids": chat_ids_eth})
        bot.reply_to(message,
                     "You have been added to the Ethereum notification list.")
    else:
        bot.reply_to(message,
                     "You are already in the Ethereum notification list.")


@bot.message_handler(commands=['addsol'])
def add_chat_id_sol(message):
    chat_id = message.chat.id
    if chat_id not in chat_ids_sol:
        chat_ids_sol.append(chat_id)
        save_data(CHAT_IDS_FILE_SOL, {"chat_ids": chat_ids_sol})
        bot.reply_to(message,
                     "You have been added to the Solana notification list.")
    else:
        bot.reply_to(message,
                     "You are already in the Solana notification list.")


@bot.message_handler(commands=['removeeth'])
def remove_chat_id_eth(message):
    chat_id = message.chat.id
    if chat_id in chat_ids_eth:
        chat_ids_eth.remove(chat_id)
        save_data(CHAT_IDS_FILE_ETH, {"chat_ids": chat_ids_eth})
        bot.reply_to(
            message,
            "You have been removed from the Ethereum notification list.")
    else:
        bot.reply_to(message, "You are not in the Ethereum notification list.")


@bot.message_handler(commands=['removesol'])
def remove_chat_id_sol(message):
    chat_id = message.chat.id
    if chat_id in chat_ids_sol:
        chat_ids_sol.remove(chat_id)
        save_data(CHAT_IDS_FILE_SOL, {"chat_ids": chat_ids_sol})
        bot.reply_to(
            message,
            "You have been removed from the Solana notification list.")
    else:
        bot.reply_to(message, "You are not in the Solana notification list.")


def fetch_token_data(blockchain):
    today = datetime.utcnow()
    yesterday = today - timedelta(days=1)

    today_str = today.strftime('%Y-%m-%dT%H:%M:%S.000Z')
    yesterday_str = yesterday.strftime('%Y-%m-%dT%H:%M:%S.000Z')

    url = f'https://public-api.dextools.io/trial/v2/token/{blockchain}?sort=socialsInfoUpdated&order=desc&from={yesterday_str}&to={today_str}&page=0&pageSize=5'

    response = requests.get(url,
                            headers={
                                'accept': 'application/json',
                                'X-API-Key': API_KEY
                            })
    return response.json().get('data')


def check_for_new_tokens_eth():
    global token_data_eth
    new_data = fetch_token_data('ether')

    if new_data:
        new_tokens = new_data.get('tokens', [])
        new_token_addresses = {token['address'] for token in new_tokens}
        old_token_addresses = {token['address'] for token in token_data_eth}

        added_tokens = [
            token for token in new_tokens
            if token['address'] not in old_token_addresses
        ]

        if added_tokens:
            for token in added_tokens:
                social_info = token.get('socialInfo', {})
                available_social_info = {
                    key: value
                    for key, value in social_info.items() if value
                }

                token_info = (
                    "⛓️ <b>Chain </b>: Ether\n"
                    f"📍 <b>Token Address:</b> <a href='https://www.dextools.io/app/en/ether/pair-explorer/{token['address']}?q=token'>{token['address']}</a>\n"
                    f"📝 <b>Name:</b> {token['name']}\n"
                    f"🔣 <b>Symbol:</b> {token['symbol']}\n"
                    f"📖 <b>Description:</b> {token['description']}\n\n"
                    "<b>🌐 Social Info:</b>\n")

                for key, value in available_social_info.items():
                    token_info += f"  {key.capitalize()}: {value}\n"

                audit_response = requests.get(
                    f'https://public-api.dextools.io/trial/v2/token/ether/{token["address"]}/audit',
                    headers={
                        'accept': 'application/json',
                        'X-API-Key': API_KEY
                    })

                if audit_response.status_code == 200:
                    audit_data = audit_response.json().get('data')
                    if audit_data:
                        audit_info = (
                            "\n<b>🔍 Token Audit Data 🔍</b>\n"
                            f"<b>🛠️ Open Source:</b> {get_emoji(audit_data.get('isOpenSource', 'unknown'))}   |   "
                            f"<b>🍯 Honeypot:</b> {get_emoji(audit_data.get('isHoneypot', 'unknown'))}\n"
                            f"<b>🪙 Mintable:</b> {get_emoji(audit_data.get('isMintable', 'unknown'))}   |   "
                            f"<b>🧩 Proxy:</b> {get_emoji(audit_data.get('isProxy', 'unknown'))}\n"
                            f"<b>⚙️ Slippage Modifiable:</b> {get_emoji(audit_data.get('slippageModifiable', 'unknown'))}   |   "
                            f"<b>🚫 Blacklisted:</b> {get_emoji(audit_data.get('isBlacklisted', 'unknown'))}\n\n"
                            f"<b>📉 Sell Tax:</b> Min: {audit_data.get('sellTax', {}).get('min', 'no data')} Max: {audit_data.get('sellTax', {}).get('max', 'no data')} Status: {get_emoji(audit_data.get('sellTax', {}).get('status', 'unknown'))}   |   "
                            f"<b>📈 Buy Tax:</b> Min: {audit_data.get('buyTax', {}).get('min', 'no data')} Max: {audit_data.get('buyTax', {}).get('max', 'no data')} Status: {get_emoji(audit_data.get('buyTax', {}).get('status', 'unknown'))}\n"
                            f"\n<b>🔒 Contract Renounced:</b> {get_emoji(audit_data.get('isContractRenounced', 'unknown'))}   |   "
                            f"<b>⚠️ Potentially Scam:</b> {get_emoji(audit_data.get('isPotentiallyScam', 'unknown'))}\n"
                            f"<a href='https://dexscreener.com/token/{token['address']}'>DexScreener</a> | "
                            f"<a href='https://etherscan.io/address/{token['address']}'> Etherscan</a>"
                            f"\n\nPowered by @Tradeinai")

                        token_info += audit_info

                for chat_id in chat_ids_eth:
                    markup = types.InlineKeyboardMarkup(row_width=3)
                    btn = types.InlineKeyboardButton('For ads contact @Rage1998',
                                                     url='https://t.me/Rage1998')
                    markup.add(btn)
                    bot.send_message(chat_id, token_info, parse_mode='HTML',reply_markup=markup)

            token_data_eth = new_tokens
            save_data(DATA_FILE_ETH, {"tokens": token_data_eth})


def check_for_new_tokens_sol():
    global token_data_sol
    new_data = fetch_token_data('solana')

    if new_data:
        new_tokens = new_data.get('tokens', [])
        new_token_addresses = {token['address'] for token in new_tokens}
        old_token_addresses = {token['address'] for token in token_data_sol}

        added_tokens = [
            token for token in new_tokens
            if token['address'] not in old_token_addresses
        ]

        if added_tokens:
            for token in added_tokens:
                social_info = token.get('socialInfo', {})
                available_social_info = {
                    key: value
                    for key, value in social_info.items() if value
                }

                token_info = (
                    f"⛓️ <b>Chain </b>: Solana\n"
                    f"📍 <b>Token Address:</b> <a href='https://www.dextools.io/app/en/solana/pair-explorer/{token['address']}?q=token'>{token['address']}</a>\n"
                    f"📝 <b>Name:</b> {token['name']}\n"
                    f"🔣 <b>Symbol:</b> {token['symbol']}\n"
                    f"📖 <b>Description:</b> {token['description']}\n\n"
                    "<b>🌐 Social Info:</b>\n")

                for key, value in available_social_info.items():
                    token_info += f"  {key.capitalize()}: {value}\n"

                audit_response = requests.get(
                    f'https://public-api.dextools.io/trial/v2/token/solana/{token["address"]}/audit',
                    headers={
                        'accept': 'application/json',
                        'X-API-Key': API_KEY
                    })

                if audit_response.status_code == 200:
                    audit_data = audit_response.json().get('data')
                    if audit_data:
                        audit_info = (
                            "\n<b>🔍 Token Audit Data 🔍</b>\n"
                            f"<b>🛠️ Open Source:</b> {get_emoji(audit_data.get('isOpenSource', 'unknown'))}   |   "
                            f"<b>🍯 Honeypot:</b> {get_emoji(audit_data.get('isHoneypot', 'unknown'))}\n"
                            f"<b>🪙 Mintable:</b> {get_emoji(audit_data.get('isMintable', 'unknown'))}   |   "
                            f"<b>🧩 Proxy:</b> {get_emoji(audit_data.get('isProxy', 'unknown'))}\n"
                            f"<b>⚙️ Slippage Modifiable:</b> {get_emoji(audit_data.get('slippageModifiable', 'unknown'))}   |   "
                            f"<b>🚫 Blacklisted:</b> {get_emoji(audit_data.get('isBlacklisted', 'unknown'))}\n\n"
                            f"<b>📉 Sell Tax:</b> Min: {audit_data.get('sellTax', {}).get('min', 'no data')} Max: {audit_data.get('sellTax', {}).get('max', 'no data')} Status: {get_emoji(audit_data.get('sellTax', {}).get('status', 'unknown'))}   |   "
                            f"<b>📈 Buy Tax:</b> Min: {audit_data.get('buyTax', {}).get('min', 'no data')} Max: {audit_data.get('buyTax', {}).get('max', 'no data')} Status: {get_emoji(audit_data.get('buyTax', {}).get('status', 'unknown'))}\n"
                            f"\n<b>🔒 Contract Renounced:</b> {get_emoji(audit_data.get('isContractRenounced', 'unknown'))}   |   "
                            f"<b>⚠️ Potentially Scam:</b> {get_emoji(audit_data.get('isPotentiallyScam', 'unknown'))}\n\n"
                            f"<a href='https://dexscreener.com/solana/{token['address']}'>DexScreener</a> | <a href='https://birdeye.so/token/{token['address']}?chain=solana&tab=recentTrades'>BirdEye</a> |"
                            f"<a href='https://solscan.io/account/{token['address']}'> SolScan</a>"
                            f"\n\nPowered by @Tradeinai")
                        token_info += audit_info

                for chat_id in chat_ids_sol:
                    markup = types.InlineKeyboardMarkup(row_width=3)
                    btn = types.InlineKeyboardButton('For ads contact @Rage1998',
                                                     url='https://t.me/Rage1998')
                    markup.add(btn)
                    bot.send_message(chat_id, token_info, parse_mode='HTML',reply_markup=markup)

            token_data_sol = new_tokens
            save_data(DATA_FILE_SOL, {"tokens": token_data_sol})


def get_emoji(value):
    if value == "yes":
        return "✔️"
    elif value == "no":
        return "❌"
    else:
        return value


def run_bot():
    while True:
        check_for_new_tokens_eth()
        check_for_new_tokens_sol()
        time.sleep(300)  # Check every 5 minutes


send_messages_thread = Thread(target=run_bot)
send_messages_thread.daemon = True
send_messages_thread.start()
bot.infinity_polling()
