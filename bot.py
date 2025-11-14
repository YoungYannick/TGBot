import logging
import random
import string
import datetime
import json
import os
import time
from html import escape as escape_html

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, Bot, Message
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from telegram.constants import ParseMode, ChatType
from telegram.helpers import escape_markdown

from database import SessionLocal, User, BlockedKeyword, init_db, SentMessage

DATABASE_FILE = 'bot_data.db'

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

perPage = 5

CST_TZ = datetime.timezone(datetime.timedelta(hours=8))


def now_cst():
    return datetime.datetime.now(CST_TZ)

def load_db_config():
    from database import SessionLocal, Config
    db = SessionLocal()
    c = db.query(Config).first()
    db.close()
    if not c:
        return None
    return {
        'BOT_TOKEN': c.bot_token,
        'ADMIN_ID': c.admin_id
    }


VERIFICATION_TOKENS = {}


def get_or_create_user(session, user_data: dict):
    user = session.get(User, user_data['id'])
    # 统一使用北京时间
    now = now_cst().astimezone(datetime.timezone.utc)

    if user:
        user.username = user_data.get('username')
        user.first_name = user_data.get('first_name')
        user.last_name = user_data.get('last_name')
        user.lang_code = user_data.get('language_code')
        user.last_seen = now
    else:
        user = User(
            id=user_data['id'],
            username=user_data.get('username'),
            first_name=user_data.get('first_name'),
            last_name=user_data.get('last_name'),
            lang_code=user_data.get('language_code'),
            is_verified=False,
            is_blocked=False,
            created_at=now,
            last_seen=now
        )
        session.add(user)

    session.commit()
    return user


def get_user_from_db(session, user_id: int):
    return session.get(User, user_id)


def check_keyword(session, text: str):
    if not text:
        return None

    keywords = session.query(BlockedKeyword.keyword).all()
    text_lower = text.lower()

    for (kw,) in keywords:
        if kw.lower() in text_lower:
            return kw
    return None


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = user.language_code or 'en'

    db_session = SessionLocal()
    try:
        get_or_create_user(db_session, user.to_dict())
    finally:
        db_session.close()

    from database import StartMessage

    db_session = SessionLocal()
    try:
        msg = db_session.query(StartMessage).filter_by(
            lang="zh" if lang.startswith("zh") else "en"
        ).first()

        text = msg.content if msg else "Welcome."
    finally:
        db_session.close()

    await update.message.reply_text(text)
    await check_verification_and_forward(update, context)


async def send_verification(chat_id: int, lang: str, context: ContextTypes.DEFAULT_TYPE):
    token = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    expiry = now_cst() + datetime.timedelta(minutes=10)
    VERIFICATION_TOKENS[chat_id] = (token, expiry)

    if lang.startswith('zh'):
        text = "🛡 为了防止骚扰，请先完成一次验证：点击下方按钮。"
        btn_text = "✅ 我是人类"
    else:
        text = "🛡 To prevent spam, please complete a quick verification: tap the button below."
        btn_text = "✅ I'm human"

    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton(btn_text, callback_data=f"verify_{token}")]]
    )
    await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=keyboard)


async def verification_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    lang = query.from_user.language_code or 'en'
    token = query.data.split("_")[1]

    stored_token_data = VERIFICATION_TOKENS.get(user_id)

    if (stored_token_data and
            stored_token_data[0] == token and
            stored_token_data[1] > now_cst()):

        db_session = SessionLocal()
        try:
            user = get_or_create_user(db_session, query.from_user.to_dict())
            user.is_verified = True
            db_session.commit()

            if user_id in VERIFICATION_TOKENS:
                del VERIFICATION_TOKENS[user_id]

            if lang.startswith('zh'):
                await query.edit_message_text("✅ 验证通过！现在您可以正常发送消息了。")
            else:
                await query.edit_message_text("✅ Verified! You can now send messages normally.")

        finally:
            db_session.close()
    else:
        if user_id in VERIFICATION_TOKENS:
            del VERIFICATION_TOKENS[user_id]

        if lang.startswith('zh'):
            await query.edit_message_text("验证失败或已过期，请重新发送消息以获取验证。")
        else:
            await query.edit_message_text(
                "Verification failed or expired. Please send a message again to get verified.")


