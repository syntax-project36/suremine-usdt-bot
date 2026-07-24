# bot.py

import logging
import os
import asyncio
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# Import the keep-alive server
from keep_alive import keep_alive

# Import database functions
from database import (
    init_db,
    get_user,
    register_user,
    get_dashboard_data,
    calculate_uncollected_earnings,
    request_withdrawal,
    collect_profit,
    set_wallet,
    create_order,
    approve_deposit,
    approve_withdrawal_db,
    admin_add_balance,
    get_all_user_ids
)

# Import keyboards
from keyboards import (
    main_menu,
    mining_store_menu,
    single_miner_menu,
    earnings_menu,
    wallet_menu,
    payment_methods_menu
)

# Import config constants
from config import MINERS, WALLETS

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
CHANNEL_ID = os.getenv("CHANNEL_ID", "")

BANNER_IMAGE = "https://images.unsplash.com/photo-1639762681485-074b7f938ba0?auto=format&fit=crop&w=1200&q=80"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ref_id = int(context.args[0]) if context.args and context.args[0].isdigit() and int(context.args[0]) != user.id else None
    
    # Check if user is newly registering
    existing_user = get_user(user.id)
    
    register_user(user.id, user.username or user.first_name, user.first_name, ref_id)

    # Notify the inviter if a brand-new user joined via their link
    if not existing_user and ref_id:
        try:
            await context.bot.send_message(
                chat_id=ref_id,
                text=f"🎉 *New Referral Alert!*\n\nUser `{user.first_name}` joined using your referral link!\n💰 *+25 USDŦ* has been added to your balance.",
                parse_mode="Markdown"
            )
        except Exception:
            pass

    bot_info = await context.bot.get_me()

    text = (
        f"☺️ *SureMine USDŦ BOT* ☺️\n\n"
        f"⚡️ *Automated Hourly Rewards, Instant Payouts 24/7*\n\n"
        f"📢 *Official Channel:* [Join Here](https://t.me/suremineusdtnews)\n\n"
        f"🫟 *Referral invite:* +25 USDŦ\n"
        f"💎 *Premium invite:* +35 USDŦ\n\n"
        f"🟢 *Automatic Payouts to your USDŦ Wallet*\n\n"
        f"🎁 *Share & Earn Referral Bonus* 👇\n"
        f"https://t.me/{bot_info.username}?start={user.id}"
    )

    if update.message:
        await update.message.reply_photo(photo=BANNER_IMAGE, caption=text, parse_mode="Markdown", reply_markup=main_menu())
    elif update.callback_query:
        await update.callback_query.message.reply_photo(photo=BANNER_IMAGE, caption=text, parse_mode="Markdown", reply_markup=main_menu())


async def render_dashboard(user_id, context, target_message=None):
    user, ref_count, miners_count = get_dashboard_data(user_id)
    
    active_str = "⛏ Miner: USDŦ Miner V0\n⚡️ Hashrate: 0 TH/s"
    if miners_count:
        active_str = "⛏️ *ACTIVE MINERS:*\n"
        for m_id, count in miners_count.items():
            if m_id in MINERS:
                m = MINERS[m_id]
                active_str += f"• {m['name']} x{count} ({m['hashrate']})\n"

    text = (
        f"💵 *USDŦ USER DASHBOARD*\n\n"
        f"✅ *Account ID:* `{user['first_name']}`\n"
        f"✅ *Current Balance:* {user['balance']:.2f} USDŦ (~ ${user['balance']:.2f})\n"
        f"✅ *Total Withdrawn:* {user['total_withdrawn']:.2f} USDŦ (~ ${user['total_withdrawn']:.2f})\n"
        f"✅ *Referrals:* {ref_count} Users\n\n"
        f"⛏️ *MINING STATISTICS*\n\n"
        f"{active_str}\n"
        f"💡 *Start your mining here:* /usdtmining"
    )

    if target_message:
        await target_message.reply_text(text, parse_mode="Markdown", reply_markup=main_menu())
    return text


async def balance_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await render_dashboard(update.effective_user.id, context, update.message)


async def mining_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "⛏️ *SELECT A MINING TIER BELOW TO VIEW DETAILS:*"
    if update.message:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=mining_store_menu())
    elif update.callback_query:
        await update.callback_query.message.reply_text(text, parse_mode="Markdown", reply_markup=mining_store_menu())


