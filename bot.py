import logging
from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup
)
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    CallbackQueryHandler, 
    ContextTypes, 
    filters
)
import requests
from config import BOT_TOKEN, CHANNEL_USERNAME, ADMIN_CHAT_ID

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Хранение данных пользователей (в продакшене используйте БД)
user_data = {}

# Клавиатура для подтверждения
confirm_keyboard = [
    [KeyboardButton("✅ Да, отправить"), KeyboardButton("🔄 Заполнить заново")]
]
confirm_markup = ReplyKeyboardMarkup(confirm_keyboard, resize_keyboard=True)

# Список разрешенных тегов
ALLOWED_TAGS = [
    "#городская_геометрия",
    "#уличное_настроение", 
    "#природная_эстетика",
    "#интерьер_и_уют",
    "#ночная_магия",
    "#монохром"
]

async def check_subscription(user_id: int) -> bool:
    """Проверяет подписку пользователя на канал"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getChatMember"
        params = {
            'chat_id': CHANNEL_USERNAME,
            'user_id': user_id
        }
        response = requests.get(url, params=params)
        result = response.json()
        
        if result['ok']:
            status = result['result']['status']
            return status in ['member', 'administrator', 'creator']
        return False
    except Exception as e:
        logging.error(f"Ошибка проверки подписки: {e}")
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user_id = update.effective_user.id
    
    # Проверка подписки
    if not await check_subscription(user_id):
        keyboard = [
            [InlineKeyboardButton("📢 Подписаться на канал", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
            [InlineKeyboardButton("✅ Я подписался", callback_data="check_subscription")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "❌ **Для использования бота необходимо быть подписчиком нашего канала!**\n\n"
            "📢 **Кадры из жизни. Повседневная эстетика** - сообщество любителей мобильной фотографии.\n\n"
            "👉 Подпишитесь на канал и нажмите «✅ Я подписался»",
            reply_markup=reply_markup
        )
        return
    
    # Пользователь подписан
    await show_main_menu(update, context)

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает главное меню"""
    welcome_text = (
        "📸 **Добро пожаловать в бот «Кадры из жизни. Повседневная эстетика»!**\n\n"
        "Я помогу вам отправить ваше фото с прогулки на модерацию.\n\n"
        "📋 **Процесс простой:**\n"
        "1. Вы отправляете фото\n"
        "2. Отвечаете на 4 коротких вопроса\n"
        "3. Ваша заявка поступает к модераторам\n\n"
        "🎯 **Требования к фото:**\n"
        "• Снято на смартфон\n"
        "• Соответствует эстетике канала\n"
        "• Хорошее качество и композиция\n\n"
        "➡️ **Чтобы начать, просто отправьте ваше фото!**"
    )
    
    if update.callback_query:
        await update.callback_query.message.reply_text(welcome_text)
    else:
        await update.message.reply_text(welcome_text)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик получения фото"""
    user_id = update.effective_user.id
    
    # Проверка подписки
    if not await check_subscription(user_id):
        await show_subscription_required(update)
        return
    
    # Сохраняем фото
    photo_file = await update.message.photo[-1].get_file()
    user_data[user_id] = {
        'photo_file_id': photo_file.file_id,
        'step': 'phone_model'
    }
    
    await update.message.reply_text(
        "📱 **На какую модель телефона снято фото?**\n\n"
        "Примеры:\n"
        "• iPhone 15 Pro Max\n"
        "• Samsung Galaxy S23 Ultra\n"  
        "• Xiaomi Redmi Note 12\n"
        "• Google Pixel 7\n"
        "• Huawei P60 Pro\n\n"
        "➡️ Напишите модель вашего смартфона:"
    )

async def handle_phone_model(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик модели телефона"""
    user_id = update.effective_user.id
    
    if user_id not in user_data or user_data[user_id]['step'] != 'phone_model':
        await update.message.reply_text("❌ Пожалуйста, сначала отправьте фото")
        return
    
    user_data[user_id]['phone_model'] = update.message.text
    user_data[user_id]['step'] = 'location'
    
    await update.message.reply_text(
        "📍 **Где было сделано фото?**\n\n"
        "Напишите место съемки кратко:\n"
        "• «Центральный парк, аллея у фонтана»\n"
        "• «Тихий двор в центре города»\n"
        "• «Набережная реки, вечер»"
    )

