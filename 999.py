
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from keep_alive import keep_alive
import json, os

TOKEN = "7388356518:AAFfaAm0IwpP79ySb3FGZAp36ePgGxG0kbc"
ADMIN_ID = 6043728545

GROUPS = [
    "@baogau",
    "@DuyetRutTeck",
    "@AppGameOnline9",
    "@ChatXocDia88",
    "@sanchoisangai3"
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
        data[user_id] = {
            "invited": [],
            "ref": None,
            "withdrawn": False,
            "bank": None,
            "name": user.full_name
        }
        save_data(data)

    args = context.args
    if args:
        ref_id = args[0]
        if ref_id != user_id and user_id not in data.get(ref_id, {}).get("invited", []):
            if ref_id not in data:
                data[ref_id] = {
                    "invited": [],
                    "ref": None,
                    "withdrawn": False,
                    "bank": None,
                    "name": ""
                }
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
            text += "\n💳 Bạn đủ điều kiện rút tiền!\n👉 Hãy nhập lệnh:\n/rut <ngân hàng>-<Họ tên>-<Số tài khoản>\n\nVí dụ:\n/rut Vietcombank-Nguyễn Văn A-0123456789"
        elif data[user_id].get("withdrawn", False):
            text += "\n✅ Bạn đã rút tiền trước đó."
        else:
            text += "\n🔺 Mời thêm để đạt đủ 20K (1 lượt mời = 1K)"

        menu = [[
            InlineKeyboardButton("💳 Rút Tiền", callback_data="rut"),
            InlineKeyboardButton("👤 Tài Khoản", callback_data="account")
        ], [
            InlineKeyboardButton("📊 Thống Kê", callback_data="stats"),
            InlineKeyboardButton("☎ Hỗ Trợ", callback_data="support")
        ]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(menu))
    else:
        group_list = "\n".join([f"{group_status[i]} {GROUPS[i]}" for i in range(len(GROUPS))])
        msg = f"❌ Bạn chưa tham gia đủ nhóm!\n\n📢 Tham gia đủ các nhóm sau:\n{group_list}"
        keyboard = [[InlineKeyboardButton("✅ Xác Minh Lại", callback_data="verify")]]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_rut(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()
    if user_id not in data or data[user_id].get("withdrawn"):
        await update.message.reply_text("❌ Bạn không đủ điều kiện hoặc đã rút trước đó.")
        return

    try:
        args = update.message.text.split(" ", 1)[1]
        bank_info = args.strip()
        data[user_id]["withdrawn"] = True
        data[user_id]["bank"] = bank_info
        save_data(data)

        buttons = [
            [
                InlineKeyboardButton("✅ Thành Công", callback_data=f"approve_{user_id}"),
                InlineKeyboardButton("❌ Không Thành Công", callback_data=f"deny_{user_id}")
            ]
        ]

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"📥 Yêu cầu rút tiền từ ID {user_id}:\n{bank_info}",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        await update.message.reply_text("📨 Đã gửi yêu cầu rút tiền tới Admin. Vui lòng chờ duyệt!")
    except:
        await update.message.reply_text("❌ Sai cú pháp! Vui lòng dùng:\n/rut <ngân hàng>-<Họ tên>-<STK>")

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = load_data()
    cb_data = query.data

    if cb_data.startswith("approve_"):
        uid = cb_data.split("_")[1]
        await context.bot.send_message(chat_id=int(uid), text="✅ Rút tiền thành công! Hãy kiểm tra tài khoản của bạn.")
        await query.edit_message_text("🟢 Đã xử lý: Thành công")

    elif cb_data.startswith("deny_"):
        uid = cb_data.split("_")[1]
        data[uid]["withdrawn"] = False
        save_data(data)
        await context.bot.send_message(chat_id=int(uid), text="❌ Rút tiền không thành công. Vui lòng thử lại sau hoặc liên hệ Admin.")
        await query.edit_message_text("🔴 Đã xử lý: Không thành công")

async def extra_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = load_data()
    user_id = str(query.from_user.id)

    if query.data == "rut":
        await query.message.reply_text("💳 Hãy nhập lệnh:\n/rut <ngân hàng>-<Họ tên>-<Số tài khoản>")
    elif query.data == "account":
        user = data.get(user_id, {})
        name = user.get("name", "Ẩn danh")
        invited = user.get("invited", [])
        balance = len(invited) * 1000
        await query.message.reply_text(f"🏆Tên: {name}\n💰Số Dư: {balance} Đ\n🆔ID Của Bạn: {user_id}")
    elif query.data == "stats":
        total_users = len(data)
        total_invites = sum(len(u.get("invited", [])) for u in data.values())
        await query.message.reply_text(f"📊 Tổng người dùng: {total_users}\n👥 Tổng lượt mời: {total_invites}")
    elif query.data == "support":
        await query.message.reply_text("☎ Liên hệ hỗ trợ: @admin hoặc nhóm hỗ trợ")

# Chạy bot
if __name__ == "__main__":
    keep_alive()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("rut", handle_rut))
    app.add_handler(CallbackQueryHandler(verify, pattern="^verify$"))
    app.add_handler(CallbackQueryHandler(admin_callback, pattern="^(approve_|deny_).*$"))
    app.add_handler(CallbackQueryHandler(extra_buttons, pattern="^(rut|account|stats|support)$"))
    app.run_polling()
