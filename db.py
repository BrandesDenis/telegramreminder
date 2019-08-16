import pytz
import datetime
from dateutil.relativedelta import relativedelta
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, Date, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


Base = declarative_base()


class UserInput(Base):

    __tablename__ = 'user_inputs'
    chat_id = Column(Integer, primary_key=True)
    text = Column(String)
    date = Column(Date)
    frequency = Column(String)
    
    def __init__(self, chat_id, text=None, date=None, frequency=None):
        self.chat_id = chat_id
        self.text = text
        self.date = date
        self.frequency = frequency

    def __repr__(self):
        return f'<UserInput({self.chat_id}, {self.text}, {self.date})>'


class Reminder(Base):

    __tablename__ = 'reminders'
    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, index=True)
    text = Column(String)
    datetime = Column(DateTime)
    frequency = Column(String)
    
    def __init__(self, chat_id, text, datetime, frequency):
        self.chat_id = chat_id
        self.text = text
        self.datetime = datetime
        self.frequency = frequency

    def __repr__(self):
        return f'<UserInput({self.chat_id}, {self.text}, {self.date}, {self.time})>'


def open_database(db_url):
    engine = create_engine(db_url, echo=True)
    Base.metadata.create_all(engine)

    return engine


def get_session(engine):
    Session = sessionmaker(bind=engine)
    return Session()


def session_commit(session):
    try:
        session.commit()
    finally:
        session.close()


def get_utc_time(datetime, timezone):
    return change_timezone(datetime, timezone, 'utc')


def get_local_time(datetime, timezone):
    return change_timezone(datetime, 'utc', timezone)


def change_timezone(datetime, timezone1, timezone2):
    timezone1_ = pytz.timezone(timezone1)
    timezone2_ = pytz.timezone(timezone2)

    timezone1_dt = timezone1_.localize(datetime, is_dst=None)

    return timezone1_dt.astimezone(timezone2_).replace(tzinfo=None)


def process_date(date):
    res_date = None
    now = datetime.datetime.now()
    today = datetime.datetime(now.year, now.month, now.day)
    if type(date) == str:
        date = date.lower()
        if date == 'сегодня':
            res_date = today
        elif date == 'завтра':
            res_date = today + relativedelta(days=1)
        elif date == 'послезавтра':
            res_date = today + relativedelta(days=2)   
    else:
        if date >= today:
            res_date = date
        
    return res_date


def process_time(time_str):
    time = time_str.strip()
    time = time.split(':')
    if len(time) == 1:
        time = time[0].split(' ')
    
    minutes = 0
    hours = 0
    try:
        hours = int(time[0])
        if len(time) > 1: 
            minutes = int(time[1])
    except:
        return None

    return datetime.timedelta(hours=hours, minutes=minutes)

def set_user_input(engine, chat_id, input_data, timezone=None, frequency=False):
    if frequency:
        clear_user_input(engine, chat_id)
    
    session = get_session(engine)
    if frequency:
        user_input = UserInput(chat_id=chat_id, frequency=input_data)
        session.add(user_input)
        session_commit(session)

        return -1

    user_input = session.query(UserInput).filter_by(chat_id=chat_id).first()
    if user_input == None:
        user_input = UserInput(chat_id=chat_id)
        session.add(user_input)

    if user_input.text == None:
        user_input.text = input_data
        state = 0    
    elif user_input.date == None:
        res_date = process_date(input_data)
        if res_date != None:
            user_input.date = process_date(input_data)
            state = 1
        else:
            state = 0    
    else:
        state = 1
        res_time = process_time(input_data)
        if res_time != None and timezone != None:
            date = datetime.datetime(user_input.date.year, user_input.date.month, user_input.date.day) + res_time
            date = get_utc_time(date, timezone)

            if date > datetime.datetime.utcnow():
                state = 2
                session.delete(user_input)
                
    if state == 2:          
        reminder = Reminder(chat_id = chat_id, text = user_input.text,
                            datetime = date, frequency=user_input.frequency)
                            
        session.add(reminder)
        
    session_commit(session)

    return state


def clear_user_input(engine, chat_id):
    session = get_session(engine)
    session.query(UserInput).filter_by(chat_id=chat_id).delete()
    session_commit(session)


def get_reminders(engine, timezone, upcoming=True):
    session = get_session(engine)

    if upcoming: 
        now = datetime.datetime.utcnow()
        reminders = session.query(Reminder).filter(Reminder.datetime < now).order_by(Reminder.datetime)
    else:
        reminders = session.query(Reminder).order_by(Reminder.datetime)

    for reminder in reminders:
        reminder.datetime = get_local_time(reminder.datetime, timezone)
        yield reminder


def delete_reminder(engine, id):
    session = get_session(engine)
    session.query(Reminder).filter_by(id=id).delete()
    session_commit(session)


def move_reccuring_reminder(engine, id):
    session = get_session(engine)
    reminder = session.query(Reminder).filter_by(id=id).first()
    
    if reminder != None:
        if reminder.frequency =='DAY':
                timedelta = relativedelta(days=1)
        elif reminder.frequency =='WEEK':
                timedelta = relativedelta(days=7)
        elif reminder.frequency =='MONTH':
                timedelta = relativedelta(months=1)

        reminder.datetime += timedelta

        session_commit(session)
