from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
from dotenv import load_dotenv
import os

from wallet import generate_wallets, get_eth_balance, get_btc_balance, send_eth
from db import get_user, add_user, get_all_users
from price import get_price
from orders import create_order, get_open_orders, get_order, update_order_status
from escrow import create_escrow, get_escrows
from utils import format_order, format_escrow

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
INFURA_URL = os.getenv("INFURA_URL")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
ADMIN_IDS = [7879117281]

user_state = {}

def is_admin(user_id):
    return user_id in ADMIN_IDS

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def admin_panel(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        if update.message:
            update.message.reply_text("Unauthorized user.")
        else:
            update.callback_query.edit_message_text("Unauthorized user.")
        return

    keyboard = [
        [InlineKeyboardButton("View Users", callback_data='admin_users')],
        [InlineKeyboardButton("View Orders", callback_data='admin_orders')],
        [InlineKeyboardButton("View Escrows", callback_data='admin_escrows')],
        [InlineKeyboardButton("View Balances", callback_data='admin_balances')],
        [InlineKeyboardButton("Cancel Order", callback_data='admin_cancel')],
    ]
    markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        update.message.reply_text("Admin Panel:\nChoose an option:", reply_markup=markup)
    elif update.callback_query:
        update.callback_query.edit_message_text("Admin Panel:\nChoose an option:", reply_markup=markup)

def main_menu(update, context, message=None):
    keyboard = [
        [InlineKeyboardButton("Wallets", callback_data='menu_wallets')],
        [InlineKeyboardButton("Orders", callback_data='menu_orders')],
        [InlineKeyboardButton("Tools", callback_data='menu_tools')],
    ]
    markup = InlineKeyboardMarkup(keyboard)
    welcome_text = " *Welcome to Crypto Trading Bot*\n\nSelect an option below:"
    
    if message:
        message.edit_text(welcome_text, reply_markup=markup, parse_mode="Markdown")
    else:
        update.message.reply_text(welcome_text, reply_markup=markup, parse_mode="Markdown")

# /start command
def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    username = update.effective_user.username or "User"
    
    if not get_user(user_id):
        mnemonic, btc, eth = generate_wallets()
        add_user(user_id, mnemonic, btc, eth)
        welcome_msg = f" Welcome @{username}!\n\nYour wallets have been created automatically."
        update.message.reply_text(welcome_msg)
    
    main_menu(update, context)

# Button callbacks
def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    query.answer()
    data = query.data

    if data == 'menu_wallets':
        keyboard = [
            [InlineKeyboardButton(" View Wallets", callback_data='wallets')],
            [InlineKeyboardButton(" Check Balances", callback_data='balances')],
            [InlineKeyboardButton(" Deposit Info", callback_data='deposit')],
            [InlineKeyboardButton(" Back to Main", callback_data='back_main')],
        ]
        query.edit_message_text(" *Wallet Management*\n\nChoose an option:", 
                               reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == 'menu_orders':
        keyboard = [
            [InlineKeyboardButton(" Create Sell Order", callback_data='sell')],
            [InlineKeyboardButton(" Browse Buy Orders", callback_data='buy')],
            [InlineKeyboardButton(" My Orders", callback_data='my_orders')],
            [InlineKeyboardButton(" Back to Main", callback_data='back_main')],
        ]
        query.edit_message_text(" *Order Management*\n\nWhat would you like to do?", 
                               reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == 'menu_tools':
        keyboard = [
            [InlineKeyboardButton(" Current Prices", callback_data='price')],
            [InlineKeyboardButton(" Active Escrows", callback_data='escrows')],
            [InlineKeyboardButton(" Withdraw Funds", callback_data='withdraw')],
            [InlineKeyboardButton(" Back to Main", callback_data='back_main')],
        ]
        query.edit_message_text(" *Trading Tools*\n\nSelect a tool:", 
                               reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == 'back_main':
        main_menu(update, context, query.message)

    elif data == 'wallets':
        user = get_user(user_id)
        if user:
            _, _, btc, eth = user
            keyboard = [[InlineKeyboardButton(" Back", callback_data='menu_wallets')]]
            wallet_text = f" *Your Wallet Addresses*\n\n **BTC:** `{btc}`\n\n **ETH:** `{eth}`"
            query.edit_message_text(wallet_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        else:
            query.edit_message_text("❌ Wallet not found. Use /start to create one.")

    elif data == 'balances':
        user = get_user(user_id)
        if user:
            _, _, btc_addr, eth_addr = user
            try:
                btc_balance = get_btc_balance(btc_addr)
                eth_balance = get_eth_balance(eth_addr, INFURA_URL)
                
                keyboard = [[InlineKeyboardButton(" Refresh", callback_data='balances')],
                           [InlineKeyboardButton(" Back", callback_data='menu_wallets')]]
                
                balance_text = f" *Your Balances*\n\n **BTC:** {btc_balance:.8f}\n **ETH:** {eth_balance:.6f}"
                query.edit_message_text(balance_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
            except Exception as e:
                keyboard = [[InlineKeyboardButton(" Try Again", callback_data='balances')],
                           [InlineKeyboardButton(" Back", callback_data='menu_wallets')]]
                query.edit_message_text("❌ Error fetching balances. Please try again.", 
                                       reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            query.edit_message_text("❌ Wallet not found.")

    elif data == 'deposit':
        user = get_user(user_id)
        if user:
            _, _, btc, eth = user
            keyboard = [[InlineKeyboardButton(" Back", callback_data='menu_wallets')]]
            deposit_text = f" *Deposit Instructions*\n\nSend your crypto to these addresses:\n\n **BTC Address:**\n`{btc}`\n\n **ETH Address:**\n`{eth}`\n\n⚠️ *Only send the respective coins to their addresses!*"
            query.edit_message_text(deposit_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        else:
            query.edit_message_text("❌ Wallet not found.")

    elif data == 'sell':
        user_state[user_id] = {'action': 'sell_coin'}
        keyboard = [[InlineKeyboardButton(" Back", callback_data='menu_orders')]]
        query.edit_message_text(" *Create Sell Order*\n\nEnter the coin symbol (e.g., eth, btc):", 
                               reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == 'buy':
        orders = get_open_orders("eth")
        if orders:
            keyboard = [
                [InlineKeyboardButton(f"{o[4]} {o[3].upper()} @ ${o[5]:.2f}", callback_data=f'buyorder_{o[0]}')]
                for o in orders[:10]  # Limit to 10 orders
            ]
            keyboard.append([InlineKeyboardButton(" Back", callback_data='menu_orders')])
            markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text(" *Available ETH Orders*\n\nClick to purchase:", reply_markup=markup)
        else:
            keyboard = [[InlineKeyboardButton(" Refresh", callback_data='buy')],
                       [InlineKeyboardButton(" Back", callback_data='menu_orders')]]
            query.edit_message_text(" No ETH orders available right now.", 
                                   reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == 'my_orders':
        # This would need to be implemented in your orders module
        keyboard = [[InlineKeyboardButton(" Back", callback_data='menu_orders')]]
        query.edit_message_text(" *My Orders*\n\nFeature coming soon!", 
                               reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == 'price':
        try:
            eth_price = get_price("eth")
            btc_price = get_price("btc") if hasattr(get_price, '__call__') else "N/A"
            keyboard = [[InlineKeyboardButton(" Refresh", callback_data='price')],
                       [InlineKeyboardButton(" Back", callback_data='menu_tools')]]
            
            price_text = f" *Current Prices*\n\n **ETH:** ${eth_price:.2f}\n **BTC:** ${btc_price if btc_price != 'N/A' else 'N/A'}"
            query.edit_message_text(price_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        except Exception as e:
            keyboard = [[InlineKeyboardButton(" Try Again", callback_data='price')],
                       [InlineKeyboardButton(" Back", callback_data='menu_tools')]]
            query.edit_message_text("❌ Error fetching prices.", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == 'escrows':
        escrows = get_escrows()
        keyboard = [[InlineKeyboardButton(" Refresh", callback_data='escrows')],
                   [InlineKeyboardButton(" Back", callback_data='menu_tools')]]
        
        if escrows:
            msg = " *Active Escrows*\n\n"
            for i, e in enumerate(escrows[:5], 1):  # Limit to 5 escrows
                msg += f"{i}. {format_escrow(e)}\n"
            query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        else:
            query.edit_message_text(" *Active Escrows*\n\nNo active escrows found.", 
                                   reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == 'withdraw':
        user_state[user_id] = {'action': 'withdraw_address'}
        keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data='menu_tools')]]
        query.edit_message_text(" *Withdraw ETH*\n\nEnter the destination ETH address:", 
                               reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith('buyorder_'):
        order_id = int(data.split('_')[1])
        order = get_order(order_id)
        if order and order[6] == 'open':
            create_escrow(buyer_id=user_id, seller_id=order[1], coin=order[3], amount=order[4])
            update_order_status(order_id, 'escrowed')
            keyboard = [[InlineKeyboardButton(" Back to Orders", callback_data='menu_orders')]]
            query.edit_message_text(f"✅ *Order Purchased!*\n\nEscrow started for order #{order_id}\nYou can track it in the Escrows section.", 
                                   reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        else:
            keyboard = [[InlineKeyboardButton(" Back", callback_data='buy')]]
            query.edit_message_text("❌ Order no longer available.", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == 'admin_users':
        if not is_admin(user_id):
            query.edit_message_text("Unauthorized access.")
            return
        users = get_all_users()
        text = "Registered Users:\n\n"
        for u in users:
            text += f"ID: {u[0]} | BTC: {u[2]} | ETH: {u[3]}\n"
        keyboard = [[InlineKeyboardButton("Back", callback_data='back_admin')]]
        query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == 'admin_orders':
        if not is_admin(user_id):
            query.edit_message_text("Unauthorized access.")
            return
        orders = get_open_orders("eth") + get_open_orders("btc")
        text = "Open Orders:\n\n"
        for o in orders[:10]:
            text += f"ID: {o[0]} | Coin: {o[3]} | Amt: {o[4]} | Price: ${o[5]}\n"
        keyboard = [[InlineKeyboardButton("Back", callback_data='back_admin')]]
        query.edit_message_text(text or "No orders found.", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == 'admin_escrows':
        if not is_admin(user_id):
            query.edit_message_text("Unauthorized access.")
            return
        escrows = get_escrows()
        text = "Active Escrows:\n\n"
        for e in escrows[:5]:
            text += format_escrow(e) + "\n"
        keyboard = [[InlineKeyboardButton("Back", callback_data='back_admin')]]
        query.edit_message_text(text or "No active escrows.", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == 'admin_balances':
        if not is_admin(user_id):
            query.edit_message_text("Unauthorized access.")
            return
        admin_eth = "0x96238A1f030FF4bE6f423A93Ce459D5Dc5615E39"
        admin_btc = "1EEKwXB7yspc7rETfE8QZofDMhPTniAtWH"
        eth_balance = get_eth_balance(admin_eth, INFURA_URL)
        btc_balance = get_btc_balance(admin_btc)
        text = f"Bot Wallet Balances:\n\nETH: {eth_balance} ETH\nBTC: {btc_balance} BTC"
        keyboard = [[InlineKeyboardButton("Back", callback_data='back_admin')]]
        query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == 'admin_cancel':
        if not is_admin(user_id):
            query.edit_message_text("Unauthorized access.")
            return
        orders = get_open_orders("eth") + get_open_orders("btc")
        keyboard = [
            [InlineKeyboardButton(f"Cancel #{o[0]} {o[3].upper()}", callback_data=f'cancel_{o[0]}')]
            for o in orders[:10]
        ]
        keyboard.append([InlineKeyboardButton("Back", callback_data='back_admin')])
        query.edit_message_text("Select order to cancel:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith('cancel_'):
        if not is_admin(user_id):
            query.edit_message_text("Unauthorized access.")
            return
        order_id = int(data.split('_')[1])
        update_order_status(order_id, 'cancelled')
        keyboard = [[InlineKeyboardButton("Back", callback_data='admin_cancel')]]
        query.edit_message_text(f"Order", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == 'back_admin':
        admin_panel(update, context)

def message_handler(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    state = user_state.get(user_id, {})

    if state.get('action') == 'sell_coin':
        coin = text.lower()
        if coin in ['eth', 'btc']:
            state['coin'] = coin
            state['action'] = 'sell_amount'
            update.message.reply_text(f" Enter amount of {coin.upper()} to sell:")
        else:
            update.message.reply_text("❌ Only ETH and BTC are supported. Please enter 'eth' or 'btc':")

    elif state.get('action') == 'sell_amount':
        try:
            amount = float(text)
            if amount > 0:
                state['amount'] = amount
                state['action'] = 'sell_price'
                update.message.reply_text(f" Enter price per {state['coin'].upper()} in USD:")
            else:
                update.message.reply_text("❌ Amount must be greater than 0:")
        except ValueError:
            update.message.reply_text("❌ Invalid amount. Please enter a number:")

    elif state.get('action') == 'sell_price':
        try:
            price = float(text)
            if price > 0:
                state['price'] = price
                create_order(user_id, "sell", state['coin'], state['amount'], state['price'])
                user_state.pop(user_id, None)
                
                summary = f"✅ *Sell Order Created!*\n\n **Details:**\n• Coin: {state['coin'].upper()}\n• Amount: {state['amount']}\n• Price: ${state['price']:.2f}\n• Total: ${state['amount'] * state['price']:.2f}"
                update.message.reply_text(summary, parse_mode="Markdown")
            else:
                update.message.reply_text("❌ Price must be greater than 0:")
        except ValueError:
            update.message.reply_text("❌ Invalid price. Please enter a number:")

    elif state.get('action') == 'withdraw_address':
        if text.startswith('0x') and len(text) == 42:
            state['to'] = text
            state['action'] = 'withdraw_amount'
            update.message.reply_text(" Enter amount to withdraw (in ETH):")
        else:
            update.message.reply_text("❌ Invalid ETH address. Please enter a valid address starting with 0x:")

    elif state.get('action') == 'withdraw_amount':
        try:
            amount = float(text)
            if amount > 0:
                to = state['to']
                tx_hash = send_eth(PRIVATE_KEY, to, amount, INFURA_URL)
                user_state.pop(user_id, None)
                
                success_msg = f"✅ *Withdrawal Successful!*\n\n **Details:**\n• Amount: {amount} ETH\n• To: `{to}`\n• TX Hash: `{tx_hash}`"
                update.message.reply_text(success_msg, parse_mode="Markdown")
            else:
                update.message.reply_text("❌ Amount must be greater than 0:")
        except Exception as e:
            user_state.pop(user_id, None)
            update.message.reply_text(f"❌ *Withdrawal Failed*\n\nError: {str(e)}", parse_mode="Markdown")

    # Clear state if user sends unrelated message
    if not state.get('action'):
        update.message.reply_text(" Use /start to access the main menu!")

# Run the bot
def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button_handler))
    dp.add_handler(CommandHandler("admin", admin_panel))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, message_handler))
    updater.start_polling()
    print("✅ Bot is running!")
    updater.idle()

if __name__ == "__main__":
    main()
