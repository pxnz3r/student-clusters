"""
report.py - which saved tables and figures make up the results. The app's
Results tab and docs/results.md both read this list, so they always match.
"""

FOLDER = "students"


def results_sections():
    """
    The results, grouped into sections.

    Returns:
        A list of (section name, items) for pxlab's show_results_tabs() and
        write_results_doc().
    """
    return [
        (
            "Hierarchical",
            [
                ("figure", f"{FOLDER}/dendrogram.png"),
                ("table", "Hierarchical (Ward) groups", f"{FOLDER}/groups_ward.csv"),
                ("table", "Linkage methods compared", f"{FOLDER}/linkages.csv"),
            ],
        ),
        (
            "K-Means",
            [
                ("figure", f"{FOLDER}/groups_kmeans.png"),
                ("table", "K-Means groups", f"{FOLDER}/groups_kmeans.csv"),
                ("figure", f"{FOLDER}/profiles_kmeans.png"),
            ],
        ),
        (
            "Choosing k",
            [
                ("figure", f"{FOLDER}/k_sweep.png"),
                ("table", "Scores for each k", f"{FOLDER}/k_sweep.csv"),
            ],
        ),
        (
            "Comparison",
            [("table", "Students by Ward group (rows) and K-Means group (columns)", f"{FOLDER}/comparison.csv")],
        ),
    ]
