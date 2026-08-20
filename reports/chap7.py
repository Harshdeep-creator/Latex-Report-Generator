import os

from osdagbridge.core.reports.report_utils import _fig_embed, simple_longtable, _tex
from osdagbridge.core.reports import styles
from osdagbridge.core.reports.report_charts import (
    parse_quantity_number,
    save_steel_tonnage_chart,
    save_concrete_vs_rebar_chart,
)


def _cell(input_dict, key, default="N.A."):
    val = input_dict.get(key, default)
    if val in (None, ""):
        val = default
    return _tex(val)


def ch7_quantities(input_dict, chart_paths=None, assets_dir=None):
    body = (
        r"1 & Structural Steel (IS 2062) for Girders & "
        + _cell(input_dict, "steel_girders_vol_formula")
        + r" & " + _cell(input_dict, "steel_girders_qty")
        + r" & " + _cell(input_dict, "steel_girders_vol_total")
        + r" & " + _cell(input_dict, "steel_girders_wt_single")
        + r" & " + _cell(input_dict, "steel_girders_wt_total")
        + r" \\" + "\n\\hline\n"
        + r"2(a) & Cross Bracing - Top Chord & "
        + _cell(input_dict, "bracing_top_vol_formula")
        + r" & " + _cell(input_dict, "bracing_top_qty")
        + r" & " + _cell(input_dict, "bracing_top_vol_total")
        + r" & " + _cell(input_dict, "bracing_top_wt_single")
        + r" & " + _cell(input_dict, "bracing_top_wt_total")
        + r" \\" + "\n\\hline\n"
        + r"2(b) & Cross Bracing - Bottom Chord & "
        + _cell(input_dict, "bracing_bot_vol_formula")
        + r" & " + _cell(input_dict, "bracing_bot_qty")
        + r" & " + _cell(input_dict, "bracing_bot_vol_total")
        + r" & " + _cell(input_dict, "bracing_bot_wt_single")
        + r" & " + _cell(input_dict, "bracing_bot_wt_total")
        + r" \\" + "\n\\hline\n"
        + r"2(c) & Cross Bracing - Diagonal Chord & "
        + _cell(input_dict, "bracing_diag_vol_formula")
        + r" & " + _cell(input_dict, "bracing_diag_qty")
        + r" & " + _cell(input_dict, "bracing_diag_vol_total")
        + r" & " + _cell(input_dict, "bracing_diag_wt_single")
        + r" & " + _cell(input_dict, "bracing_diag_wt_total")
        + r" \\" + "\n\\hline\n"
        + r"3 & Concrete (M40) for Deck Slab & "
        + _cell(input_dict, "concrete_deck_vol_formula")
        + r" & " + _cell(input_dict, "concrete_deck_qty")
        + r" & " + _cell(input_dict, "concrete_deck_vol_total")
        + r" & " + _cell(input_dict, "concrete_deck_wt_single")
        + r" & " + _cell(input_dict, "concrete_deck_wt_total")
        + r" \\" + "\n\\hline\n"
        + r"4 & Reinforcement Steel (Fe 500) & "
        + _cell(input_dict, "rebar_deck_vol_formula")
        + r" & " + _cell(input_dict, "rebar_deck_qty")
        + r" & " + _cell(input_dict, "rebar_deck_vol_total")
        + r" & " + _cell(input_dict, "rebar_deck_wt_single")
        + r" & " + _cell(input_dict, "rebar_deck_wt_total")
        + r" \\" + "\n\\hline\n"
        + r"5 & Shear Stud Connectors & "
        + _cell(input_dict, "shear_studs_vol_formula")
        + r" & " + _cell(input_dict, "shear_studs_qty")
        + r" & " + _cell(input_dict, "shear_studs_vol_total")
        + r" & " + _cell(input_dict, "shear_studs_wt_single")
        + r" & " + _cell(input_dict, "shear_studs_wt_total")
        + r" \\" + "\n\\hline\n"
        + r"6 & Crash Barrier & "
        + _cell(input_dict, "crash_barrier_vol_formula")
        + r" & " + _cell(input_dict, "crash_barrier_qty")
        + r" & " + _cell(input_dict, "crash_barrier_vol_total")
        + r" & " + _cell(input_dict, "crash_barrier_wt_single")
        + r" & " + _cell(input_dict, "crash_barrier_wt_total")
        + r" \\" + "\n\\hline"
    )

    table_tex = (
        styles.dense_table_begingroup()
        + "\n"
        + simple_longtable(
            "|C{1.0cm}|L{3.8cm}|C{2.6cm}|C{1.8cm}|C{1.8cm}|C{1.8cm}|C{1.8cm}|",
            "Bill of Materials (Steel, Concrete, and Reinforcement Quantities)",
            r"\textbf{S.N.} & \textbf{Item Description} & \textbf{Volume} & \textbf{Quantity} & \textbf{Total Volume} & \textbf{Weight (MT)} & \textbf{Total Weight (MT)} \\",
            body,
        )
        + "\n"
        + styles.dense_table_endgroup()
    )

    # Auto-generate material charts into the report assets directory
    local_paths = dict(chart_paths or {})
    if assets_dir:
        steel_series = [
            ("Girders", parse_quantity_number(input_dict.get("steel_girders_wt_total"))),
            ("CB Top", parse_quantity_number(input_dict.get("bracing_top_wt_total"))),
            ("CB Bottom", parse_quantity_number(input_dict.get("bracing_bot_wt_total"))),
            ("CB Diagonal", parse_quantity_number(input_dict.get("bracing_diag_wt_total"))),
            ("End Diaphragms", parse_quantity_number(input_dict.get("ed_wt_total"))),
        ]
        # Drop None entries for the chart helper
        steel_series = [(n, v if v is not None else 0.0) for n, v in steel_series]
        try:
            abs_steel = os.path.join(assets_dir, "steel_tonnage.png")
            if save_steel_tonnage_chart(steel_series, abs_steel):
                local_paths.setdefault("steel_tonnage", "assets/steel_tonnage.png")
        except Exception:
            pass
        try:
            abs_cr = os.path.join(assets_dir, "concrete_rebar.png")
            if save_concrete_vs_rebar_chart(
                parse_quantity_number(input_dict.get("concrete_deck_vol_total")),
                parse_quantity_number(input_dict.get("rebar_deck_wt_total")),
                abs_cr,
            ):
                local_paths.setdefault("concrete_rebar", "assets/concrete_rebar.png")
        except Exception:
            pass

    chart_tex = ""
    if local_paths.get("steel_tonnage") or local_paths.get("concrete_rebar"):
        chart_tex += (
            "\n\\vspace{1.2em}\n"
            r"\subsection*{Material Quantity Visualisation}" + "\n"
            r"\noindent The charts below summarise governing steel tonnage and "
            r"concrete / reinforcement quantities from Table~7.1." + "\n"
        )
    if local_paths.get("steel_tonnage"):
        chart_tex += "\n\\vspace{0.6em}\n" + _fig_embed(
            local_paths["steel_tonnage"],
            r"Figure --- Structural steel tonnage (girders, cross bracing, end diaphragms).",
        )
    if local_paths.get("concrete_rebar"):
        chart_tex += "\n\\vspace{0.6em}\n" + _fig_embed(
            local_paths["concrete_rebar"],
            r"Figure --- Concrete volume (m$^3$) and reinforcement steel (MT) "
            r"shown on independent axes.",
        )

    return (
        r"""
\chapter{Material Take-off \& Quantity Summary}
\label{ch:material-takeoff}

\noindent\textbf{Table 7.1  Bill of Materials (Steel, Concrete, and Reinforcement Quantities)}

"""
        + table_tex
        + chart_tex
        + "\n"
    )
