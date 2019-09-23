import logging
from telegramreminder import TelegramReminder


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

token = '554203005:AAEfk5x1nqKuzjU2Od2se6r790II0b2pHuU'

tr = TelegramReminder(token, 'sqlite:///BASE.db', 5)
tr.run()