async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик локации"""
    user_id = update.effective_user.id
    
    if user_id not in user_data or user_data[user_id]['step'] != 'location':
        await update.message.reply_text("❌ Пожалуйста, начните с отправки фото")
        return
    
    user_data[user_id]['location'] = update.message.text
    user_data[user_id]['step'] = 'description'
    
    await update.message.reply_text(
        "📝 **Опишите фото или ваше настроение:**\n\n"
        "Примеры:\n"
        "• «Утро, первый снег, пустынные улицы»\n"
        "• «Кофейня с панорамными окнами, чувство уюта»\n"  
        "• «Грусть осеннего дня»"
    )

async def handle_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик описания"""
    user_id = update.effective_user.id
    
    if user_id not in user_data or user_data[user_id]['step'] != 'description':
        await update.message.reply_text("❌ Пожалуйста, начните с отправки фото")
        return
    
    user_data[user_id]['description'] = update.message.text
    user_data[user_id]['step'] = 'tag'
    
    # Показываем кнопки с тегами
    tag_buttons = [[InlineKeyboardButton(tag, callback_data=f"tag_{tag}")] for tag in ALLOWED_TAGS]
    reply_markup = InlineKeyboardMarkup(tag_buttons)
    
    await update.message.reply_text(
        "🏷️ **Выберите основной тег для фото:**\n\n"
        "• #городская_геометрия - линии, архитектура, паттерны\n"
        "• #уличное_настроение - эмоции, люди, моменты\n"
        "• #природная_эстетика - парки, деревья, вода, небо\n"
        "• #интерьер_и_уют - кафе, дома, детали\n"
        "• #ночная_магия - вечер, огни, сумерки\n"
        "• #монохром - черно-белые фото",
        reply_markup=reply_markup
    )

async def handle_tag_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик выбора тега"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if user_id not in user_data:
        await query.message.reply_text("❌ Сессия устарела. Начните с /start")
        return
    
    tag = query.data.replace('tag_', '')
    user_data[user_id]['tag'] = tag
    user_data[user_id]['step'] = 'confirmation'
    
    # Показываем подтверждение
    user_info = user_data[user_id]
    confirmation_text = (
        "✅ **Отлично! Ваша заявка собрана:**\n\n"
        f"📱 **Телефон:** {user_info['phone_model']}\n"
        f"📍 **Место:** {user_info['location']}\n"
        f"📝 **Описание:** {user_info['description']}\n"
        f"🏷️ **Тег:** {tag}\n\n"
        "❓ **Всё верно? Отправляем на модерацию?**"
    )
    
    await query.message.reply_text(
        confirmation_text,
        reply_markup=confirm_markup
    )