async def view_blocked_user_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id_str = query.data.split("_")[-1]
    if not user_id_str.isdigit():
        await query.edit_message_text("❌ 无效的用户ID。")
        return

    user_id = int(user_id_str)
    db_session = SessionLocal()
    try:
        user = db_session.get(User, user_id)
        if not user or not user.is_blocked:
            await query.edit_message_text("❌ 未找到被屏蔽的用户。")
            return

        info_card = format_user_info_card(user)

        keyboard = [
            [InlineKeyboardButton("解封", callback_data=f"unblock_{user_id}")],
            [InlineKeyboardButton("返回", callback_data="return_to_list")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(info_card, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
    finally:
        db_session.close()


async def secondary_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    if data.startswith("unblock_"):
        user_id_str = data.split("_")[-1]
        if not user_id_str.isdigit():
            await query.edit_message_text("❌ 无效的用户ID。")
            return

        user_id = int(user_id_str)
        db_session = SessionLocal()
        try:
            user = db_session.get(User, user_id)
            if user:
                user.is_blocked = False
                db_session.commit()
                if user:
                    user.is_blocked = False
                    db_session.commit()

                    blocked_users = db_session.query(User).filter_by(is_blocked=True).order_by(User.id).all()

                    if blocked_users:
                        page = 1
                        per_page = perPage
                        text, reply_markup = get_blocked_list_page_content(blocked_users, page, per_page)

                        await query.edit_message_text(
                            text,
                            parse_mode=ParseMode.HTML,
                            reply_markup=reply_markup
                        )
                    else:
                        await query.edit_message_text("🚫 当前没有被屏蔽的用户。")
                try:
                    await context.bot.send_message(user_id, "🎉 您已被管理员解除屏蔽，现在可以正常发送消息了。")
                except Exception as e:
                    logger.warning(f"Failed to send unblock notification to user {user_id}: {e}")
            else:
                await query.edit_message_text("❌ 未找到用户。")
        finally:
            db_session.close()

    elif data == "return_to_list":
        await query.edit_message_text("↩️ 已返回到列表。请重新使用 /listblock_all 查看更新列表。")


def get_blocked_list_page_content(users, page, per_page):
    total_users = len(users)
    if total_users == 0:
        return "🚫 当前没有被屏蔽的用户。", None

    total_pages = (total_users + per_page - 1) // per_page
    page = max(1, min(page, total_pages))

    start = (page - 1) * per_page
    end = start + per_page
    page_users = users[start:end]

    text = f"🚫 <b>被屏蔽的用户列表 (第 {page}/{total_pages} 页，总 {total_users} 个)：</b>\n"
    keyboard = []

    for user in page_users:
        name = (f"{user.first_name or ''} {user.last_name or ''}").strip()
        username = f"@{user.username}" if user.username else name
        escaped_info = escape_html(username)
        text += f"• <code>{user.id}</code> ({escaped_info})\n"

        keyboard.append([InlineKeyboardButton(f"查看 {user.id}", callback_data=f"view_blocked_{user.id}")])

    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton("« 上一页", callback_data=f"blocked_page_{page - 1}"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton("下一页 »", callback_data=f"blocked_page_{page + 1}"))
    if nav_buttons:
        keyboard.append(nav_buttons)

    reply_markup = InlineKeyboardMarkup(keyboard)
    return text, reply_markup


async def blocked_page_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    page_str = query.data.split("_")[-1]
    if not page_str.isdigit():
        return

    page = int(page_str)
    db_session = SessionLocal()
    try:
        users = db_session.query(User).filter_by(is_blocked=True).order_by(User.id).all()
        per_page = perPage

        text, reply_markup = get_blocked_list_page_content(users, page, per_page)
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
    finally:
        db_session.close()


async def user_info_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id_str = query.data.split("_")[1]

    if not user_id_str.isdigit():
        await query.message.reply_text("❌ 回调数据错误。")
        return

    user_id = int(user_id_str)

    db_session = SessionLocal()
    try:
        user = db_session.get(User, user_id)
        if not user:
            await query.message.reply_text("❌ 未在数据库中找到该用户。")
            return

        info_card = format_user_info_card(user)
        await query.message.reply_text(info_card, parse_mode=ParseMode.HTML)

    except Exception as e:
        logger.error(f"Error processing user_info callback: {e}")
        await query.message.reply_text(f"❌ 发生错误: {e}")
    finally:
        db_session.close()


async def check_verification_and_forward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message:
        return

    user = update.effective_user
    lang = user.language_code or 'en'

    db_session = SessionLocal()
    try:
        db_user = get_or_create_user(db_session, user.to_dict())

        if db_user.is_blocked:
            if lang.startswith('zh'):
                await message.reply_text("🚫 您已被管理员屏蔽，无法发送消息。")
            else:
                await message.reply_text("🚫 You have been blocked by the administrator and cannot send messages.")
            return

        if not db_user.is_verified:
            await send_verification(user.id, lang, context)
            return

        text_to_check = message.text or message.caption
        hit_keyword = check_keyword(db_session, text_to_check)
        if hit_keyword:
            if lang.startswith('zh'):
                await message.reply_text(
                    f"⚠️ 您的消息包含被屏蔽的关键词 (<code>{escape_html(str(hit_keyword))}</code>)，未被转发给管理员。",
                    parse_mode=ParseMode.HTML
                )
            else:
                await message.reply_text(
                    f"⚠️ Your message contains blocked keywords (<code>{escape_html(str(hit_keyword))}</code>) and was not forwarded to the admin.",
                    parse_mode=ParseMode.HTML
                )

            await context.bot.send_message(
                ADMIN_ID,
                f"🚫 已拦截来自 {user.mention_html()} (@{user.username} UID: <code>{user.id}</code>) 的消息，命中关键词：<code>{escape_html(str(hit_keyword))}</code>",
                parse_mode=ParseMode.HTML
            )
            return

        try:
            forwarded_msg = await message.forward(ADMIN_ID)

            from database import MessageMap
            db_session.add(MessageMap(admin_msg_id=forwarded_msg.message_id, user_id=user.id))

            message_content = message.text or message.caption
            db_session.add(SentMessage(
                user_id=user.id,
                message_text=(message_content[:500] + '...') if message_content and len(
                    message_content) > 500 else message_content,
                sent_at = now_cst().astimezone(datetime.timezone.utc)
            ))

            db_session.commit()

        except Exception as e:
            logger.error(f"Failed to forward message: {e}")
            if lang.startswith('zh'):
                await message.reply_text("抱歉，您的消息未能成功转发给管理员，请稍后再试。")
            else:
                await message.reply_text(
                    "Sorry, your message could not be forwarded to the administrator. Please try again later.")

    finally:
        db_session.close()


def format_user_info_card(user: User):
    username = f"@{user.username}" if user.username else "N/A"
    name = (f"{user.first_name or ''} {user.last_name or ''}").strip()

    username = escape_html(username)
    name = escape_html(name)
    status = 'Blocked 🚫' if user.is_blocked else 'Active ✅'

    text = f"<b>👤 用户信息</b>\n" \
           f"UID: <code>{user.id}</code>\n" \
           f"Username: {username}\n" \
           f"Name: {name}\n" \
           f"Lang: <code>{user.lang_code}</code>\n" \
           f"Status: <b>{status}</b>"
    return text


async def handle_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    if not message.reply_to_message:
        await message.reply_text("🙅 请点击**转发的用户消息**进行回复，这样我才能知道您是想回复哪位用户。")
        return

    replied_msg = message.reply_to_message
    fwd_msg = replied_msg

    if replied_msg.from_user.is_bot and replied_msg.reply_to_message:
        fwd_msg = replied_msg.reply_to_message

    db_session = SessionLocal()
    try:
        from database import MessageMap
        mapping = db_session.get(MessageMap, fwd_msg.message_id)
        target_user_id = mapping.user_id if mapping else None

        if not target_user_id:
            await message.reply_text("❌ 无法识别要操作的用户。请确保您回复的是用户转发给您的消息。")
            return

        await message.copy(chat_id=target_user_id)

    except Exception as e:
        await message.reply_text(f"回复发送失败: {e}")

    finally:
        db_session.close()


async def send_blocked_list_page(original_message, users, page, per_page):
    text, reply_markup = get_blocked_list_page_content(users, page, per_page)
    await original_message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)


async def admin_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from database import MessageMap
    message = update.message
    command_text = message.text.split(' ', 1)
    command = command_text[0].lower()
    args = command_text[1] if len(command_text) > 1 else ""

    db_session = SessionLocal()
    try:
        if command == '/addkw':
            if not args:
                await message.reply_text("用法: /addkw <关键词>")
                return

            kw = args.strip().lower()
            exists = db_session.query(BlockedKeyword).filter_by(keyword=kw).first()
            if exists:
                await message.reply_text(f"关键词 <code>{escape_html(kw)}</code> 已存在。", parse_mode=ParseMode.HTML)
            else:
                new_kw = BlockedKeyword(keyword=kw, added_at=now_cst())
                db_session.add(new_kw)
                db_session.commit()
                await message.reply_text(f"✅ 已添加屏蔽关键词：<code>{escape_html(kw)}</code>",
                                         parse_mode=ParseMode.HTML)
            return

        if command == '/rmkw':
            if not args:
                await message.reply_text("用法: /rmkw <关键词>")
                return

            kw = args.strip().lower()
            kw_obj = db_session.query(BlockedKeyword).filter_by(keyword=kw).first()
            if kw_obj:
                db_session.delete(kw_obj)
                db_session.commit()
                await message.reply_text(f"✅ 已移除屏蔽关键词：<code>{escape_html(kw)}</code>",
                                         parse_mode=ParseMode.HTML)
            else:
                await message.reply_text(f"关键词 <code>{escape_html(kw)}</code> 未找到。", parse_mode=ParseMode.HTML)
            return

        if command == '/listkw_all':
            keywords = db_session.query(BlockedKeyword.keyword).all()
            if not keywords:
                await message.reply_text("📃 当前屏蔽关键词列表为空。")
                return

            total = len(keywords)
            words = "  ".join([f"<code>{escape_html(kw)}</code>" for (kw,) in keywords])
            text = (
                 f"📃 <b>当前屏蔽关键词列表（共 {total} 个）：</b>\n\n"
                f"{words}"
            )
            await message.reply_text(text, parse_mode=ParseMode.HTML)
            return

        if command == '/listblock_all':
            users = db_session.query(User).filter_by(is_blocked=True).order_by(User.id).all()
            if not users:
                await message.reply_text("🚫 当前没有被屏蔽的用户。")
                return

            page = 1
            per_page = perPage
            await send_blocked_list_page(message, users, page, per_page)
            return

        if command in ['/block', '/unblock', '/checkblock', '/info']:
            if not message.reply_to_message:
                await message.reply_text(f"请回复一条**用户的转发消息**来使用 <code>{command}</code> 命令。",
                                         parse_mode=ParseMode.HTML)
                return

            replied_msg = message.reply_to_message
            fwd_msg = replied_msg

            if replied_msg.from_user.is_bot and replied_msg.reply_to_message:
                fwd_msg = replied_msg.reply_to_message

            mapping = db_session.get(MessageMap, fwd_msg.message_id)
            target_user_id = mapping.user_id if mapping else None

            if not target_user_id:
                await message.reply_text("❌ 无法识别要操作的用户。请确保你回复的是转发消息。")
                return

            target_user = db_session.get(User, target_user_id)
            if not target_user:
                try:
                    user_data_source = await context.bot.get_chat(target_user_id)
                    user_data = {
                        'id': user_data_source.id,
                        'username': user_data_source.username,
                        'first_name': user_data_source.first_name,
                        'last_name': user_data_source.last_name,
                    }
                    target_user = get_or_create_user(db_session, user_data)
                except Exception as e:
                    logger.error(f"Could not find user {target_user_id} in DB and could not fetch from TG: {e}")
                    await message.reply_text(f"数据库中未找到用户 <code>{target_user_id}</code>。",
                                             parse_mode=ParseMode.HTML)
                    return

            if command == '/block':
                target_user.is_blocked = True
                db_session.commit()
                await message.reply_text(f"✅ 用户 <code>{target_user_id}</code> 已被屏蔽。", parse_mode=ParseMode.HTML)
                try:
                    await context.bot.send_message(target_user_id, "🚫 您已被管理员屏蔽，无法发送消息。")
                except Exception as e:
                    logger.warning(f"Failed to send block notification to user {target_user_id}: {e}")

            elif command == '/unblock':
                target_user.is_blocked = False
                db_session.commit()
                await message.reply_text(f"✅ 用户 <code>{target_user_id}</code> 已解除屏蔽。", parse_mode=ParseMode.HTML)
                try:
                    await context.bot.send_message(target_user_id, "🎉 您已被管理员解除屏蔽，现在可以正常发送消息了。")
                except Exception as e:
                    logger.warning(f"Failed to send unblock notification to user {target_user_id}: {e}")

            elif command == '/checkblock' or command == '/info':
                info_card = format_user_info_card(target_user)
                await message.reply_text(info_card, parse_mode=ParseMode.HTML)
    except Exception as e:
        await message.reply_text(f"❌ 命令执行失败：\n{escape_html(str(e))}", parse_mode=ParseMode.HTML)
        logger.error(f"Error executing admin command {command}: {e}", exc_info=True)
    finally:
        db_session.close()


async def set_admin_commands(app: Application):
    commands = [
        ("block", "屏蔽用户 (回复消息)"),
        ("unblock", "解封用户 (回复消息)"),
        ("checkblock", "查看用户状态 (回复消息)"),
        ("info", "查看用户详细信息 (回复消息)"),
        ("addkw", "添加屏蔽词"),
        ("rmkw", "移除屏蔽词"),
        ("listkw_all", "查看所有屏蔽词"),
        ("listblock_all", "查看所有被封禁用户"),
    ]
    await app.bot.set_my_commands(commands, scope={"type": "chat", "chat_id": ADMIN_ID})

    user_commands = [
        ("start", "开始 / Welcome"),
    ]
    await app.bot.set_my_commands(user_commands)


def main():
    global ADMIN_ID
    from database import init_db
    init_db()

    BOT_CONFIG = None
    while BOT_CONFIG is None:
        BOT_CONFIG = load_db_config()
        if BOT_CONFIG is None:
            logger.warning("数据库未找到配置，等待 Web 面板完成初始化...")
            time.sleep(5)

    ADMIN_ID = int(BOT_CONFIG['ADMIN_ID'])

    app = Application.builder().token(BOT_CONFIG['BOT_TOKEN']).build()


    admin_filter = filters.User(user_id=ADMIN_ID)
    app.add_handler(CommandHandler(
        ["block", "unblock", "checkblock", "info", "addkw", "rmkw", "listkw_all", "listblock_all"],
        admin_command_handler,
        filters=admin_filter
    ))

    app.add_handler(MessageHandler(
        admin_filter & filters.REPLY & (~filters.COMMAND),
        handle_admin_reply
    ))

    app.add_handler(CallbackQueryHandler(verification_callback_handler, pattern="^verify_"))

    user_filter = (~admin_filter) & filters.ChatType.PRIVATE
    app.add_handler(CommandHandler("start", start_handler, filters=user_filter))
    app.add_handler(MessageHandler(
        user_filter & (~filters.COMMAND),
        check_verification_and_forward
    ))

    app.add_handler(CallbackQueryHandler(view_blocked_user_callback, pattern="^view_blocked_"))
    app.add_handler(CallbackQueryHandler(secondary_menu_callback, pattern="^(unblock_|return_to_list)"))
    app.add_handler(CallbackQueryHandler(blocked_page_callback, pattern="^blocked_page_"))

    app.post_init = set_admin_commands

    logger.info("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()