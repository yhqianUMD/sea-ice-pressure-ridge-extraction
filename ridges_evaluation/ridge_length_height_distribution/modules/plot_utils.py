import matplotlib.pyplot as plt
import numpy as np
from typing import Dict

def save_histogram(values: np.ndarray,
                   hist_png: str,
                   stats: Dict[str, float],
                   value_label: str,
                   key_prefix: str,
                   bin_width: float,
                   x_min: float = 0.0,
                   x_max: float | None = None) -> None:
    fig, ax = plt.subplots(figsize=(9, 6))

    if x_max is not None:
        plot_vals = values[(values >= x_min) & (values <= x_max)]
        bin_edges = np.arange(x_min, x_max + bin_width, bin_width)
    else:
        plot_vals = values[values >= x_min]
        max_val = float(np.max(plot_vals)) if len(plot_vals) > 0 else x_min + bin_width
        bin_edges = np.arange(x_min, max_val + bin_width, bin_width)

    ax.hist(plot_vals, bins=bin_edges, edgecolor="white")
    ax.set_xlabel(value_label)
    ax.set_ylabel("Count")

    if x_max is not None:
        ax.set_xlim(x_min, x_max)

    textstr = "\n".join([
        f"mean: {stats[f'mean_{key_prefix}']:.2f}",
        f"range: {stats[f'min_{key_prefix}']:.2f}, {stats[f'max_{key_prefix}']:.2f}",
        f"n: {int(stats['N_ridges_total'])}",
        f"mode: {stats[f'mode_{key_prefix}']:.2f}",
        f"sd.: {stats[f'std_{key_prefix}']:.2f}",
    ])

    ax.text(
        0.40, 0.86, textstr,
        transform=ax.transAxes,
        fontsize=16,
        verticalalignment="top",
        bbox=dict(boxstyle="square,pad=0.6", alpha=0.25)
    )

    fig.tight_layout()
    fig.savefig(hist_png, dpi=600, bbox_inches="tight")
    plt.close(fig)

