"""
analysis.py - clustering helpers shared by every clustering project.

Clustering is unsupervised: there is no right answer to learn from. The
algorithm groups examples that are close to each other. "Close" is measured
as distance between the scaled inputs, so every input is standardised first
(mean 0, standard deviation 1); otherwise income in thousands would drown
out a score from 1 to 100.

    K-Means: picks k centres, gives every example to its nearest centre,
        moves each centre to the mean of its examples, and repeats until
        nothing changes. It needs k up front.
    Hierarchical (agglomerative): starts with every example on its own and
        keeps merging the two closest groups. The record of merges is a tree
        (dendrogram); cutting it at a height gives the groups.

Choosing k:
    inertia: the total squared distance from each example to its centre.
        It always falls as k grows; the "elbow" where it stops falling fast
        is a good k.
    silhouette: for each example, how much closer it is to its own group
        than to the next one, from -1 to 1. Higher is better.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.cluster.hierarchy import dendrogram, linkage
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from pxlab.common import RANDOM_STATE


def scale(table, columns):
    """
    Standardise the inputs so each counts equally in the distances.

    Inputs:
        table: the DataFrame.
        columns: the input columns.
    Returns:
        A numpy array, one row per example.
    """
    return StandardScaler().fit_transform(table[columns])


def k_sweep(features, k_values):
    """
    Fit K-Means for each k and score it.

    Inputs:
        features: the scaled inputs.
        k_values: the k to try (each at least 2).
    Returns:
        A table with k, inertia and silhouette.
    """
    rows = []
    for k in k_values:
        model = KMeans(n_clusters=k, n_init=20, random_state=RANDOM_STATE).fit(features)
        rows.append({"k": k, "Inertia": model.inertia_, "Silhouette": silhouette_score(features, model.labels_)})
    return pd.DataFrame(rows)


def plot_k_sweep(sweep, chosen_k, title):
    """
    Inertia (the elbow) and silhouette against k, side by side.

    Inputs:
        sweep: the table from k_sweep().
        chosen_k: the k used, marked on both panels.
        title: the figure title.
    Returns:
        The figure.
    """
    figure, (left, right) = plt.subplots(1, 2, figsize=(11, 4))
    for axis, column, note in [(left, "Inertia", "lower is tighter"), (right, "Silhouette", "higher is better")]:
        axis.plot(sweep["k"], sweep[column], marker="o")
        axis.axvline(chosen_k, color="grey", linestyle="--", linewidth=1)
        axis.set_xlabel("Number of groups (k)")
        axis.set_ylabel(column)
        axis.set_title(f"{column} ({note})")
        axis.set_xticks(sweep["k"])
    figure.suptitle(title)
    figure.tight_layout()
    return figure


def kmeans_pipeline(k):
    """
    Scaling plus K-Means in one pipeline, so a new example is scaled the
    same way before it is given to its nearest centre.

    Input:
        k: the number of groups.
    Returns:
        An unfitted sklearn Pipeline.
    """
    return make_pipeline(StandardScaler(), KMeans(n_clusters=k, n_init=20, random_state=RANDOM_STATE))


def hierarchical_labels(features, k, method="ward"):
    """
    Agglomerative clustering cut into k groups.

    Inputs:
        features: the scaled inputs.
        k: the number of groups.
        method: how the distance between two groups is measured. "ward"
            merges the pair that adds least to the spread inside groups;
            "average" uses the mean distance between their members;
            "complete" the largest; "single" the smallest.
    Returns:
        The group of each example (0 to k-1).
    """
    return AgglomerativeClustering(n_clusters=k, linkage=method).fit_predict(features)


def relabel_by(labels, values):
    """
    Renumber groups so group 0 has the lowest mean of `values`, group 1 the
    next and so on. Clustering numbers groups arbitrarily; this makes the
    numbering stable and readable.

    Inputs:
        labels: the group of each example.
        values: one number per example to order the groups by.
    Returns:
        The renumbered labels.
    """
    means = pd.Series(values).groupby(np.asarray(labels)).mean().sort_values()
    order = {old: new for new, old in enumerate(means.index)}
    return np.array([order[label] for label in labels])


def stability(features, k, seeds=10):
    """
    How much K-Means depends on its random starting centres: the agreement
    (adjusted Rand index, 1 = identical groups, 0 = chance) between runs
    from different seeds and the first run.

    Inputs:
        features: the scaled inputs.
        k: the number of groups.
        seeds: how many runs.
    Returns:
        The mean and lowest agreement.
    """
    runs = [KMeans(n_clusters=k, n_init=1, random_state=seed).fit_predict(features) for seed in range(seeds)]
    scores = [adjusted_rand_score(runs[0], run) for run in runs[1:]]
    return float(np.mean(scores)), float(np.min(scores))


def agreement(labels_a, labels_b):
    """
    Adjusted Rand index between two groupings of the same examples.

    Inputs:
        labels_a, labels_b: two label arrays.
    Returns:
        A number from about 0 (chance) to 1 (identical).
    """
    return float(adjusted_rand_score(labels_a, labels_b))


def profiles(table, labels, columns, names=None):
    """
    The average of each input in each group, with the group's size.

    Inputs:
        table: the DataFrame of original (unscaled) inputs.
        labels: the group of each row.
        columns: the inputs to average.
        names: optional dictionary group number -> name.
    Returns:
        A table with one row per group.
    """
    grouped = table[columns].groupby(np.asarray(labels))
    result = grouped.mean()
    result.insert(0, "Customers", grouped.size())
    result.insert(1, "Share", (grouped.size() / len(table)).round(3))
    result.index.name = "Group"
    if names:
        result.index = [names[group] for group in result.index]
        result.index.name = "Group"
    return result.reset_index()


def plot_profile_heatmap(table, labels, columns, names, title):
    """
    Each group's average of each input, shown as standard deviations above
    or below the overall average (so different units share one colour scale).

    Inputs:
        table: the DataFrame of original inputs.
        labels: the group of each row.
        columns: the inputs.
        names: dictionary group number -> name.
        title: the figure title.
    Returns:
        The figure.
    """
    means = table[columns].groupby(np.asarray(labels)).mean()
    z = (means - table[columns].mean()) / table[columns].std()
    z.index = [names[group] for group in z.index]
    figure, axis = plt.subplots(figsize=(1.6 * len(columns) + 3, 0.6 * len(z) + 1.5))

    sns.heatmap(
        z, annot=True, fmt="+.1f", cmap="RdBu_r", center=0, ax=axis, cbar_kws={"label": "Std. dev. from average"}
    )
    axis.set_title(title)
    axis.set_ylabel("")
    return figure


def plot_groups_2d(table, labels, x, y, names, title, centres=None):
    """
    A scatter plot of two inputs coloured by group.

    Inputs:
        table: the DataFrame.
        labels: the group of each row.
        x, y: the two columns to plot.
        names: dictionary group number -> name.
        title: the figure title.
        centres: optional array of group centres in (x, y) units, one row
            per group number.
    Returns:
        The figure.
    """
    figure, axis = plt.subplots(figsize=(8, 6))
    for group in sorted(names):
        rows = np.asarray(labels) == group
        axis.scatter(table.loc[rows, x], table.loc[rows, y], s=14, alpha=0.6, label=names[group])
    if centres is not None:
        axis.scatter(centres[:, 0], centres[:, 1], marker="X", s=180, c="black", label="Centres")
    axis.set_xlabel(x)
    axis.set_ylabel(y)
    axis.set_title(title)
    axis.legend(loc="best", fontsize="small")
    return figure


def plot_groups_pca(features, labels, names, title):
    """
    The groups on the first two principal components: the two directions
    along which the scaled inputs vary most. It squeezes many inputs into
    a flat picture, so overlap here doesn't always mean overlap in full.

    Inputs:
        features: the scaled inputs.
        labels: the group of each example.
        names: dictionary group number -> name.
        title: the figure title.
    Returns:
        The figure.
    """
    pca = PCA(n_components=2, random_state=RANDOM_STATE)
    points = pca.fit_transform(features)
    figure, axis = plt.subplots(figsize=(8, 6))
    for group in sorted(names):
        rows = np.asarray(labels) == group
        axis.scatter(points[rows, 0], points[rows, 1], s=14, alpha=0.6, label=names[group])
    share = pca.explained_variance_ratio_
    axis.set_xlabel(f"First component ({share[0]:.0%} of the spread)")
    axis.set_ylabel(f"Second component ({share[1]:.0%} of the spread)")
    axis.set_title(title)
    axis.legend(loc="best", fontsize="small")
    return figure


def plot_dendrogram(features, method, title, cut_k=None):
    """
    The merge tree of hierarchical clustering, with only the last 30 merges
    drawn so it stays readable.

    Inputs:
        features: the scaled inputs.
        method: the linkage method ("ward", "average", "complete", "single").
        title: the figure title.
        cut_k: optional number of groups; a line marks where the tree is cut.
    Returns:
        The figure.
    """
    merges = linkage(features, method=method)
    figure, axis = plt.subplots(figsize=(11, 5))
    dendrogram(merges, truncate_mode="lastp", p=30, ax=axis, color_threshold=None, no_labels=True)
    if cut_k:
        # The cut sits between the heights of the (k-1)-th and k-th last merges.
        heights = merges[:, 2]
        axis.axhline((heights[-cut_k] + heights[-cut_k + 1]) / 2, color="grey", linestyle="--", linewidth=1)
    axis.set_ylabel("Merge distance")
    axis.set_xlabel("Groups (last 30 merges; numbers are group sizes)")
    axis.set_title(title)
    return figure


def choose_k_by_stability(features, k_values):
    """
    The k whose K-Means groups come out most alike whatever the random
    starting centres. Silhouette tends to favour k = 2, which often just
    splits "more" from "less"; stability picks a k whose groups are real
    enough to be found again.

    Inputs:
        features: the scaled inputs.
        k_values: the k to consider.
    Returns:
        (chosen k, table of mean and lowest agreement per k).
    """
    rows = []
    for k in k_values:
        mean, lowest = stability(features, k)
        rows.append({"k": k, "Stability (mean)": round(mean, 3), "Stability (lowest)": round(lowest, 3)})
    table = pd.DataFrame(rows)
    return int(table.loc[table["Stability (mean)"].idxmax(), "k"]), table
