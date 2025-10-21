import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_USERNAME = '@footagefromreallife'  # Замените на ваш канал
ADMIN_CHAT_ID = -1001234567890  # Замените на ID чата модераторов