async def handle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик подтверждения"""
    user_id = update.effective_user.id
    text = update.message.text
    
    if user_id not in user_data:
        await update.message.reply_text("❌ Сессия устарела. Начните с /start")
        return
    
    if text == "✅ Да, отправить":
        # Отправляем на модерацию
        await send_to_moderation(update, context, user_id)
    elif text == "🔄 Заполнить заново":
        # Сбрасываем данные
        user_data[user_id]['step'] = 'restart'
        await update.message.reply_text(
            "🔄 Хорошо, начнем заполнение заново!\n\n"
            "➡️ Просто отправьте ваше фото:",
            reply_markup=None
        )

async def send_to_moderation(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Отправляет заявку в чат модераторов"""
    user_info = user_data[user_id]
    username = update.effective_user.username or "Без username"
    
    moderation_text = (
        f"🆕 НОВАЯ ЗАЯВКА #{user_id}\n\n"
        f"👤 **Автор:** @{username} (ID: {user_id})\n"
        f"📱 **Телефон:** {user_info['phone_model']}\n"
        f"📍 **Локация:** {user_info['location']}\n"
        f"📝 **Описание:** {user_info['description']}\n"
        f"🏷️ **Тег:** {user_info['tag']}\n"
    )
    
    # Клавиатура для модераторов
    keyboard = [
        [
            InlineKeyboardButton("✅ Одобрить", callback_data=f"approve_{user_id}"),
            InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{user_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Отправляем фото с текстом
    await context.bot.send_photo(
        chat_id=ADMIN_CHAT_ID,
        photo=user_info['photo_file_id'],
        caption=moderation_text,
        reply_markup=reply_markup
    )
    
    # Уведомляем пользователя
    await update.message.reply_text(
        "📨 **Ваша заявка отправлена на модерацию!**\n\n"
        "Обычно проверка занимает от 1 до 24 часов. "
        "Вы получите уведомление о результате.\n\n"
        "Спасибо за участие! ✨",
        reply_markup=None
    )
    
    # Очищаем данные пользователя
    user_data.pop(user_id, None)

async def handle_moderation_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик действий модераторов"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = int(data.split('_')[1])
    
    if data.startswith('approve'):
        # Одобрение
        await context.bot.send_message(
            chat_id=user_id,
            text="🎉 **Отличные новости! Ваше фото одобрено модераторами и скоро будет опубликовано в канале «Кадры из жизни. Повседневная эстетика»!**\n\n"
                 "Следите за публикациями! ✨\n\n"
                 "Хотите отправить еще одно фото? Просто пришлите его! 📸"
        )
        await query.edit_message_caption(caption=f"✅ ОДОБРЕНО: {query.message.caption}")
        
    elif data.startswith('reject'):
        # Отклонение
        await context.bot.send_message(
            chat_id=user_id,
            text="😔 **К сожалению, ваше фото не подошло для публикации.**\n\n"
                 "Это могло произойти по нескольким причинам:\n"
                 "• Не соответствует тематике канала\n"
                 "• Низкое качество изображения\n"
                 "• Нарушение правил\n\n"
                 "Не расстраивайтесь! Попробуйте отправить другую фотографию 📸"
        )
        await query.edit_message_caption(caption=f"❌ ОТКЛОНЕНО: {query.message.caption}")

async def handle_check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка подписки после нажатия кнопки"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if await check_subscription(user_id):
        await show_main_menu(update, context)
    else:
        await query.message.reply_text(
            "❌ **Вы еще не подписались на канал!**\n\n"
            "Пожалуйста, подпишитесь и нажмите кнопку еще раз.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ Я подписался", callback_data="check_subscription")
            ]])
        )

async def show_subscription_required(update: Update):
    """Показывает сообщение о необходимости подписки"""
    keyboard = [
        [InlineKeyboardButton("📢 Подписаться на канал", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
        [InlineKeyboardButton("✅ Я подписался", callback_data="check_subscription")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "❌ **Для использования бота необходимо быть подписчиком нашего канала!**\n\n"
        "📢 **Кадры из жизни. Повседневная эстетика** - сообщество любителей мобильной фотографии.\n\n"
        "👉 Подпишитесь на канал и нажмите «✅ Я подписался»",
        reply_markup=reply_markup
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    user_id = update.effective_user.id
    
    # Проверяем подписку для любого сообщения
    if not await check_subscription(user_id):
        await show_subscription_required(update)
        return
    
    # Определяем текущий шаг пользователя
    current_step = user_data.get(user_id, {}).get('step', 'start')
    
    if current_step == 'phone_model':
        await handle_phone_model(update, context)
    elif current_step == 'location':
        await handle_location(update, context)
    elif current_step == 'description':
        await handle_description(update, context)
    elif current_step == 'confirmation':
        await handle_confirmation(update, context)
    else:
        await update.message.reply_text("📸 Отправьте фото чтобы начать!")

def main():
    """Запуск бота"""
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Обработчики команд
    application.add_handler(CommandHandler("start", start))
    
    # Обработчики callback-запросов
    application.add_handler(CallbackQueryHandler(handle_tag_selection, pattern="^tag_"))
    application.add_handler(CallbackQueryHandler(handle_moderation_action, pattern="^(approve|reject)_"))
    application.add_handler(CallbackQueryHandler(handle_check_subscription, pattern="^check_subscription$"))
    
    # Обработчики сообщений
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Запуск бота
    application.run_polling()

if __name__ == '__main__':
    main()
