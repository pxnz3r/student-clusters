"""
data.py - load the prepared student table.

prepared/students.csv holds 1,655 real students of one Open University
course (module DDD, autumn 2014), one row each, built from the Open
University Learning Analytics Dataset by scripts/build_students.py.
"""

import numpy as np
import pandas as pd

PATH = "prepared/students.csv"

ATTENDANCE = "Attendance"
STUDY = "Study activity"
STUDY_LOG = "Study activity (log)"
COMPLETION = "Assignment completion"
RESULT = "Final result"

# The inputs the groups are made from. Study activity enters on a log
# scale: a few students click ten times more than most, and on the raw
# scale they would form a group of their own.
INPUTS = [ATTENDANCE, STUDY_LOG, COMPLETION]
SHOWN = [ATTENDANCE, STUDY, COMPLETION]
RESULTS = ["Distinction", "Pass", "Fail", "Withdrawn"]

DESCRIPTIONS = {
    ATTENDANCE: "Share of the 38 course weeks in which the student opened the online learning environment.",
    STUDY: "Average clicks in the online learning environment per course week.",
    COMPLETION: "Share of the six tutor-marked assignments handed in.",
}


def add_log_study(table):
    """
    Add the log-scale study activity column.

    Input:
        table: a DataFrame with the study activity column.
    Returns:
        The same DataFrame with STUDY_LOG added.
    """
    table[STUDY_LOG] = np.log10(1 + table[STUDY])
    return table


def load_students():
    """
    The student table with the log column added.

    Returns:
        A DataFrame: attendance, study activity, assignment completion,
        final result and the log column.
    """
    return add_log_study(pd.read_csv(PATH))