async def show_single_miner(update: Update, context: ContextTypes.DEFAULT_TYPE, miner_id: str):
    miner = MINERS.get(miner_id)
    if not miner:
        return

    text = (
        f"⛏️ *{miner['name'].upper()}*\n\n"
        f"⚡️ *Hashrate:* {miner['hashrate']}\n"
        f"💰 *Daily Earnings:* {miner['daily']:.2f} USDŦ\n"
        f"💵 *Monthly Return:* {miner['monthly']:.2f} USDŦ\n"
        f"✅ *Miner Price:* *${miner['price']:.2f}*\n"
    )

    query = update.callback_query
    if query:
        await query.message.reply_photo(
            photo=miner["image"],
            caption=text,
            parse_mode="Markdown",
            reply_markup=single_miner_menu(miner_id)
        )


async def myearnings_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    total_uncollected, tier = calculate_uncollected_earnings(user_id)

    text = (
        f"⛏️ *LIVE USDŦ MINING PROTOCOL*\n\n"
        f"🥇 USDŦ Miner V1 ({tier['miner_v1']['count']} Nodes): {tier['miner_v1']['mined']:.2f} USDŦ\n"
        f"🥈 USDŦ Miner V2 ({tier['miner_v2']['count']} Nodes): {tier['miner_v2']['mined']:.2f} USDŦ\n"
        f"🥉 USDŦ Miner V3 ({tier['miner_v3']['count']} Nodes): {tier['miner_v3']['mined']:.2f} USDŦ\n\n"
        f"💰 *Cumulative USDŦ Mined:* `{total_uncollected:.2f} USDŦ`\n\n"
        f"⚡️ *Upgrade your mining power to boost USDŦ yield!*"
    )
    if update.message:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=earnings_menu())
    elif update.callback_query:
        await update.callback_query.message.reply_text(text, parse_mode="Markdown", reply_markup=earnings_menu())


async def withdraw_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user, _, miners_count = get_dashboard_data(user_id)

    if not miners_count:
        text = (
            "🔐 *To activate the withdrawal feature, you need to buy at least one mining machine.*\n\n"
            "🟢 *Your Status*\n"
            "⛏ Miner: USDŦ Miner V0\n"
            "⚡️ Hashrate: 0 TH/s"
        )
        msg_obj = update.message or update.callback_query.message
        await msg_obj.reply_text(text, parse_mode="Markdown")
        return

    text = (
        f"📤 *WITHDRAWAL SECTION*\n\n"
        f"💰 Your Balance: `{user['balance']:.2f} USDŦ`\n"
        f"💳 Wallet: `{user['payout_wallet']}`\n\n"
        f"⚠️ Minimum Withdrawal: *300 USDŦ*\n"
        f"To request a withdrawal, type `/withdraw_amount` (e.g. `/withdraw_amount 300`)"
    )
    msg_obj = update.message or update.callback_query.message
    await msg_obj.reply_text(text, parse_mode="Markdown")


