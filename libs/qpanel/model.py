# -*- coding: utf-8 -*-

#
# Class Qpanel for Asterisk
#
# Copyright (C) 2015-2016 Rodrigo Ramírez Norambuena <a@rodrigoramirez.com>
#

from sqlalchemy import Table, Column, Integer, Text
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql import exists
from database import session_db, metadata, DeclarativeBase
import utils

# Class queue_log Table
queue_log = Table(u'queue_log', metadata,
                  Column('id', Integer, primary_key=True, nullable=False),
                  Column('time', Text),
                  Column('callid', Text),
                  Column('queuename', Text),
                  Column('agent', Text),
                  Column('event', Text),
                  Column('data', Text),
                  Column('data1', Text),
                  Column('data2', Text),
                  Column('data3', Text),
                  Column('data4', Text),
                  Column('data5', Text))


class QueueLog(DeclarativeBase):
    __table__ = queue_log
    query = session_db.query_property()

    # relation definitions
    def as_dict(self):
        return {'id': self.id,
                'time': self.time.split('.')[0],
                'callid': self.callid,
                'queuename': self.queuename,
                'agent': self.agent,
                'event': self.event,
                'data': self.data,
                'data1': self.data1,
                'data2': self.data2,
                'data3': self.data3,
                'data4': self.data4,
                'data5': self.data5}


def queuelog_event_by_range_and_types(start_date, end_date, events=None,
                                      agent=None, queue=None):
    try:
        q = session_db.query(QueueLog)
        if start_date:
            q = q.filter(QueueLog.time >= start_date)
        if end_date:
            q = q.filter(QueueLog.time <= end_date)
        if events:
            q = q.filter(QueueLog.event.in_(events))
        if agent:
            q = q.filter(QueueLog.agent.in_(agent))
        if queue:
            q = q.filter(QueueLog.queuename == queue)
        return q.order_by(QueueLog.id.asc()).all()
    except NoResultFound, e:
        print(e)
        return None


def queuelog_count_answered(start_date, end_date, agent=None, queue=None):
    events = ['CONNECT']
    data = queuelog_event_by_range_and_types(start_date, end_date, events,
                                             agent, queue)
    return len(data)


def queuelog_count_inbound(start_date, end_date, agent=None, queue=None):
    events = ['ENTERQUEUE']
    calls = []
    data = queuelog_event_by_range_and_types(start_date, end_date, events,
                                             agent, queue)

    for call in data:
        if call.callid not in calls:
            calls.append(call.callid)
    return len(calls)


def queuelog_count_abandon(start_date, end_date, agent=None, queue=None):
    events = ['ABANDON']
    data = queuelog_event_by_range_and_types(start_date, end_date, events,
                                             agent, queue)
    return len(data)


def queuelog_seconds_wait_abandon(start_date, end_date, agent=None,
                                  queue=None):
    events = ['ABANDON']
    seconds = 0
    data = queuelog_event_by_range_and_types(start_date, end_date, events,
                                             agent, queue)
    for call in data:
        seconds = seconds + int(call.data3)
    return seconds


def queuelog_seconds_wait(start_date, end_date, agent=None, queue=None):
    events = ['CONNECT']
    seconds = 0
    data = queuelog_event_by_range_and_types(start_date, end_date, events,
                                             agent, queue)
    for call in data:
        seconds = seconds + int(call.data1)
    return seconds


def queuelog_seconds_talking(start_date, end_date, agent=None, queue=None):
    events = ['COMPLETECALLER', 'COMPLETEAGENT']
    seconds = 0
    data = queuelog_event_by_range_and_types(start_date, end_date, events,
                                             agent, queue)
    for call in data:
        seconds = seconds + int(call.data2)
    return seconds


def parse_list_record(list):
    record = {}
    fields = ['callid', 'queuename', 'agent', 'event',
              'data1', 'data2', 'data3', 'data4', 'data5']

    # hardcore parse to date
    try:
        time = int(list[0])
        record['time'] = utils.dt(time)
    except:
        print list
        pass

    i = 1
    len_list = len(list)
    for f in fields:
        value = ''
        if i < len_list:
            value = list[i]
        record[f] = value
        i += 1
    return record


def queuelog_insert(log):
    if isinstance(log, list):
        log = parse_list_record(log)

    qlog = QueueLog()
    for val in log:
        if log[val] is not None:
            setattr(qlog, val, log[val])

    qlog.data = ''  # set backwards old compatibility

    try:
        session_db.add(qlog)
        session_db.commit()
        return True
    except Exception, e:
        print(str(e))
        return False


def queuelog_exists_record(log):
    if isinstance(log, list):  # improveme later...sure
        log = parse_list_record(log)

    return session_db.query(
               exists().where(QueueLog.time == log['time']).
               where(QueueLog.event == log['event']).
               where(QueueLog.queuename == log['queuename']).
               where(QueueLog.callid == log['callid'])
           ).scalar()
