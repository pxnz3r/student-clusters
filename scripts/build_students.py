"""
build_students.py - build students.csv from the Open University Learning
Analytics Dataset (OULAD). Run it once from the project folder:

    python scripts/build_students.py

The raw download is 47 MB zipped and 450 MB unzipped, too big for the
hosted app, so this keeps one course presentation (module DDD, autumn
2014) and boils each student down to one row. The result is committed in
prepared/students.csv; main.py and the app read that file.

Each student gets:
    attendance: share of course weeks in which they opened the online
        learning environment at least once,
    study activity: average clicks in the learning environment per week,
    assignment completion: share of the six tutor-marked assignments they
        handed in,
    final result: Distinction, Pass, Fail or Withdrawn (kept aside to
        check the groups, never used to make them).
"""

import math
import os
import urllib.request
import zipfile

import pandas as pd

URL = "https://archive.ics.uci.edu/static/public/349/open+university+learning+analytics+dataset.zip"
ZIP_PATH = os.path.join("data", "oulad.zip")
OUTPUT = os.path.join("prepared", "students.csv")
MODULE = "DDD"
PRESENTATION = "2014J"


def download():
    """
    Download the zip into data/ unless it is already there.

    Returns:
        Nothing.
    """
    if os.path.isfile(ZIP_PATH):
        return
    os.makedirs("data", exist_ok=True)
    print("Downloading OULAD (47 MB)...")
    urllib.request.urlretrieve(URL, ZIP_PATH)


def course_rows(archive, name, **read_options):
    """
    The rows of one OULAD table that belong to the chosen presentation.

    Inputs:
        archive: the open zip file.
        name: the CSV name inside the zip.
        read_options: extra options for pandas.read_csv.
    Returns:
        A DataFrame.
    """
    # OULAD writes missing values as "?".
    chunks = pd.read_csv(archive.open(name), chunksize=1_000_000, na_values="?", **read_options)
    keep = [chunk[(chunk["code_module"] == MODULE) & (chunk["code_presentation"] == PRESENTATION)] for chunk in chunks]
    return pd.concat(keep, ignore_index=True)


def build():
    """
    Build and save the one-row-per-student table.

    Returns:
        The table.
    """
    archive = zipfile.ZipFile(ZIP_PATH)
    courses = pd.read_csv(archive.open("courses.csv"))
    length = int(
        courses.loc[
            (courses["code_module"] == MODULE) & (courses["code_presentation"] == PRESENTATION),
            "module_presentation_length",
        ].iloc[0]
    )
    weeks = math.ceil(length / 7)

    info = course_rows(archive, "studentInfo.csv")
    registration = course_rows(archive, "studentRegistration.csv")
    # Students who left before the course started never took part.
    left_early = registration.loc[registration["date_unregistration"] <= 0, "id_student"]
    students = info[~info["id_student"].isin(left_early)][["id_student", "final_result"]].copy()

    vle = course_rows(
        archive, "studentVle.csv", usecols=["code_module", "code_presentation", "id_student", "date", "sum_click"]
    )
    vle = vle[(vle["date"] >= 0) & (vle["date"] < length)]
    vle["week"] = vle["date"] // 7
    weeks_active = vle.groupby("id_student")["week"].nunique()
    clicks = vle.groupby("id_student")["sum_click"].sum()

    assessments = pd.read_csv(archive.open("assessments.csv"))
    assignments = assessments[
        (assessments["code_module"] == MODULE)
        & (assessments["code_presentation"] == PRESENTATION)
        & (assessments["assessment_type"] == "TMA")
    ]["id_assessment"]
    submitted = pd.read_csv(archive.open("studentAssessment.csv"), na_values="?")
    submitted = submitted[submitted["id_assessment"].isin(assignments)].groupby("id_student")["id_assessment"].nunique()

    ids = students["id_student"]
    students["Attendance"] = (ids.map(weeks_active).fillna(0) / weeks).round(3).values
    students["Study activity"] = (ids.map(clicks).fillna(0) / weeks).round(1).values
    students["Assignment completion"] = (ids.map(submitted).fillna(0) / len(assignments)).round(3).values
    students = students.rename(columns={"final_result": "Final result"})
    students = students[["Attendance", "Study activity", "Assignment completion", "Final result"]]

    os.makedirs("prepared", exist_ok=True)
    students.to_csv(OUTPUT, index=False)
    print(f"{len(students)} students, {weeks} weeks, {len(assignments)} assignments -> {OUTPUT}")
    return students


if __name__ == "__main__":
    download()
    build()
