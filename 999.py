#
import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

TOKEN = "7388356518:AAFfaAm0IwpP79ySb3FGZAp36ePgGxG0kbc"
ADMIN_ID = 6043728545
GROUPS = [
    "@baogau", "@DuyetRutTeck", "@AppGameOnline9",
    "@ChatXocDia88", "@sanchoisangai3"
]
DATA_FILE = "user_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    data = load_data()
    if user_id not in data:
        data[user_id] = {"invited": [], "ref": None, "withdrawn": False, "bank": None, "name": user.full_name}
        save_data(data)

    args = context.args
    if args:
        ref_id = args[0]
        if ref_id != user_id and user_id not in data.get(ref_id, {}).get("invited", []):
            if ref_id not in data:
                data[ref_id] = {"invited": [], "ref": None, "withdrawn": False, "bank": None, "name": ""}
            data[ref_id]["invited"].append(user_id)
            save_data(data)

    group_status = []
    for group in GROUPS:
        try:
            member = await context.bot.get_chat_member(chat_id=group, user_id=int(user_id))
            if member.status in ["member", "administrator", "creator"]:
                group_status.append("✅")
            else:
                group_status.append("❌")
        except:
            group_status.append("❌")

    group_list = "\n".join([f"{group_status[i]} {GROUPS[i]}" for i in range(len(GROUPS))])
    message = f"📢 Vui lòng tham gia các nhóm sau:\n{group_list}"
    keyboard = [[InlineKeyboardButton("✅ Xác Minh", callback_data="verify")]]
    await update.message.reply_text(message, reply_markup=InlineKeyboardMarkup(keyboard))

async def verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)

    group_status = []
    for group in GROUPS:
        try:
            member = await context.bot.get_chat_member(chat_id=group, user_id=int(user_id))
            if member.status in ["member", "administrator", "creator"]:
                group_status.append("✅")
            else:
                group_status.append("❌")
        except:
            group_status.append("❌")

    data = load_data()
    invited = data.get(user_id, {}).get("invited", [])
    money = len(invited) * 1000
    can_withdraw = money >= 20000 and not data[user_id].get("withdrawn", False)

    if all(status == "✅" for status in group_status):
        text = (
            "🎉 Bạn đã tham gia đủ nhóm!\n"
            f"👥 Bạn đã mời: {len(invited)} người\n"
            f"💰 Số tiền hiện có: {money} VNĐ\n"
        )
        if can_withdraw:
            text += "\n💳 Nhập lệnh /rut <ngân hàng>-<Họ tên>-<STK>"
        elif data[user_id].get("withdrawn", False):
            text += "\n✅ Bạn đã rút tiền trước đó."
        else:
            text += "\n🔺 Mời thêm để đạt 20K (1 lượt = 1K)"

        menu = [[
    InlineKeyboardButton("💳 Rút Tiền", callback_data="rut"),
    InlineKeyboardButton("👤 Tài Khoản", callback_data="account")
], [
    InlineKeyboardButton("📊 Thống Kê", callback_data="stats"),
    InlineKeyboardButton("☎ Hỗ Trợ", callback_data="support")
], [
    InlineKeyboardButton("👥 Mời Bạn Bè", callback_data="invite")
]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(menu))
    else:
        group_list = "\n".join([f"{group_status[i]} {GROUPS[i]}" for i in range(len(GROUPS))])
        msg = f"❌ Bạn chưa tham gia đủ nhóm!\n\n📢 Cần tham gia đủ:\n{group_list}"
        keyboard = [[InlineKeyboardButton("✅ Xác Minh Lại", callback_data="verify")]]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_rut(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()
    if user_id not in data or data[user_id].get("withdrawn"):
        await update.message.reply_text("❌ Bạn không đủ điều kiện hoặc đã rút rồi.")
        return
    try:
        args = update.message.text.split(" ", 1)[1]
        bank_info = args.strip()
        data[user_id]["withdrawn"] = True
        data[user_id]["bank"] = bank_info
        save_data(data)

        buttons = [[
            InlineKeyboardButton("✅ Thành Công", callback_data=f"approve_{user_id}"),
            InlineKeyboardButton("❌ Không Thành Công", callback_data=f"deny_{user_id}")
        ]]
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"📥 Rút tiền từ {user_id}:\n{bank_info}",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        await update.message.reply_text("✅ Đã gửi yêu cầu đến Admin, vui lòng chờ!")
    except:
        await update.message.reply_text(
            "❌ Sai cú pháp! Dùng:\n/rut <ngân hàng>-<Họ tên>-<STK>"
        )


async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = load_data()
    cb_data = query.data

    if cb_data.startswith("approve_"):
        uid = cb_data.split("_")[1]
        await context.bot.send_message(chat_id=int(uid), text="✅ Rút tiền thành công!")
        await query.edit_message_text("🟢 Admin xử lý: Thành công")

    elif cb_data.startswith("deny_"):
        uid = cb_data.split("_")[1]

        if uid not in data:
            data[uid] = {"invited": [], "ref": None, "withdrawn": False, "bank": None, "name": ""}

        data[uid]["withdrawn"] = False
        save_data(data)
        await context.bot.send_message(chat_id=int(uid), text="❌ Rút tiền không thành công.")
        await query.edit_message_text("🔴 Admin xử lý: Thất bại")

async def extra_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = load_data()
    user_id = str(query.from_user.id)

    if query.data == "rut":
        await query.message.reply_text(
            "💳 Nhập lệnh:\n/rut <ngân hàng>-<Họ tên>-<Số tài khoản>"
        )

    elif query.data == "account":
        user = data.get(user_id, {})
        name = user.get("name", "Ẩn danh")
        invited = user.get("invited", [])
        balance = len(invited) * 1000
        await query.message.reply_text(
            f"🏆Tên: {name}\n💰Số dư: {balance} VNĐ\n🆔ID: {user_id}"
        )

    elif query.data == "stats":
        total_users = len(data)
        total_invites = sum(len(u.get("invited", [])) for u in data.values())
        await query.message.reply_text(
            f"📊 Tổng user: {total_users}\n👥 Tổng mời: {total_invites}"
        )

    elif query.data == "support":
        await query.message.reply_text("☎ Liên hệ hỗ trợ: @admin")

    elif query.data == "invite":
        bot_username = (await context.bot.get_me()).username
        await query.message.reply_text(
            f"👥 Mời bạn bè nhận 1.000đ mỗi lượt mời!\n\n"
            f"📎 Link giới thiệu của bạn:\nhttps://t.me/{bot_username}?start={user_id}"
        )


import asyncio

async def main():
    keep_alive()
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("rut", handle_rut))
    app.add_handler(CallbackQueryHandler(verify, pattern="^verify$"))
    app.add_handler(CallbackQueryHandler(admin_callback, pattern="^(approve_|deny_).*$"))
    app.add_handler(CallbackQueryHandler(extra_buttons, pattern="^(rut|account|stats|support|invite)$"))

    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await app.updater.idle()

if __name__ == "__main__":
    asyncio.run(main())
