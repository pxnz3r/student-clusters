"""
app.py - explore the student groups. Run it with:

    streamlit run app.py

Tabs:
    Overview         what was done and found,
    Explore          re-run hierarchical clustering or K-Means live,
    Place a student  which group a student falls in, and what to do,
    Results          the saved tables and figures from main.py.
"""

import json
import os

import joblib
import pandas as pd
import streamlit as st

from pxlab.app import setup_page, show_markdown_file, show_results_tabs
from pxlab.cluster.analysis import (
    hierarchical_labels,
    kmeans_pipeline,
    plot_dendrogram,
    plot_groups_2d,
    profiles,
    relabel_by,
    scale,
)
from pxlab.common import MODELS_FOLDER
from student_clusters.data import (
    ATTENDANCE,
    COMPLETION,
    DESCRIPTIONS,
    INPUTS,
    RESULT,
    RESULTS,
    SHOWN,
    STUDY,
    add_log_study,
    load_students,
)
from student_clusters.groups import advice_for, name_groups
from student_clusters.report import results_sections


@st.cache_data
def students_and_features():
    """
    The student table and its scaled inputs, loaded once.

    Returns:
        (students DataFrame, scaled inputs).
    """
    students = load_students()
    return students, scale(students, INPUTS)


@st.cache_resource
def load_model():
    """
    The K-Means pipeline saved by main.py and its group names.

    Returns:
        (pipeline, info dictionary).
    """
    pipeline = joblib.load(os.path.join(MODELS_FOLDER, "groups.joblib"))
    with open(os.path.join(MODELS_FOLDER, "groups.json")) as file:
        info = json.load(file)
    return pipeline, info


@st.cache_data
def hierarchical(k, method):
    """
    Hierarchical labels, cached because the merge tree is slow to rebuild.

    Inputs:
        k: the number of groups.
        method: the linkage.
    Returns:
        The group of each student.
    """
    _students, features = students_and_features()
    return hierarchical_labels(features, k, method)


def show_explore_page():
    """
    The Explore tab.

    Returns:
        Nothing.
    """
    students, features = students_and_features()
    first, second, third = st.columns(3)
    method = first.radio("Method", ["Hierarchical", "K-Means"], horizontal=True)
    linkage = second.selectbox(
        "Linkage",
        ["ward", "average", "complete", "single"],
        disabled=method == "K-Means",
        help="How the distance between two groups is measured when deciding which to merge.",
    )
    k = third.slider("Number of groups (k)", 2, 8, 4)

    if method == "Hierarchical":
        raw = hierarchical(k, linkage)
    else:
        raw = kmeans_pipeline(k).fit_predict(students[INPUTS])
    labels = relabel_by(raw, students[ATTENDANCE])
    names = name_groups(students, labels)

    figure = plot_groups_2d(students, labels, ATTENDANCE, STUDY, names, f"{method}, {k} groups")
    figure.axes[0].set_yscale("symlog", linthresh=1)
    st.pyplot(figure, width="stretch")

    table = profiles(students, labels, SHOWN, names).rename(columns={"Customers": "Students"})
    results = pd.crosstab(labels, students[RESULT], normalize="index").reindex(columns=RESULTS, fill_value=0)
    table = pd.concat([table, results.reset_index(drop=True)], axis=1)
    percent = st.column_config.NumberColumn(format="percent")
    st.dataframe(
        table,
        hide_index=True,
        width="stretch",
        column_config={
            "Share": percent,
            ATTENDANCE: percent,
            COMPLETION: percent,
            STUDY: st.column_config.NumberColumn(format="%.1f"),
            **{result: percent for result in RESULTS},
        },
    )
    st.caption("Final results were never shown to the algorithms; they only check the groups afterwards.")
    if method == "Hierarchical":
        st.pyplot(plot_dendrogram(features, linkage, f"Merge tree ({linkage} linkage)", cut_k=k), width="stretch")


def show_place_page():
    """
    The Place a student tab.

    Returns:
        Nothing.
    """
    pipeline, info = load_model()
    first, second, third = st.columns(3)
    attendance = first.slider(ATTENDANCE, 0.0, 1.0, 0.5, step=0.05, help=DESCRIPTIONS[ATTENDANCE])
    study = second.number_input(STUDY, 0.0, 400.0, 10.0, step=1.0, help=DESCRIPTIONS[STUDY])
    completion = third.slider(COMPLETION, 0.0, 1.0, 0.5, step=1 / 6, format="%.2f", help=DESCRIPTIONS[COMPLETION])

    student = add_log_study(pd.DataFrame([{ATTENDANCE: attendance, STUDY: study, COMPLETION: completion}]))
    name = info["groups"][str(int(pipeline.predict(student[info["inputs"]])[0]))]
    st.subheader(name, anchor=False)
    st.markdown(advice_for(name))


def main():
    """
    Build the page.

    Returns:
        Nothing.
    """
    setup_page("Student groups")
    overview, explore, place, results = st.tabs(["Overview", "Explore", "Place a student", "Results"])
    with overview:
        show_markdown_file("app_overview.md")
    with explore:
        show_explore_page()
    with place:
        show_place_page()
    with results:
        show_results_tabs(results_sections())


main()
