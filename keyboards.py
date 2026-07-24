# keyboards.py

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def main_menu():
    keyboard = [
        [
            InlineKeyboardButton("📊 Dashboard", callback_data="dashboard"),
            InlineKeyboardButton("⛏️ USDŦ Mining", callback_data="mining_store")
        ],
        [
            InlineKeyboardButton("💳 Payout Wallet", callback_data="payout_wallet"),
            InlineKeyboardButton("👥 Referral", callback_data="referral")
        ],
        [
            InlineKeyboardButton("📢 Official Channel", url="https://t.me/suremineusdtnews")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def miner_store_menu():
    keyboard = [
        [InlineKeyboardButton("USDŦ Miner V1 ($4.00)", callback_data="show_miner_v1")],
        [InlineKeyboardButton("USDŦ Miner V2 ($6.00)", callback_data="show_miner_v2")],
        [InlineKeyboardButton("USDŦ Miner V3 ($8.00)", callback_data="show_miner_v3")],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)


def miner_detail_menu(miner_id: str):
    keyboard = [
        [InlineKeyboardButton("⚡ Buy This Miner", callback_data=f"buy_{miner_id}")],
        [InlineKeyboardButton("🔙 Back to Store", callback_data="mining_store")]
    ]
    return InlineKeyboardMarkup(keyboard)


def payment_methods_menu(miner_id: str):
    keyboard = [
        [
            InlineKeyboardButton("USDT (TRC20)", callback_data=f"pay_USDT_TRC20_{miner_id}"),
            InlineKeyboardButton("USDT (BEP20)", callback_data=f"pay_USDT_BEP20_{miner_id}")
        ],
        [
            InlineKeyboardButton("USDT (TON)", callback_data=f"pay_USDT_TON_{miner_id}"),
            InlineKeyboardButton("TRX", callback_data=f"pay_TRX_{miner_id}")
        ],
        [
            InlineKeyboardButton("SOL", callback_data=f"pay_SOL_{miner_id}"),
            InlineKeyboardButton("TON", callback_data=f"pay_TON_{miner_id}")
        ],
        [
            InlineKeyboardButton("SUI", callback_data=f"pay_SUI_{miner_id}"),
            InlineKeyboardButton("BNB", callback_data=f"pay_BNB_{miner_id}")
        ],
        [
            InlineKeyboardButton("ETH (ERC20)", callback_data=f"pay_ETH_{miner_id}")
        ],
        [
            InlineKeyboardButton("🔙 Back to Miner Details", callback_data=f"show_{miner_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def back_to_main_menu():
    keyboard = [
        [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)