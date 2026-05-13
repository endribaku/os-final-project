"""
common/plots.py
Shared matplotlib helpers so every figure across the three papers has consistent styling.

Provided plots
--------------
- line_with_errorbars(x, ys_runs, ...) -- mean +/- std across seeded repetitions.
- heatmap(matrix, ...)                 -- for grid sweeps (e.g. Q1 x Q2 in Paper 3).
- surface3d(X, Y, Z, ...)              -- the 2D/3D performance surfaces Paper 3 requires.
- bar_compare(groups, series, ...)     -- side-by-side comparisons
                                          (POSIX vs Java, original vs optimized, etc.).

All functions return (fig, ax). Use `save(fig, path)` to write a 300 dpi PNG.
Call `set_style()` once if you want to re-apply the shared style after tweaking rc.

Dependencies:  pip install numpy matplotlib
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def set_style() -> None:
    """Apply the shared rc style for all figures."""
    plt.rcParams.update({
        "figure.figsize":   (6.5, 4.0),
        "figure.dpi":       110,
        "savefig.dpi":      300,
        "savefig.bbox":     "tight",
        "font.size":        10,
        "axes.titlesize":   11,
        "axes.labelsize":   10,
        "legend.fontsize":  9,
        "xtick.labelsize":  9,
        "ytick.labelsize":  9,
        "axes.grid":        True,
        "grid.alpha":       0.3,
        "lines.linewidth":  1.4,
        "lines.markersize": 4,
    })


# Apply on import so callers don't have to.
set_style()


def save(fig, path: str | Path) -> None:
    """Save `fig` to `path` (creates parent dirs)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path)


def line_with_errorbars(
    x,
    ys_runs,
    *,
    label: str | None = None,
    ax=None,
    xlabel: str = "",
    ylabel: str = "",
    title: str = "",
    marker: str = "o",
    logx: bool = False,
    logy: bool = False,
):
    """
    Plot mean +/- std across repetitions.

    x       : 1D array, length n_x.
    ys_runs : 2D array [n_x, n_runs]  (or 1D if a single run per x).
    """
    x = np.asarray(x)
    Y = np.asarray(ys_runs, dtype=float)
    if Y.ndim == 1:
        Y = Y[:, None]
    mean = Y.mean(axis=1)
    std = Y.std(axis=1, ddof=1) if Y.shape[1] > 1 else np.zeros_like(mean)

    if ax is None:
        fig, ax = plt.subplots()
    else:
        fig = ax.figure

    ax.errorbar(x, mean, yerr=std, marker=marker, capsize=3, label=label)
    if logx:
        ax.set_xscale("log")
    if logy:
        ax.set_yscale("log")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    if label:
        ax.legend()
    return fig, ax


def heatmap(
    matrix,
    *,
    xticks=None,
    yticks=None,
    xlabel: str = "",
    ylabel: str = "",
    title: str = "",
    cbar_label: str = "",
    cmap: str = "viridis",
    ax=None,
    annotate: bool = False,
    annot_fmt: str = "{:.2f}",
):
    """2D heatmap of `matrix` (shape [n_rows, n_cols])."""
    M = np.asarray(matrix, dtype=float)
    if ax is None:
        fig, ax = plt.subplots()
    else:
        fig = ax.figure

    im = ax.imshow(M, origin="lower", aspect="auto", cmap=cmap)
    if xticks is not None:
        ax.set_xticks(range(len(xticks)))
        ax.set_xticklabels(xticks)
    if yticks is not None:
        ax.set_yticks(range(len(yticks)))
        ax.set_yticklabels(yticks)

    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label(cbar_label)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)

    if annotate:
        threshold = (np.nanmin(M) + np.nanmax(M)) / 2
        for i in range(M.shape[0]):
            for j in range(M.shape[1]):
                ax.text(
                    j, i, annot_fmt.format(M[i, j]),
                    ha="center", va="center", fontsize=7,
                    color="white" if M[i, j] < threshold else "black",
                )
    return fig, ax


def surface3d(
    X,
    Y,
    Z,
    *,
    xlabel: str = "",
    ylabel: str = "",
    zlabel: str = "",
    title: str = "",
    cmap: str = "viridis",
):
    """
    3D surface plot. X, Y are 2D meshgrids (see np.meshgrid); Z is 2D values.
    """
    X = np.asarray(X)
    Y = np.asarray(Y)
    Z = np.asarray(Z, dtype=float)

    fig = plt.figure(figsize=(7, 5))
    ax = fig.add_subplot(111, projection="3d")
    surf = ax.plot_surface(X, Y, Z, cmap=cmap, edgecolor="none", alpha=0.9)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_zlabel(zlabel)
    ax.set_title(title)
    fig.colorbar(surf, ax=ax, shrink=0.6)
    return fig, ax


def bar_compare(
    groups,
    series,
    *,
    errors=None,
    xlabel: str = "",
    ylabel: str = "",
    title: str = "",
    ax=None,
):
    """
    Grouped bar chart.

    groups : list of category labels on the x-axis.
    series : dict {series_name: list-of-values aligned with `groups`}.
    errors : dict {series_name: list-of-stds} or None.
    """
    if ax is None:
        fig, ax = plt.subplots()
    else:
        fig = ax.figure

    n_groups = len(groups)
    n_series = len(series)
    width = 0.8 / max(n_series, 1)
    idx = np.arange(n_groups)

    for i, (name, vals) in enumerate(series.items()):
        err = errors[name] if (errors and name in errors) else None
        offset = i * width - 0.4 + width / 2
        ax.bar(idx + offset, vals, width, yerr=err, capsize=3, label=name)

    ax.set_xticks(idx)
    ax.set_xticklabels(groups)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend()
    return fig, ax
