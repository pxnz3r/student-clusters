"""
validate.py - is a clustering real, and can each group be trusted?

Clustering always returns groups, even on random noise. These checks ask
whether the groups found are more than an artefact:

    Several quality scores per k: silhouette (higher is better),
        Calinski-Harabasz (spread between groups against spread inside them,
        higher is better) and Davies-Bouldin (how much each group overlaps
        its most similar neighbour, lower is better). When they agree on k,
        the choice is safer.
    Silhouette diagram: the silhouette of every example, grouped and sorted.
        A group with many negative values contains examples that sit closer
        to another group.
    Per-group stability (bootstrap): draw the examples again with
        replacement, cluster the draw, and see whether each original group
        reappears (Jaccard overlap, 1 = the same members). Averaged over
        many draws: above 0.75 a group is stable, below 0.5 it dissolves.
    Comparison with structureless data: shuffle every input column on its
        own, which keeps each input's spread but destroys how inputs go
        together, and cluster that. If the real data's silhouette is no
        better than the shuffled data's, the groups are just slices of a
        cloud.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import calinski_harabasz_score, davies_bouldin_score, silhouette_samples, silhouette_score

from pxlab.common import RANDOM_STATE, save_figure, save_table


def quality_indices(features, k_values):
    """
    Silhouette, Calinski-Harabasz and Davies-Bouldin of K-Means for each k.

    Inputs:
        features: the scaled inputs.
        k_values: the k to try (each at least 2).
    Returns:
        A table with one row per k.
    """
    rows = []
    for k in k_values:
        labels = KMeans(n_clusters=k, n_init=20, random_state=RANDOM_STATE).fit_predict(features)
        rows.append(
            {
                "k": k,
                "Silhouette (higher better)": silhouette_score(features, labels),
                "Calinski-Harabasz (higher better)": calinski_harabasz_score(features, labels),
                "Davies-Bouldin (lower better)": davies_bouldin_score(features, labels),
            }
        )
    return pd.DataFrame(rows)


def plot_silhouette_diagram(features, labels, names, title):
    """
    The silhouette of every example, one band per group, sorted within it.
    The dashed line is the average.

    Inputs:
        features: the scaled inputs.
        labels: the group of each example.
        names: dictionary group number -> name.
        title: the figure title.
    Returns:
        The figure.
    """
    values = silhouette_samples(features, labels)
    figure, axis = plt.subplots(figsize=(8, 0.9 * len(names) + 3))
    bottom = 0
    colours = plt.get_cmap("tab10")
    for group in sorted(names):
        group_values = np.sort(values[labels == group])
        top = bottom + len(group_values)
        axis.fill_betweenx(np.arange(bottom, top), 0, group_values, color=colours(group % 10), alpha=0.8)
        negative = np.mean(group_values < 0)
        axis.text(
            -0.02, (bottom + top) / 2, f"{names[group]} ({negative:.0%} < 0)", ha="right", va="center", fontsize=9
        )
        bottom = top + 10
    axis.axvline(values.mean(), color="black", linestyle="--", linewidth=1, label=f"Average {values.mean():.2f}")
    axis.axvline(0, color="grey", linewidth=0.8)
    axis.set_yticks([])
    axis.set_xlabel("Silhouette (how much closer to its own group than to the next)")
    axis.set_title(title)
    axis.legend(loc="lower right")
    figure.tight_layout()
    return figure


def jaccard(members_a, members_b):
    """
    Overlap of two sets of example numbers: shared / either.

    Inputs:
        members_a, members_b: sets of row numbers.
    Returns:
        A number from 0 (no overlap) to 1 (identical).
    """
    either = len(members_a | members_b)
    return len(members_a & members_b) / either if either else 0.0


def group_stability(features, labels, k, rounds=50):
    """
    Bootstrap stability of each group (Hennig's method): for every draw,
    the best Jaccard match of each original group among the draw's groups,
    counting only the examples that were drawn.

    Inputs:
        features: the scaled inputs.
        labels: the group of each example (from K-Means on all of them).
        k: the number of groups.
        rounds: how many bootstrap draws.
    Returns:
        A table: Group number, mean Jaccard, share of draws where the group
        was recovered (Jaccard of at least 0.5).
    """
    generator = np.random.default_rng(RANDOM_STATE)
    scores = {group: [] for group in range(k)}
    for round_number in range(rounds):
        drawn = np.unique(generator.integers(0, len(features), len(features)))
        new_labels = KMeans(n_clusters=k, n_init=5, random_state=round_number).fit_predict(features[drawn])
        new_groups = [set(drawn[new_labels == g]) for g in range(k)]
        for group in range(k):
            original = set(drawn[labels[drawn] == group])
            scores[group].append(max(jaccard(original, other) for other in new_groups))
    rows = []
    for group, values in scores.items():
        rows.append(
            {
                "Group": group,
                "Mean Jaccard": float(np.mean(values)),
                "Recovered in": float(np.mean(np.asarray(values) >= 0.5)),
            }
        )
    return pd.DataFrame(rows)


def stability_verdict(mean_jaccard):
    """
    Hennig's reading of a mean Jaccard score.

    Input:
        mean_jaccard: from group_stability().
    Returns:
        A short phrase.
    """
    if mean_jaccard >= 0.85:
        return "very stable"
    if mean_jaccard >= 0.75:
        return "stable"
    if mean_jaccard >= 0.6:
        return "a pattern, but its edges move"
    return "unstable"


def shuffled_comparison(features, k, rounds=20):
    """
    Silhouette of the real data against data with every column shuffled on
    its own (same spreads, no relationships between inputs).

    Inputs:
        features: the scaled inputs.
        k: the number of groups.
        rounds: how many shuffled copies.
    Returns:
        A dictionary: real silhouette, shuffled mean and spread, and how many
        standard deviations the real one sits above the shuffled ones.
    """
    generator = np.random.default_rng(RANDOM_STATE)
    real = silhouette_score(features, KMeans(n_clusters=k, n_init=10, random_state=RANDOM_STATE).fit_predict(features))
    shuffled = []
    for _ in range(rounds):
        copy = np.column_stack([generator.permutation(column) for column in features.T])
        labels = KMeans(n_clusters=k, n_init=5, random_state=RANDOM_STATE).fit_predict(copy)
        shuffled.append(silhouette_score(copy, labels))
    spread = max(float(np.std(shuffled)), 1e-9)
    return {
        "Real silhouette": float(real),
        "Shuffled silhouette (mean)": float(np.mean(shuffled)),
        "Shuffled silhouette (spread)": spread,
        "Standard deviations above shuffled": (real - float(np.mean(shuffled))) / spread,
    }


def run_validation(features, labels, names, k, k_values, folder):
    """
    Run every check on a K-Means grouping and save the tables and figure
    into outputs/<folder>/, plus validation_findings.csv with one sentence
    per finding.

    Inputs:
        features: the scaled inputs the grouping was made from.
        labels: the group of each example (any numbering).
        names: dictionary group number -> name.
        k: the number of groups.
        k_values: the k to score for the quality table.
        folder: the output subfolder.
    Returns:
        The list of finding sentences.
    """
    indices = quality_indices(features, k_values)
    save_table(indices.round(3), f"{folder}/quality_indices.csv")
    save_figure(
        plot_silhouette_diagram(features, labels, names, f"Silhouette of every example, k = {k}"),
        f"{folder}/silhouette_diagram.png",
    )
    stable = group_stability(features, labels, k)
    stable["Group"] = [names[group] for group in stable["Group"]]
    stable["Verdict"] = [stability_verdict(value) for value in stable["Mean Jaccard"]]
    save_table(stable.round(3), f"{folder}/group_stability.csv")
    shuffled = shuffled_comparison(features, k)
    save_table(pd.DataFrame([shuffled]).round(3), f"{folder}/shuffled_comparison.csv")

    best_by = {
        "silhouette": int(indices.loc[indices["Silhouette (higher better)"].idxmax(), "k"]),
        "Calinski-Harabasz": int(indices.loc[indices["Calinski-Harabasz (higher better)"].idxmax(), "k"]),
        "Davies-Bouldin": int(indices.loc[indices["Davies-Bouldin (lower better)"].idxmin(), "k"]),
    }
    findings = [
        "Best k by each score: "
        + ", ".join(f"{name} {value}" for name, value in best_by.items())
        + f"; k = {k} was used."
    ]
    weakest = stable.loc[stable["Mean Jaccard"].idxmin()]
    strongest = stable.loc[stable["Mean Jaccard"].idxmax()]
    findings.append(
        f"Most stable group: {strongest['Group']} (mean Jaccard {strongest['Mean Jaccard']:.2f}, {strongest['Verdict']}); "
        f"least stable: {weakest['Group']} ({weakest['Mean Jaccard']:.2f}, {weakest['Verdict']})."
    )
    real, fake = shuffled["Real silhouette"], shuffled["Shuffled silhouette (mean)"]
    verdict = (
        "real structure"
        if shuffled["Standard deviations above shuffled"] > 3
        else "little more than slices of one cloud"
    )
    findings.append(
        f"Silhouette {real:.3f} on the real data against {fake:.3f} on shuffled data with no relationships between "
        f"inputs: the groups reflect {verdict}."
    )
    save_table(pd.DataFrame({"Finding": findings}), f"{folder}/validation_findings.csv")
    for finding in findings:
        print("  " + finding)
    return findings


def validation_sections(folder):
    """
    The validation tables and figure as one results section.

    Input:
        folder: the output subfolder.
    Returns:
        A list with one (section name, items) entry.
    """
    return [
        (
            "Validation",
            [
                ("table", "What the checks found", f"{folder}/validation_findings.csv"),
                ("figure", f"{folder}/silhouette_diagram.png"),
                ("table", "Bootstrap stability of each group (50 draws)", f"{folder}/group_stability.csv"),
                ("table", "Real data against shuffled data", f"{folder}/shuffled_comparison.csv"),
                ("table", "Three quality scores for each k", f"{folder}/quality_indices.csv"),
            ],
        )
    ]
