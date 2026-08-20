# =============================================================================
# Report formatting and layout settings used by chapter generators and preamble.
# =============================================================================

from __future__ import annotations

# --- Document geometry -------------------------------------------------------
PAGE_PAPER = "a4paper"
# Extra bottom margin prevents table/footer collisions (e.g. "G4" bleed).
PAGE_MARGIN_TOP = "1in"
PAGE_MARGIN_BOTTOM = "1.25in"
PAGE_MARGIN_LEFT = "1in"
PAGE_MARGIN_RIGHT = "1in"

# --- Brand / colour palette --------------------------------------------------
COLOR_OSDAG_GREEN = "91B014"
COLOR_UR_PASS = "#2E7D32"
COLOR_UR_FAIL = "#C62828"
COLOR_UR_THRESHOLD = "#D32F2F"
COLOR_CHART_STEEL = "#455A64"
COLOR_CHART_CONCRETE = "#607D8B"
COLOR_CHART_REBAR = "#EF6C00"
COLOR_CHART_BRACING = "#00838F"
COLOR_CHART_DIAPHRAGM = "#6A1B9A"

# --- Table metrics -----------------------------------------------------------
TABCOLSEP = "5.5pt"
ARRAYSTRETCH = "1.15"
EXTRAROWHEIGHT = "0.8pt"
ARRAYRULEWIDTH = "0.5pt"
LT_PRE = "2pt"
LT_POST = "8pt"
ROW_SKIP = r"\\[6pt]"  # standard body-row terminator used across chapters
NEEDSPACE_BASELINES = 8  # break early when near page bottom

# Dense tables (analysis / design summaries)
TABCOLSEP_DENSE = "3.5pt"
ARRAYSTRETCH_DENSE = "1.25"
TABCOLSEP_COMPACT = "4pt"
TABCOLSEP_ANALYSIS = "3pt"
TABCOLSEP_CODES = "3.5pt"
ARRAYSTRETCH_ANALYSIS = "1.25"

# --- Header / footer ---------------------------------------------------------
HEADRULE_HEIGHT = "1pt"
FOOTRULE_HEIGHT = "1pt"
# Positive clearance above the footer rule — avoids content overlapping the
# green footrule / "* Software default value" annotation.
FOOTER_CLEARANCE = "6pt"
FOOTRULE_AFTER = "6pt"
SD_NOTE_VSPACE_BEFORE = "3pt"
SD_NOTE_VSPACE_AFTER = "5pt"

# --- Title page --------------------------------------------------------------
TITLE_LOGO_WIDTH = r"0.62\textwidth"
TITLE_ORG_LOGO_HEIGHT = "1.5cm"

# --- Figures / charts --------------------------------------------------------
FIGURE_WIDTH_DEFAULT = r"0.94\textwidth"
CHART_DPI = 180
CHART_FIGSIZE_UR = (9.0, 4.6)
CHART_FIGSIZE_MATERIAL = (9.0, 4.4)
UR_THRESHOLD = 1.0
FIGURE_CAPTION_SKIP_BEFORE = "0.2em"
FIGURE_CAPTION_SKIP_AFTER = "0.4em"


def geometry_options() -> str:
    """LaTeX geometry package option string."""
    return (
        f"{PAGE_PAPER}, "
        f"top={PAGE_MARGIN_TOP}, bottom={PAGE_MARGIN_BOTTOM}, "
        f"left={PAGE_MARGIN_LEFT}, right={PAGE_MARGIN_RIGHT}"
    )


def table_layout_preamble() -> str:
    """Shared table spacing commands for the document preamble."""
    return rf"""
\setlength{{\tabcolsep}}{{{TABCOLSEP}}}
\renewcommand{{\arraystretch}}{{{ARRAYSTRETCH}}}
\setlength{{\LTpre}}{{{LT_PRE}}}
\setlength{{\LTpost}}{{{LT_POST}}}
\setlength{{\arrayrulewidth}}{{{ARRAYRULEWIDTH}}}
\setlength{{\extrarowheight}}{{{EXTRAROWHEIGHT}}}
\BeforeBeginEnvironment{{table}}{{\needspace{{{NEEDSPACE_BASELINES}\baselineskip}}}}
\BeforeBeginEnvironment{{longtable}}{{\needspace{{{NEEDSPACE_BASELINES}\baselineskip}}}}
""".strip()


def local_table_spacing(tabcolsep: str, arraystretch: str | None = None) -> str:
    """Chapter-local spacing — values must come from this module."""
    parts = [rf"\setlength{{\tabcolsep}}{{{tabcolsep}}}"]
    if arraystretch is not None:
        parts.append(rf"\renewcommand{{\arraystretch}}{{{arraystretch}}}")
    return "\n".join(parts)


def dense_table_begingroup() -> str:
    return (
        r"\begingroup" + "\n"
        + local_table_spacing(TABCOLSEP_DENSE, ARRAYSTRETCH_DENSE) + "\n"
    )


def analysis_table_begingroup() -> str:
    return (
        r"\begingroup" + "\n"
        + r"\footnotesize" + "\n"
        + local_table_spacing(TABCOLSEP_ANALYSIS, ARRAYSTRETCH_ANALYSIS) + "\n"
    )


def compact_table_begingroup() -> str:
    return (
        r"\begingroup" + "\n"
        + local_table_spacing(TABCOLSEP_COMPACT) + "\n"
    )


def codes_table_begingroup() -> str:
    return (
        r"\begingroup" + "\n"
        + local_table_spacing(TABCOLSEP_CODES) + "\n"
    )


def dense_table_endgroup() -> str:
    return r"\endgroup"
