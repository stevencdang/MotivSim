

import logging

import datetime as dt
import pandas as pd


logger = logging.getLogger(__name__)


class SessionCalculator:

    def __init__(self, db):
        self.db = db


    def get_student_sessions(self, sids):
        # Get login-logout transactions for students
        tx = pd.DataFrame(self.db.tutor_events.find({"stu_id": {'$in': sids}, "type": {"$in": ["SessionStart", "SessionEnd"]}}))
        ses_ids = tx['session_id'].unique().tolist()
        # Append session metadata
        sessions = pd.DataFrame(self.db.sessions.find({"_id": {'$in': ses_ids}}))
        sessions.drop(columns=['type'], inplace=True)
        sessions.rename(columns={"_id": "session_id"}, inplace=True)
        tx = pd.merge(tx, sessions, on="session_id", how='inner')
        return tx


    def calc_session_stats(self, sids):
        tx = self.get_student_sessions(sids)

        # Calc student-session stats
        session_stats = tx.pivot(index=['stu_id', 'session_id'], columns='type', values='time').reset_index()
        session_stats = pd.merge(tx.loc[:, ['stu_id', 'session_id', 'start', 'end']].drop_duplicates(), session_stats, on=['stu_id', 'session_id'])

        # Start/end speed
        session_stats['start speed'] = session_stats.apply(lambda x: (x['SessionStart'] - x['start']).total_seconds()/60, axis=1)
        session_stats['early finish'] = session_stats.apply(lambda x: (x['end'] - x['SessionEnd']).total_seconds()/60, axis=1)

        # session length
        session_stats['session length'] = session_stats.apply(lambda x: (x['SessionEnd'] - x['SessionStart']).total_seconds()/60, axis=1)
        session_stats['class length'] = session_stats.apply(lambda x: (x['end'] - x['start']).total_seconds()/60, axis=1)
        session_stats['pct class'] = session_stats['session length'] / session_stats['class length']

        return session_stats


    def calc_stu_session_stats(self, sids):
        session_stats = self.calc_session_stats(sids)
        stu_session_stats = session_stats.groupby('stu_id')[['start speed', 'early finish', 'session length', 'pct class']].agg('mean', 'std')
        stu_session_stats['total opportunity'] = session_stats.groupby('stu_id')['session length'].sum()
        return stu_session_stats


