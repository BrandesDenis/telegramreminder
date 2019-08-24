# telegramreminder

A simple bot for creating telegram reminders.

The bot allows you to create one-time and recurring reminders.

You can view and edit the list of created reminders.

Usage example:

```
from telegramreminder import TelegramReminder

token = 'BOT_TOKEN'

reminder = TelegramReminder(token)
reminder.run()
```

Installation:
```
pip install git+https://github.com/BrandesDenis/telegramreminder
```

