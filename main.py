"""
main.py - run the whole student grouping study with one command:

    python main.py

It:
    1. loads 1,655 students (prepared/students.csv),
    2. picks the number of groups k by how stable K-Means is,
    3. groups the students with hierarchical clustering, comparing four
       ways of measuring the distance between groups (linkage),
    4. groups them with K-Means,
    5. names and describes each group, and checks it against the students'
       final results, which neither algorithm saw,
    6. compares the two groupings, saves the K-Means pipeline for the app
       and writes docs/results.md.
Figures and tables go to outputs/students/.
"""

import json
import os

import joblib
import pandas as pd
from sklearn.metrics import silhouette_score

from pxlab.cluster.analysis import (
    agreement,
    choose_k_by_stability,
    hierarchical_labels,
    k_sweep,
    kmeans_pipeline,
    plot_dendrogram,
    plot_groups_2d,
    plot_k_sweep,
    plot_profile_heatmap,
    profiles,
    relabel_by,
    scale,
)
from pxlab.common import MODELS_FOLDER, save_figure, save_table, set_plot_style, write_results_doc
from student_clusters.data import ATTENDANCE, INPUTS, RESULT, RESULTS, SHOWN, STUDY, load_students
from student_clusters.groups import advice_for, name_groups
from student_clusters.report import FOLDER, results_sections

K_VALUES = range(2, 9)
K_CHOICES = range(3, 7)  # k = 2 only splits active from inactive students
LINKAGES = ["ward", "average", "complete", "single"]


def group_table(students, labels, names):
    """
    One row per group: size, averages, final results and advice.

    Inputs:
        students: the student table.
        labels: the group of each student.
        names: dictionary group number -> name.
    Returns:
        The table.
    """
    table = profiles(students, labels, SHOWN, names).rename(columns={"Customers": "Students"}).round(2)
    results = pd.crosstab(labels, students[RESULT], normalize="index").reindex(columns=RESULTS, fill_value=0)
    results = results.round(2).reset_index(drop=True)
    table = pd.concat([table, results], axis=1)
    table["Advice"] = [advice_for(name) for name in table["Group"]]
    return table


def groups_figure(students, labels, names, title):
    """
    Attendance against study activity, coloured by group. Study activity
    is drawn on a log-like scale, as it is clustered.

    Inputs:
        students: the student table.
        labels: the group of each student.
        names: dictionary group number -> name.
        title: the figure title.
    Returns:
        The figure.
    """
    figure = plot_groups_2d(students, labels, ATTENDANCE, STUDY, names, title)
    figure.axes[0].set_yscale("symlog", linthresh=1)
    return figure


def main():
    """
    The full study.

    Returns:
        Nothing.
    """
    set_plot_style()
    students = load_students()
    features = scale(students, INPUTS)
    print(f"Students: {len(students)}")

    # Choosing k
    k, stable = choose_k_by_stability(features, K_CHOICES)
    sweep = k_sweep(features, K_VALUES)
    sweep["Ward silhouette"] = [silhouette_score(features, hierarchical_labels(features, n)) for n in K_VALUES]
    sweep = sweep.rename(columns={"Silhouette": "K-Means silhouette"}).merge(stable, on="k", how="left").round(3)
    save_table(sweep, f"{FOLDER}/k_sweep.csv")
    save_figure(
        plot_k_sweep(sweep.rename(columns={"K-Means silhouette": "Silhouette"}), k, f"Choosing k (k = {k} chosen)"),
        f"{FOLDER}/k_sweep.png",
    )
    print(f"  k = {k}")

    # Hierarchical clustering with each linkage
    rows = []
    for method in LINKAGES:
        labels = hierarchical_labels(features, k, method)
        sizes = sorted(pd.Series(labels).value_counts().tolist(), reverse=True)
        rows.append(
            {
                "Linkage": method,
                "Silhouette": round(silhouette_score(features, labels), 3),
                "Group sizes": ", ".join(str(size) for size in sizes),
            }
        )
    save_table(pd.DataFrame(rows), f"{FOLDER}/linkages.csv")

    ward = relabel_by(hierarchical_labels(features, k, "ward"), students[ATTENDANCE])
    ward_names = name_groups(students, ward)
    save_table(group_table(students, ward, ward_names), f"{FOLDER}/groups_ward.csv")
    save_figure(
        plot_dendrogram(features, "ward", f"Hierarchical clustering (Ward), cut into {k} groups", cut_k=k),
        f"{FOLDER}/dendrogram.png",
    )
    print("  Ward: " + ", ".join(ward_names.values()))

    # K-Means
    pipeline = kmeans_pipeline(k).fit(students[INPUTS])
    raw = pipeline.predict(students[INPUTS])
    kmeans = relabel_by(raw, students[ATTENDANCE])
    kmeans_names = name_groups(students, kmeans)
    save_table(group_table(students, kmeans, kmeans_names), f"{FOLDER}/groups_kmeans.csv")
    save_figure(groups_figure(students, kmeans, kmeans_names, f"K-Means, {k} groups"), f"{FOLDER}/groups_kmeans.png")
    save_figure(
        plot_profile_heatmap(students, kmeans, SHOWN, kmeans_names, "How each K-Means group differs from the average"),
        f"{FOLDER}/profiles_kmeans.png",
    )
    print("  K-Means: " + ", ".join(kmeans_names.values()))

    # Comparison
    comparison = pd.crosstab(
        pd.Series([ward_names[g] for g in ward], name="Ward"),
        pd.Series([kmeans_names[g] for g in kmeans], name="K-Means"),
    ).loc[list(ward_names.values()), list(kmeans_names.values())]
    save_table(comparison.reset_index(), f"{FOLDER}/comparison.csv")
    same = agreement(ward, kmeans)
    print(f"  agreement (adjusted Rand): {same:.3f}")

    os.makedirs(MODELS_FOLDER, exist_ok=True)
    joblib.dump(pipeline, os.path.join(MODELS_FOLDER, "groups.joblib"))
    raw_names = {int(r): kmeans_names[int(n)] for r, n in set(zip(raw, kmeans))}
    with open(os.path.join(MODELS_FOLDER, "groups.json"), "w") as file:
        json.dump({"inputs": INPUTS, "k": k, "groups": raw_names, "students": len(students)}, file, indent=2)

    write_results_doc(
        "Results",
        f"Produced by `python main.py` on {len(students):,} students. K-Means with 20 random starts, seed 42. "
        f"Agreement between the Ward and K-Means groupings (adjusted Rand index): {same:.2f}.",
        results_sections(),
    )
    print("  Done. Run: streamlit run app.py")


if __name__ == "__main__":
    main()
