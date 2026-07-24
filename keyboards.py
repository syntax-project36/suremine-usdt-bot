from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def main_menu():
    keyboard = [
        [
            InlineKeyboardButton("📊 Dashboard", callback_data="dashboard"),
            InlineKeyboardButton("⛏️ USDT Mining", callback_data="usdtmining")
        ],
        [
            InlineKeyboardButton("💰 My Earnings", callback_data="myearnings"),
            InlineKeyboardButton("💳 Payout Wallet", callback_data="wallet")
        ],
        [
            InlineKeyboardButton("📤 Withdraw Funds", callback_data="withdraw")
        ],
        [
            InlineKeyboardButton("📢 Official Channel", url="https://t.me/suremineusdtnews")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def mining_store_menu():
    keyboard = [
        [InlineKeyboardButton("🥇 USDŦ Miner V1 (1 Fan)", callback_data="show_miner_v1")],
        [InlineKeyboardButton("🥈 USDŦ Miner V2 (2 Fans)", callback_data="show_miner_v2")],
        [InlineKeyboardButton("🥉 USDŦ Miner V3 (3 Fans)", callback_data="show_miner_v3")],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="home")]
    ]
    return InlineKeyboardMarkup(keyboard)

def single_miner_menu(miner_id):
    keyboard = [
        [InlineKeyboardButton("💳 Buy This Miner", callback_data=f"buy_{miner_id}")],
        [InlineKeyboardButton("🔙 Back to Mining Tiers", callback_data="usdtmining")]
    ]
    return InlineKeyboardMarkup(keyboard)

def payment_methods_menu(miner_id):
    keyboard = [
        [
            InlineKeyboardButton("USDT", callback_data=f"pay_USDT_{miner_id}"),
            InlineKeyboardButton("BTC", callback_data=f"pay_BTC_{miner_id}")
        ],
        [
            InlineKeyboardButton("ETH", callback_data=f"pay_ETH_{miner_id}"),
            InlineKeyboardButton("LTC", callback_data=f"pay_LTC_{miner_id}")
        ],
        [
            InlineKeyboardButton("TRX", callback_data=f"pay_TRX_{miner_id}"),
            InlineKeyboardButton("BNB", callback_data=f"pay_BNB_{miner_id}")
        ],
        [
            InlineKeyboardButton("🔙 Back to Tier Details", callback_data=f"show_{miner_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def wallet_menu():
    keyboard = [
        [InlineKeyboardButton("✏️ Set / Change Wallet Address", callback_data="set_wallet")],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="home")]
    ]
    return InlineKeyboardMarkup(keyboard)

def earnings_menu():
    keyboard = [
        [InlineKeyboardButton("⚡️ Collect Mined USDŦ", callback_data="collect_profit")],
        [InlineKeyboardButton("⛏️ Buy More Hashrate", callback_data="usdtmining")],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="home")]
    ]
    return InlineKeyboardMarkup(keyboard)