async def withdraw_amount_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or not context.args[0].replace('.', '', 1).isdigit():
        await update.message.reply_text("❌ Usage: `/withdraw_amount 300`", parse_mode="Markdown")
        return

    amount = float(context.args[0])
    user_id = update.effective_user.id
    success, result = request_withdrawal(user_id, amount)

    if not success:
        await update.message.reply_text(result, parse_mode="Markdown")
        return

    await update.message.reply_text(
        f"✅ Withdrawal request of *{amount:.2f} USDŦ* submitted! (Order ID: `#{result}`)\n"
        "Admin is reviewing your transaction.",
        parse_mode="Markdown"
    )

    if ADMIN_ID:
        user = get_user(user_id)
        admin_txt = (
            f"🚨 *NEW WITHDRAWAL REQUEST* 🚨\n\n"
            f"Withdrawal ID: `#{result}`\n"
            f"User: `{user['first_name']}` (`{user_id}`)\n"
            f"Amount: *{amount:.2f} USDŦ*\n"
            f"Wallet: `{user['payout_wallet']}`"
        )
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Approve Withdrawal", callback_data=f"appw_{result}")]])
        await context.bot.send_message(chat_id=ADMIN_ID, text=admin_txt, parse_mode="Markdown", reply_markup=kb)


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user = update.effective_user

    if data == "home":
        await start(update, context)
    elif data == "dashboard":
        await render_dashboard(user.id, context, query.message)
    elif data == "usdtmining":
        await mining_cmd(update, context)
    elif data.startswith("show_"):
        miner_id = data.replace("show_", "")
        await show_single_miner(update, context, miner_id)
    elif data == "myearnings":
        await myearnings_cmd(update, context)
    elif data == "withdraw":
        await withdraw_cmd(update, context)
    elif data == "collect_profit":
        collected = collect_profit(user.id)
        await query.message.reply_text(f"🎉 Successfully collected *{collected:.2f} USDŦ* to your balance!", parse_mode="Markdown")
        await myearnings_cmd(update, context)

    elif data == "wallet":
        u = get_user(user.id)
        text = (
            f"💡 Your currently set USDŦ wallet is: `{u['payout_wallet']}`\n\n"
            "📤 It will be used for all future withdrawals."
        )
        await query.message.reply_text(text, parse_mode="Markdown", reply_markup=wallet_menu())

    elif data == "set_wallet":
        context.user_data["awaiting_wallet"] = True
        await query.message.reply_text("📝 Please reply with your USDŦ wallet address:")

    elif data.startswith("buy_"):
        m_id = data.replace("buy_", "")
        miner = MINERS[m_id]
        text = f"{user.first_name} Choose a crypto to complete the purchase of {miner['name']} 👇"
        await query.message.reply_text(text, parse_mode="Markdown", reply_markup=payment_methods_menu(m_id))

    elif data.startswith("pay_"):
        parts = data.split("_", 2)
        crypto = parts[1]
        m_id = parts[2]
        miner = MINERS[m_id]
        addr = WALLETS.get(crypto, "Contact Admin")

        order_id = create_order(user.id, m_id, crypto)

        text = (
            f"⚠️ {user.first_name} If you send less than {miner['price']:.2f} {crypto} ~ ${miner['price']:.2f} your deposit will be ignored!\n\n"
            f"✅ Please send the amount to the following address for purchase {miner['name']} with ⚡️ Hashrate {miner['hashrate']}\n\n"
            f"🛡 All deposits are verified instantly.\n\n"
            f"`{addr}`"
        )
        await query.message.reply_text(text, parse_mode="Markdown")

        if ADMIN_ID:
            admin_msg = (
                f"🚨 *NEW MINER PURCHASE REQUEST* 🚨\n\n"
                f"Order ID: `#{order_id}`\n"
                f"User: `{user.first_name}` (`{user.id}`)\n"
                f"Item: {miner['name']}\n"
                f"Payment Method: *{crypto}*"
            )
            kb = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Approve Purchase", callback_data=f"appdep_{order_id}")]])
            await context.bot.send_message(chat_id=ADMIN_ID, text=admin_msg, parse_mode="Markdown", reply_markup=kb)

    elif data.startswith("appdep_"):
        if user.id != ADMIN_ID:
            return
        order_id = int(data.replace("appdep_", ""))
        order = approve_deposit(order_id)
        if order:
            miner = MINERS[order["miner_id"]]
            await query.edit_message_text(f"✅ Deposit Order `#{order_id}` Approved & Mining Started!")
            
            await context.bot.send_message(
                chat_id=order["user_id"],
                text=f"🎉 *Payment Verified!* Your {miner['name']} has been approved and is now active and mining!",
                parse_mode="Markdown"
            )

            if CHANNEL_ID:
                bot_info = await context.bot.get_me()
                target_user = get_user(order["user_id"])
                chan_msg = (
                    f"✅✅✅✅✅✅✅✅\n"
                    f"Activated {miner['name']} for {target_user['first_name']} 🌱🌟 Completed\n\n"
                    f"•Account ID: `{target_user['user_id']}`\n"
                    f"•Hashrate: {miner['hashrate']}\n\n"
                    f"💚 [Claim your 10 USDŦ welcome bonus.](https://t.me/{bot_info.username}?start={target_user['user_id']})"
                )
                await context.bot.send_message(chat_id=CHANNEL_ID, text=chan_msg, parse_mode="Markdown")

    elif data.startswith("appw_"):
        if user.id != ADMIN_ID:
            return
        w_id = int(data.replace("appw_", ""))
        context.user_data["approving_w_id"] = w_id
        await query.message.reply_text(f"📝 Reply with the Transaction Proof (TX Hash) for Withdrawal `#{w_id}`:")


