import datetime
import calendar
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def create_callback_data(action, year=0, month=0, day=0):
    return ";".join([action, str(year), str(month), str(day)])


def create_calendar(year=None, month=None):
    now = datetime.datetime.now()

    if year is None:
        year = now.year
    if month is None:
        month = now.month

    curr_month = False
    if year == now.year and month == now.month:
        curr_month = True

    now_day = now.day

    ignore_callback = create_callback_data(action="IGNORE")

    keyboard = []
    
    # month and year
    row = []
    row.append(InlineKeyboardButton(calendar.month_name[month] + " " + str(year),
               callback_data=ignore_callback))
    keyboard.append(row)

    # week days
    row = []
    for day in ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]:
        row.append(InlineKeyboardButton(day, callback_data=ignore_callback))
    keyboard.append(row)

    my_calendar = calendar.monthcalendar(year, month)
    for week in my_calendar:
        row = []
        week_has_day = False
        for day in week:
            if (curr_month and day < now_day) or day == 0:
                row.append(InlineKeyboardButton(" ", callback_data=ignore_callback))
            else:
                week_has_day = True
                row.append(InlineKeyboardButton(day,
                           callback_data=create_callback_data("DAY", year, month, day)))
        if week_has_day:
            keyboard.append(row)

    # Buttons
    row = []
    prev_callback = create_callback_data("PREV-MONTH", year, month, day)
    row.append(InlineKeyboardButton("<", callback_data=prev_callback))

    row.append(InlineKeyboardButton(" ", callback_data=ignore_callback))

    next_callback = create_callback_data("NEXT-MONTH", year, month, day)
    row.append(InlineKeyboardButton(">", callback_data=next_callback))

    keyboard.append(row)

    # today, tomorrow, aftertomorrow
    row = []
    today_callback = create_callback_data("DAY_rel", 0, 0, 'today')
    row.append(InlineKeyboardButton('today', callback_data=today_callback))

    tomorrow_callback = create_callback_data("DAY_rel", 0, 0, 'tomorrow')
    row.append(InlineKeyboardButton('tomorrow', callback_data=tomorrow_callback))

    aftertomorrow_callback = create_callback_data("DAY_rel", 0, 0, 'aftertomorrow')
    row.append(InlineKeyboardButton('after tom', callback_data=aftertomorrow_callback))

    keyboard.append(row)

    return InlineKeyboardMarkup(keyboard)


def process_selection(bot, update):
    day_selected = False
    res_data = None

    query = update.callback_query
    (action, year, month, day) = query.data.split(';')

    if action == 'DAY_rel':
        res_data = day
    else:
        selected_month = datetime.datetime(int(year), int(month), 1)

        now = datetime.datetime.now()
        curr_month = datetime.datetime(int(now.year), int(now.month), 1)

    if action == "IGNORE":
        bot.answer_callback_query(callback_query_id=query.id)
    elif action == "DAY" or action == "DAY_rel":
        bot.edit_message_text(text=query.message.text,
                              chat_id=query.message.chat_id,
                              message_id=query.message.message_id)
        if action == "DAY":
            res_data = datetime.datetime(int(year), int(month), int(day))
         day_selected = True
    elif action == "PREV-MONTH":
        prev_month = selected_month - datetime.timedelta(days=1)
        if prev_month >= curr_month:
            bot.edit_message_text(text=query.message.text,
                                  chat_id=query.message.chat_id,
                                  message_id=query.message.message_id,
                                  reply_markup=create_calendar(int(prev_month.year), int(prev_month.month)))
    elif action == "NEXT-MONTH":
        next_month = selected_month + datetime.timedelta(days=31)
        bot.edit_message_text(text=query.message.text,
                              chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              reply_markup=create_calendar(int(next_month.year), int(next_month.month)))
  
    return day_selected, res_data
