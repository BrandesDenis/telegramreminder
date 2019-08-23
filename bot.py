import pytz
from . import db
from . import telegramcalendar
from .language import translate
from telegram import ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CallbackQueryHandler, MessageHandler, Filters, RegexHandler, CommandHandler


class TelegramReminder:

    def __init__(self, token, db_url='sqlite:///BASE.db', interval=5):
        self._token = token
        self._interval = interval

        self._set_db_engine(db_url)

        self.updater = Updater(token=token)
        self.dispatcher = self.updater.dispatcher

        self.scheduler = self.updater.job_queue
        self.scheduler.run_repeating(self._send_reminders, interval=self._interval)

        self._add_handlers()

    def _set_db_engine(self, db_url):
        self.db_engine = db.open_database(db_url)

    def _add_handlers(self):
        start = CommandHandler('start', self._start)
        self.dispatcher.add_handler(start)

        cancel = RegexHandler(r'^\s*(?:Отмена|Cancel)\s*', self._cancel)
        self.dispatcher.add_handler(cancel)

        menu = RegexHandler(r'^\s*(?:Меню|Menu)\s*', self._menu)
        self.dispatcher.add_handler(menu)

        settings = CallbackQueryHandler(self._settings,
                                        pattern=r'^GETSETTINGS;.*')
        self.dispatcher.add_handler(settings)

        settings_action = CallbackQueryHandler(self._settings_action,
                                               pattern=r'^SETTINGS;.*')
        self.dispatcher.add_handler(settings_action)

        new_reminder_action = CallbackQueryHandler(self._new_reminder_action,
                                                   pattern=r'^NEW_REMINDER;.*')
        self.dispatcher.add_handler(new_reminder_action)

        reminders_list = CallbackQueryHandler(self._reminders_list,
                                              pattern=r'^REMINDER_LIST;.*')
        self.dispatcher.add_handler(reminders_list)

        recurring_action = CallbackQueryHandler(self._recurring_action,
                                                pattern=r'^RECCURING;.*')
        self.dispatcher.add_handler(recurring_action)

        reminder_actions = CallbackQueryHandler(self._reminder_actions,
                                                pattern=r'^REMINDER;.*')
        self.dispatcher.add_handler(reminder_actions)

        calendar_pattern = r'^(?:IGNORE|DAY|PREV|NEXT).*'
        calendar_actions = CallbackQueryHandler(self._calendar_actions,
                                                pattern=calendar_pattern)
        self.dispatcher.add_handler(calendar_actions)  

        move_reminder = CallbackQueryHandler(self._move_reminder,
                                             pattern=r'^MOVE;.*')   
        self.dispatcher.add_handler(move_reminder)

        del_reminder = CallbackQueryHandler(self._del_reminder,
                                            pattern=r'^DEL;.*')   
        self.dispatcher.add_handler(del_reminder)

        process_message = MessageHandler(Filters.text, self._process_message)
        self.dispatcher.add_handler(process_message)

    def _get_default_keyboard(self, chat_id):

        lang = db.UserSettings.get_user_settings(self.db_engine, chat_id, 'language')

        button_new_reminder = InlineKeyboardButton(translate('newReminder', lang) + ' 🕭', callback_data='NEW_REMINDER;')
        button_new_recc_reminder = InlineKeyboardButton(translate('newRecReminder', lang) + ' ♲', callback_data='NEW_REMINDER;RECC')
        button_reminders_list = InlineKeyboardButton(translate('remindersList', lang) + ' 🗓', callback_data='REMINDER_LIST;')

        reply_markup = InlineKeyboardMarkup([
            [button_new_reminder],
            [button_new_recc_reminder],
            [button_reminders_list],
            ])

        return reply_markup

    @staticmethod
    def _get_callback_data(data_str):
        sep_position = data_str.find(';')
        data = data_str[sep_position+1:]
        return data.split(';')
        
    def _start(self, bot, update):
        chat_id = update.message.chat_id
        lang = db.UserSettings.get_user_settings(self.db_engine, chat_id, 'language')

        text = translate('hello', lang)
        reply_markup = self._get_default_keyboard(chat_id)

        button_settings = InlineKeyboardButton(translate('settings', lang) + ' ⛭', callback_data='GETSETTINGS;')
        reply_markup.inline_keyboard.append([button_settings])

        bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)

    def _settings(self, bot, update):
        chat_id = update.callback_query.from_user.id
        lang = db.UserSettings.get_user_settings(self.db_engine, chat_id, 'language')
        
        button_language = InlineKeyboardButton(translate('lang', lang), callback_data='SETTINGS;LANG')
        button_timezone = InlineKeyboardButton(translate('timezone', lang), callback_data='SETTINGS;TIMEZONE')

        reply_markup = InlineKeyboardMarkup([
            [button_language],
            [button_timezone],
            ])

        text = translate('settings', lang)
        bot.answer_callback_query(callback_query_id=update.callback_query.id)
        bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)

    def _settings_action(self, bot, update):
        chat_id = update.callback_query.from_user.id
        lang = db.UserSettings.get_user_settings(self.db_engine, chat_id, 'language')
        reminder_data = TelegramReminder._get_callback_data(update.callback_query.data)

        settings_name = reminder_data[0]
        if len(reminder_data) == 1:
            if settings_name == 'LANG':
                text = translate('chooseLang', lang)
                button_eng = InlineKeyboardButton('ENG', callback_data='SETTINGS;LANG;ENG')
                button_rus = InlineKeyboardButton('RUS', callback_data='SETTINGS;LANG;RUS')
                keyboard = [[button_eng], [button_rus]]
            elif settings_name == 'TIMEZONE':
                text = translate('chooseTimezone', lang)
                keyboard = []
                row = []
                timezones = [tz for tz in pytz.all_timezones if 'Etc/GMT' in tz]
                for i, timezine in enumerate(timezones):
                    if i % 3 == 0:
                        keyboard.append(row)
                        row = []
                    button = InlineKeyboardButton(timezine.replace('Etc/', ''), 
                                                  callback_data='SETTINGS;TIMEZONE;' + timezine)
                    row.append(button)
                keyboard.append(row)
            
            reply_markup = InlineKeyboardMarkup(keyboard)

        else:
            settings_value = reminder_data[1]

            if settings_name == 'LANG':
                db.UserSettings.set_user_settings(self.db_engine, chat_id, language=settings_value)
                lang = db.UserSettings.get_user_settings(self.db_engine, chat_id, 'language')
                text = translate('langChanged', lang)
            elif settings_name == 'TIMEZONE':
                db.UserSettings.set_user_settings(self.db_engine, chat_id, timezone=settings_value)
                text = translate('timezoneChanged', lang)

            reply_markup = ReplyKeyboardRemove() 

        bot.answer_callback_query(callback_query_id=update.callback_query.id)
        bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)
    
    def _new_reminder_action(self, bot, update):
        chat_id = update.callback_query.from_user.id
        lang = db.UserSettings.get_user_settings(self.db_engine, chat_id, 'language')
        reminder_data = TelegramReminder._get_callback_data(update.callback_query.data)

        if reminder_data[0] == 'RECC':
            button_day = InlineKeyboardButton(translate('recDay', lang), callback_data='RECCURING;DAY')
            button_week = InlineKeyboardButton(translate('recWeek', lang), callback_data='RECCURING;WEEK')
            button_month = InlineKeyboardButton(translate('recMonth', lang), callback_data='RECCURING;MONTH')

            reply_markup = InlineKeyboardMarkup([[button_day], [button_week], [button_month]])
            reply_text = translate('chooseRec', lang)
        else:
            reply_markup = None
            reply_text = translate('setTitle', lang)

        bot.answer_callback_query(callback_query_id=update.callback_query.id)
        bot.send_message(chat_id=chat_id, text=reply_text, reply_markup=reply_markup)

    def _recurring_action(self, bot, update):
        chat_id = update.callback_query.from_user.id
        lang = db.UserSettings.get_user_settings(self.db_engine, chat_id, 'language')
        recurring_data = update.callback_query.data.replace('RECCURING;', '')

        db.UserInput.set_user_input(self.db_engine, chat_id, recurring_data, frequency=True)
        bot.answer_callback_query(callback_query_id=update.callback_query.id)
        bot.send_message(chat_id=chat_id, text=translate('setTitle', lang),
                         reply_markup=ReplyKeyboardRemove())

    def _reminders_list(self, bot, update):
        chat_id = update.callback_query.from_user.id
        lang = db.UserSettings.get_user_settings(self.db_engine, chat_id, 'language')

        keyboard = []
        for reminder in db.Reminder.get_reminders(self.db_engine, False):
            freq_str = '' if reminder.frequency is None else reminder.frequency
            time_str = reminder.datetime.strftime('%d.%m.%y %H:%M')
           
            button_text = f'{reminder.text} {time_str} {freq_str}'
            reccuring = reminder.frequency is not None
            callback_data = f'REMINDER;{reminder.id};{reminder.text};{int(reccuring)}'

            button = InlineKeyboardButton(button_text, callback_data=callback_data)
            keyboard.append([button])    
        if len(keyboard):
            reply_markup = InlineKeyboardMarkup(keyboard)
            reply_text = translate('remindersList', lang)
        else:
            reply_text = translate('remindersListEmpty', lang)
            reply_markup = self._get_default_keyboard(chat_id)

        bot.answer_callback_query(callback_query_id=update.callback_query.id)
        bot.send_message(chat_id=chat_id, text=reply_text, reply_markup=reply_markup)

    def _reminder_actions(self, bot, update):
        chat_id = update.callback_query.from_user.id
        lang = db.UserSettings.get_user_settings(self.db_engine, chat_id, 'language')
        reminder_data = TelegramReminder._get_callback_data(update.callback_query.data)

        reminder_id = reminder_data[0]
        reminder_text = reminder_data[1]
        reccuring = reminder_data[2]

        callback_data = f'MOVE;{reminder_id};{reminder_text};{reccuring}'
        button_move = InlineKeyboardButton(translate('changeTime', lang), callback_data=callback_data)

        button_del = InlineKeyboardButton(translate('delete', lang), callback_data='DEL;' + reminder_id)

        reply_markup = InlineKeyboardMarkup([[button_move, button_del]])

        bot.answer_callback_query(callback_query_id=update.callback_query.id)
        bot.send_message(chat_id=chat_id, text=reminder_text,
                         reply_markup=reply_markup)

    def _cancel(self, bot, update):
        chat_id = update.message.chat_id
        lang = db.UserSettings.get_user_settings(self.db_engine, chat_id, 'language')
        db.UserInput.clear_user_input(self.db_engine, chat_id)

        reply_text = translate('actionCanceled', lang)
        reply_markup = self._get_default_keyboard(chat_id)
    
        bot.send_message(chat_id=chat_id, text=reply_text, reply_markup=reply_markup)

    def _menu(self, bot, update):
        chat_id = update.message.chat_id

        reply_markup = self._get_default_keyboard(chat_id)
        bot.send_message(chat_id=chat_id, text='Меню:', reply_markup=reply_markup)

    def _process_input_data(self, bot, chat_id, message_data):
        status = db.UserInput.set_user_input(self.db_engine, chat_id, message_data)
        lang = db.UserSettings.get_user_settings(self.db_engine, chat_id, 'language')
        
        if status == 0:
            reply_text = translate('setDate', lang)
            reply_markup = telegramcalendar.create_calendar()
        elif status == 1:
            reply_text = translate('setTime', lang)
            reply_markup = ReplyKeyboardRemove()
        elif status == 2:
            reply_text = translate('remSaved', lang)
            reply_markup = self._get_default_keyboard(chat_id)

        bot.send_message(chat_id=chat_id, text=reply_text, reply_markup=reply_markup)

    def _process_message(self, bot, update):
        chat_id = update.message.chat_id
        message_text = update.message.text

        self._process_input_data(bot, chat_id, message_text)

    def _calendar_actions(self, bot, update):
        selected, date = telegramcalendar.process_selection(bot, update)
        if selected:
            chat_id = update.callback_query.from_user.id
            self._process_input_data(bot, chat_id, date)

    def _move_reminder(self, bot, update):
        chat_id = update.callback_query.from_user.id
        reminder_data = TelegramReminder._get_callback_data(update.callback_query.data)

        reminder_id = int(reminder_data[0])
        reminder_text = reminder_data[1]
        reccuring = reminder_data[2]

        db.UserInput.clear_user_input(self.db_engine, chat_id)
        if reccuring == '0':
            db.Reminder.delete_reminder(self.db_engine, reminder_id)

        bot.answer_callback_query(callback_query_id=update.callback_query.id)
        self._process_input_data(bot, chat_id, reminder_text)

    def _del_reminder(self, bot, update):
        chat_id = update.callback_query.from_user.id
        lang = db.UserSettings.get_user_settings(self.db_engine, chat_id, 'language')
        reminder_id = update.callback_query.data.replace('DEL;', '')

        db.Reminder.delete_reminder(self.db_engine, reminder_id)
        reply_markup = self._get_default_keyboard(chat_id)
        bot.answer_callback_query(callback_query_id=update.callback_query.id)
        bot.send_message(chat_id=chat_id, text=translate('remDeleted', lang),
                         reply_markup=reply_markup)       

    def _send_reminders(self, bot, update):
        for reminder in db.Reminder.get_reminders(self.db_engine):
            reccuring = reminder.frequency is not None
           
            lang = db.UserSettings.get_user_settings(self.db_engine, reminder.chat_id, 'language')
            callback_data = f'MOVE;{reminder.id};{reminder.text};{int(reccuring)}'
            button = InlineKeyboardButton(translate('postpone', lang), callback_data=callback_data)
            reply_markup = InlineKeyboardMarkup([[button]])

            bot.send_message(chat_id=reminder.chat_id, text=reminder.text, reply_markup=reply_markup)

            if reccuring:
                db.Reminder.move_reccuring_reminder(self.db_engine, reminder.id)    
            else:
                db.Reminder.delete_reminder(self.db_engine, reminder.id)
                
    def run(self):
        self.updater.start_polling()