async def handle_text_inputs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    if context.user_data.get("awaiting_wallet"):
        set_wallet(user_id, text)
        context.user_data["awaiting_wallet"] = False
        await update.message.reply_text(f"✅ Payout wallet updated to:\n`{text}`", parse_mode="Markdown")
        return

    if context.user_data.get("approving_w_id") and user_id == ADMIN_ID:
        w_id = context.user_data["approving_w_id"]
        tx_hash = text
        context.user_data["approving_w_id"] = None

        w = approve_withdrawal_db(w_id, tx_hash)
        if w:
            await update.message.reply_text(f"✅ Withdrawal `#{w_id}` Approved!")

            await context.bot.send_message(
                chat_id=w["user_id"],
                text=f"🎉 Your withdrawal of *{w['amount']:.2f} USDŦ* has been processed!\nTX Hash: `{tx_hash}`",
                parse_mode="Markdown"
            )

            if CHANNEL_ID:
                bot_info = await context.bot.get_me()
                target_user = get_user(w["user_id"])
                chan_msg = (
                    f"✅✅✅✅✅✅✅✅\n"
                    f"Withdrawal of {w['amount']:.0f} USDŦ by {target_user['first_name']} 🌱🌟 Completed\n\n"
                    f"•Account ID: `{target_user['user_id']}`\n"
                    f"•Amount: {w['amount']:.0f} USDŦ\n"
                    f"•Transaction Proof: `{tx_hash}`\n\n"
                    f"💚 [Claim your 10 USDŦ welcome bonus.](https://t.me/{bot_info.username}?start={target_user['user_id']})"
                )
                await context.bot.send_message(chat_id=CHANNEL_ID, text=chan_msg, parse_mode="Markdown", disable_web_page_preview=True)


async def admin_add_bal_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if len(context.args) < 2:
        await update.message.reply_text("❌ Usage: `/addbalance <user_id> <amount>`", parse_mode="Markdown")
        return
    try:
        target_id = int(context.args[0])
        amt = float(context.args[1])
        admin_add_balance(target_id, amt)
        await update.message.reply_text(f"✅ Added *{amt:.2f} USDŦ* to User `{target_id}` balance.", parse_mode="Markdown")
        
        await context.bot.send_message(
            chat_id=target_id,
            text=f"🎉 *Bonus Alert!* Admin has credited your account with *{amt:.2f} USDŦ*!",
            parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error updating balance: {e}")


async def admin_broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.args:
        await update.message.reply_text("❌ Usage: `/broadcast <Your Announcement Message Here>`", parse_mode="Markdown")
        return

    broadcast_text = " ".join(context.args)
    user_ids = get_all_user_ids()
    
    success_count = 0
    fail_count = 0

    status_msg = await update.message.reply_text(f"📢 Starting broadcast to {len(user_ids)} users...")

    for u_id in user_ids:
        try:
            await context.bot.send_message(
                chat_id=u_id,
                text=f"📢 *ANNOUNCEMENT*\n\n{broadcast_text}",
                parse_mode="Markdown"
            )
            success_count += 1
            await asyncio.sleep(0.05)
        except Exception:
            fail_count += 1

    await status_msg.edit_text(
        f"✅ *Broadcast Finished*\n\n"
        f"• Delivered: `{success_count}`\n"
        f"• Failed/Blocked: `{fail_count}`",
        parse_mode="Markdown"
    )


def main():
    # 1. Initialize SQLite Database
    init_db()

    # 2. Start Flask Keep-Alive Server for Render
    keep_alive()

    # 3. Build Application
    app = ApplicationBuilder().token(TOKEN).build()

    # --- USER COMMANDS ---
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("balance", balance_cmd))
    app.add_handler(CommandHandler("usdtmining", mining_cmd))
    app.add_handler(CommandHandler("myearnings", myearnings_cmd))
    app.add_handler(CommandHandler("withdraw", withdraw_cmd))
    app.add_handler(CommandHandler("withdraw_amount", withdraw_amount_cmd))
    
    # --- ADMIN COMMANDS ---
    app.add_handler(CommandHandler("addbalance", admin_add_bal_cmd))
    app.add_handler(CommandHandler("broadcast", admin_broadcast_cmd))

    # --- CALLBACK & MESSAGE HANDLERS ---
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_inputs))

    # 4. Start Bot Polling
    print("🚀 SureMine USDŦ Production Bot is live...")
    app.run_polling()


if __name__ == '__main__':
    main()