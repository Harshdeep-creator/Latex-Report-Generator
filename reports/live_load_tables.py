# =============================================================================
# Vehicle / footpath live-load longtables for Chapter 3.
# Vehicle | Total Load | Impact Factor | Braking Load; centrifugal separate.
# Rows follow Additional Inputs → Loading tab selections.
# =============================================================================

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from osdagbridge.core.utils.common import (
    KEY_BL_IRC_CLASS_SV,
    KEY_FOOTPATH,
    KEY_LL_CUSTOM_VEHICLES,
    KEY_LL_ECCENTRICITY,
    KEY_LL_FOOTPATH_PRESSURE_MODE,
    KEY_LL_FOOTPATH_PRESSURE_VALUE,
    KEY_LL_IRC_70R_BOGIE,
    KEY_LL_IRC_70R_TRACKED,
    KEY_LL_IRC_70R_WHEELED,
    KEY_LL_IRC_AA_TRACKED,
    KEY_LL_IRC_AA_WHEELED,
    KEY_LL_IRC_CLASS_A,
    KEY_LL_IRC_CLASS_FATIGUE,
    KEY_LL_IRC_CLASS_SV,
    KEY_SPAN,
    KEY_WC_LD_LANE_TABLE_COUNT,
)
from osdagbridge.core.reports import styles
from osdagbridge.core.reports.report_utils import _tex, longtable_repeating_headers

KEY_LL_CURVE_RADIUS_M = "loading.live_load.curve_radius_m"
KEY_LL_DESIGN_SPEED_KMPH = "loading.live_load.design_speed_kmph"
_CURVE_RADIUS_ALIASES = (
    KEY_LL_CURVE_RADIUS_M,
    "geometry.horizontal_curve_radius_m",
    "geometry.curve_radius_m",
)
_DESIGN_SPEED_ALIASES = (
    KEY_LL_DESIGN_SPEED_KMPH,
    "loading.live_load.design_speed",
    "geometry.design_speed_kmph",
)

_DASH = "---"

try:
    from osdagbridge.core.utils.codes.keyfile import g, kN
except Exception:
    g, kN = 9.81, 1000.0


def _is_selected(raw: Any) -> bool:
    if raw is None:
        return False
    if raw is True:
        return True
    return str(raw).strip().lower() in ("true", "yes", "1", "checked")


def _fmt_num(value: Optional[float], nd: int = 2) -> str:
    if value is None:
        return _DASH
    try:
        return f"{float(value):.{nd}f}"
    except (TypeError, ValueError):
        return _DASH


def _force_to_kN(raw_sum: float) -> float:
    """IRC helper wheel loads are stored in Newtons (unit ``t = kN * g``)."""
    return float(raw_sum) / float(kN)


def _vehicle_total_load_kN(kind: str) -> Optional[float]:
    """Gross vehicle load (kN) from IRC:6 axle / track definitions."""
    from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017

    nominal_tonne = {
        "class_a": 55.4,
        "70r_wheeled": 100.0,
        "70r_bogie": 100.0,
        "aa_wheeled": 100.0,
        "70r_tracked": 70.0,
        "aa_tracked": 70.0,
        "class_sv": 385.0,
        "fatigue": 40.0,
    }

    try:
        if kind == "class_a":
            return _force_to_kN(sum(IRC6_2017.cl_204_1_ClassA_vehicle()["wheel_loads"]))
        if kind in ("70r_wheeled", "aa_wheeled", "70r_bogie"):
            return _force_to_kN(sum(IRC6_2017.cl_204_1_Class70R_vehicle_wheel()["wheel_loads"]))
        if kind in ("70r_tracked", "aa_tracked"):
            data = IRC6_2017.cl_204_1_Class70R_vehicle_track()
            length = float(data["x"][1] - data["x"][0])
            udl = float(data["wheel_loads_udl"])
            return _force_to_kN(udl * length * 2.0)
        if kind == "class_sv":
            return float(IRC6_2017.cl_204_5_1_special_vehicle()["total_load_kN"])
        if kind == "fatigue":
            return _force_to_kN(sum(IRC6_2017.cl_204_6_fatigue_load()["wheel_loads"]))
    except Exception:
        pass
    if kind in nominal_tonne:
        return float(nominal_tonne[kind]) * float(g)
    return None


def _impact_factor_for(kind: str, span_m: Optional[float]) -> Optional[float]:
    """Return (1 + IM) per IRC 6 Cl. 208. Steel bridges: IM = 9/(13.5+L)."""
    if span_m is None:
        return None
    from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017

    try:
        s = float(span_m)
        if kind in ("class_a", "fatigue", "class_sv"):
            return 1.0 + float(IRC6_2017.cl_208_2_impact_factor(s))

        tracked = kind in ("70r_tracked", "aa_tracked")
        if s < 9.0:
            im = 0.10 if (tracked and s >= 5.0) else 0.25
        elif s <= 45.0:
            if tracked:
                im = 0.10
            else:
                im = 0.25 if s < 23.0 else 9.0 / (13.5 + s)
        else:
            im = 9.0 / (13.5 + 45.0)
        return 1.0 + round(im, 3)
    except Exception:
        return None


def _braking_value_kN(input_dict: dict) -> Optional[float]:
    """
    IRC 6 Cl. 211.2 — braking force for the carriageway (kN), not per vehicle.

    First two lanes: 20% of one Class A train; additional lanes: +5% of 70R wheeled.
    """
    lanes = input_dict.get(KEY_WC_LD_LANE_TABLE_COUNT)
    if lanes in (None, ""):
        n = 2
    else:
        try:
            n = int(lanes)
        except (TypeError, ValueError):
            n = 2
    if n <= 0:
        return None

    class_a = _vehicle_total_load_kN("class_a") or 0.0
    r70 = _vehicle_total_load_kN("70r_wheeled") or 0.0
    braking = 0.20 * class_a
    if n > 2:
        braking += 0.05 * r70
    return float(braking)


def _curve_radius_m(input_dict: dict) -> Optional[float]:
    for key in _CURVE_RADIUS_ALIASES:
        raw = input_dict.get(key)
        if raw in (None, ""):
            continue
        try:
            r = float(raw)
            if r > 0:
                return r
        except (TypeError, ValueError):
            continue
    return None


def _design_speed_kmph(input_dict: dict) -> float:
    for key in _DESIGN_SPEED_ALIASES:
        raw = input_dict.get(key)
        if raw in (None, ""):
            continue
        try:
            v = float(raw)
            if v > 0:
                return v
        except (TypeError, ValueError):
            continue
    return 80.0


def _centrifugal_force_kN(total_load_kN: Optional[float], input_dict: dict) -> tuple[str, Optional[float]]:
    """IRC 6 Cl. 212 — F = W v^2 / (127 R)."""
    radius = _curve_radius_m(input_dict)
    if radius is None:
        return "No", None
    if total_load_kN is None:
        return "Yes", None
    v = _design_speed_kmph(input_dict)
    force = float(total_load_kN) * (v ** 2) / (127.0 * radius)
    return "Yes", force


def _eccentricity_m(input_dict: dict) -> Optional[float]:
    ecc = input_dict.get(KEY_LL_ECCENTRICITY)
    if ecc in (None, ""):
        try:
            from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017

            return float(IRC6_2017.cl_211_3_braking_force_location()["height_m"])
        except Exception:
            return 1.2
    try:
        return float(ecc)
    except (TypeError, ValueError):
        return 1.2


def _display_label(kind: str, selected_kinds: List[str]) -> str:
    """Match the task example: Class A / Class 70R / Class SV when unambiguous."""
    r70 = {"70r_wheeled", "70r_tracked", "70r_bogie"}
    aa = {"aa_wheeled", "aa_tracked"}
    if kind in r70:
        n = sum(1 for k in selected_kinds if k in r70)
        if n <= 1:
            return "Class 70R"
        return {
            "70r_wheeled": "Class 70R (Wheeled)",
            "70r_tracked": "Class 70R (Tracked)",
            "70r_bogie": "Class 70R (Bogie)",
        }[kind]
    if kind in aa:
        n = sum(1 for k in selected_kinds if k in aa)
        if n <= 1:
            return "Class AA"
        return {
            "aa_wheeled": "Class AA (Wheeled)",
            "aa_tracked": "Class AA (Tracked)",
        }[kind]
    return {
        "class_a": "Class A",
        "class_sv": "Class SV",
        "fatigue": "Class Fatigue",
    }.get(kind, kind)


def _selected_vehicle_rows(input_dict: dict) -> List[Dict[str, Any]]:
    catalog: List[Tuple[str, str, Optional[str]]] = [
        ("class_a", KEY_LL_IRC_CLASS_A, None),
        ("aa_wheeled", KEY_LL_IRC_AA_WHEELED, None),
        ("aa_tracked", KEY_LL_IRC_AA_TRACKED, None),
        ("70r_wheeled", KEY_LL_IRC_70R_WHEELED, None),
        ("70r_tracked", KEY_LL_IRC_70R_TRACKED, None),
        ("70r_bogie", KEY_LL_IRC_70R_BOGIE, None),
        ("class_sv", KEY_LL_IRC_CLASS_SV, KEY_BL_IRC_CLASS_SV),
        ("fatigue", KEY_LL_IRC_CLASS_FATIGUE, None),
    ]

    span_raw = input_dict.get(KEY_SPAN)
    try:
        span_m = float(span_raw) if span_raw not in (None, "") else None
    except (TypeError, ValueError):
        span_m = None

    braking_kN = _braking_value_kN(input_dict)
    ecc_m = _eccentricity_m(input_dict)
    radius_m = _curve_radius_m(input_dict)

    picked: List[Tuple[str, str, Optional[str]]] = [
        item for item in catalog if _is_selected(input_dict.get(item[1]))
    ]
    kinds = [k for k, _, _ in picked]

    rows: List[Dict[str, Any]] = []
    for kind, _vkey, bkey in picked:
        if bkey is not None:
            braking_yes = _is_selected(input_dict.get(bkey))
        else:
            braking_yes = True
        total_kN = _vehicle_total_load_kN(kind)
        cf_yes, cf_kN = _centrifugal_force_kN(total_kN, input_dict)
        rows.append(
            {
                "vehicle": _display_label(kind, kinds),
                "total_kN": total_kN,
                "impact": _impact_factor_for(kind, span_m),
                "braking_considered": "Yes" if braking_yes else "No",
                "braking_kN": braking_kN if braking_yes else None,
                "eccentricity_m": ecc_m if braking_yes else None,
                "centrifugal_considered": cf_yes,
                "centrifugal_kN": cf_kN,
                "radius_m": radius_m if cf_yes == "Yes" else None,
            }
        )

    custom = input_dict.get(KEY_LL_CUSTOM_VEHICLES)
    if custom and isinstance(custom, list):
        for c in custom:
            if isinstance(c, dict) and c.get("name"):
                name = str(c["name"])
                impact = c.get("impact_factor")
                try:
                    impact_f = 1.0 + float(impact) if impact not in (None, "") else None
                except (TypeError, ValueError):
                    impact_f = None
                total = c.get("total_load_kN") or c.get("gross_load_kN")
                try:
                    total_f = float(total) if total not in (None, "") else None
                except (TypeError, ValueError):
                    total_f = None
                cf_yes, cf_kN = _centrifugal_force_kN(total_f, input_dict)
                rows.append(
                    {
                        "vehicle": name,
                        "total_kN": total_f,
                        "impact": impact_f,
                        "braking_considered": "Yes",
                        "braking_kN": braking_kN,
                        "eccentricity_m": ecc_m,
                        "centrifugal_considered": cf_yes,
                        "centrifugal_kN": cf_kN,
                        "radius_m": radius_m if cf_yes == "Yes" else None,
                    }
                )
            elif isinstance(c, str) and c.strip():
                cf_yes, cf_kN = _centrifugal_force_kN(None, input_dict)
                rows.append(
                    {
                        "vehicle": c.strip(),
                        "total_kN": None,
                        "impact": None,
                        "braking_considered": "Yes",
                        "braking_kN": braking_kN,
                        "eccentricity_m": ecc_m,
                        "centrifugal_considered": cf_yes,
                        "centrifugal_kN": cf_kN,
                        "radius_m": radius_m if cf_yes == "Yes" else None,
                    }
                )

    return rows


def build_vehicle_live_load_table(input_dict: dict) -> str:
    """
    Spec example columns:

      Vehicle | Total Load (kN) | Impact Factor |
      Braking Load [Considered? | Value | Eccentricity]
    """
    rows = _selected_vehicle_rows(input_dict)
    if not rows:
        body = (
            r"\multicolumn{6}{|c|}{\textit{No vehicle live loads selected in "
            r"Additional Inputs \,$\rightarrow$\, Loading tab.}} \\" + "\n"
            + r"\hline"
        )
    else:
        parts = []
        for r in rows:
            parts.append(
                _tex(r["vehicle"])
                + r" & " + _fmt_num(r["total_kN"])
                + r" & " + _fmt_num(r["impact"], nd=3)
                + r" & " + _tex(r["braking_considered"])
                + r" & " + _fmt_num(r["braking_kN"])
                + r" & " + _fmt_num(r["eccentricity_m"], nd=2)
                + styles.ROW_SKIP + "\n"
                + r"\hline"
            )
        body = "\n".join(parts)

    # Fits A4 with 1 in margins; no multirow (avoids header overlay on body cells).
    col_spec = "|L{2.8cm}|C{2.3cm}|C{2.3cm}|C{2.4cm}|C{2.3cm}|C{2.6cm}|"
    header = r"""\hline
\textbf{Vehicle} & \textbf{Total Load} & \textbf{Impact Factor} &
\multicolumn{3}{c|}{\textbf{Braking Load}} \\
\cline{4-6}
& \textbf{(kN)} & & \textbf{Considered?} & \textbf{Value} & \textbf{Eccentricity} \\
\hline"""

    return longtable_repeating_headers(
        col_spec,
        r"\caption{\textbf{Vehicle Live Loads (LL)}}",
        header,
        body,
    )


def build_centrifugal_force_table(input_dict: dict) -> str:
    """Separate centrifugal-force table with explicit units (IRC 6 Cl. 212)."""
    rows = _selected_vehicle_rows(input_dict)
    radius = _curve_radius_m(input_dict)
    speed = _design_speed_kmph(input_dict) if radius is not None else None

    if not rows:
        body = (
            r"\multicolumn{5}{|c|}{\textit{No vehicle live loads selected.}} \\" + "\n"
            + r"\hline"
        )
    else:
        parts = []
        for r in rows:
            parts.append(
                _tex(r["vehicle"])
                + r" & " + _tex(r["centrifugal_considered"])
                + r" & " + _fmt_num(r["centrifugal_kN"])
                + r" & " + _fmt_num(r["radius_m"])
                + r" & " + (_fmt_num(speed, nd=0) if r["centrifugal_considered"] == "Yes" else _DASH)
                + styles.ROW_SKIP + "\n"
                + r"\hline"
            )
        body = "\n".join(parts)

    col_spec = "|L{3.4cm}|C{2.6cm}|C{2.6cm}|C{2.8cm}|C{2.8cm}|"
    header = r"""\hline
\textbf{Vehicle} & \textbf{Considered?} & \textbf{Value (kN)} &
\textbf{Radius (m)} & \textbf{Speed (km/h)} \\
\hline"""

    return longtable_repeating_headers(
        col_spec,
        r"\caption{\textbf{Centrifugal Force (IRC 6 Cl.\ 212)}}",
        header,
        body,
    )


def build_footpath_live_load_table(input_dict: dict) -> str:
    """Separate footpath / footway live-load table with explicit units."""
    from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017

    fp_config = input_dict.get(KEY_FOOTPATH, "")
    fp_mode = input_dict.get(KEY_LL_FOOTPATH_PRESSURE_MODE, "")
    fp_value = input_dict.get(KEY_LL_FOOTPATH_PRESSURE_VALUE, "")

    cfg = str(fp_config).strip().lower() if fp_config not in (None, "") else ""
    if cfg in ("none", "no", "0", ""):
        applicable = "No"
        pressure = _DASH
        mode_disp = _DASH
        note = "Footpath not provided"
    else:
        applicable = "Yes"
        mode_l = str(fp_mode).strip().lower()
        if mode_l in ("as per irc 6", "as per irc6", "automatic"):
            try:
                pressure = f"{IRC6_2017.cl_206_1_footway_load():.3f}"
            except Exception:
                pressure = _DASH
            mode_disp = "As per IRC 6 Cl. 206.1"
            note = "Default footway pressure"
        elif fp_value not in (None, ""):
            pressure = _tex(fp_value)
            mode_disp = "Custom"
            note = "User-specified pressure"
        else:
            pressure = _DASH
            mode_disp = _tex(fp_mode) if fp_mode else _DASH
            note = _DASH

    config_disp = _tex(fp_config) if fp_config not in (None, "") else _DASH

    body = (
        r"Footpath configuration & " + config_disp + r" & --- & --- \\" + "\n\\hline\n"
        + r"Footpath live load applicable? & " + applicable + r" & --- & --- \\" + "\n\\hline\n"
        + r"Pressure mode & " + mode_disp + r" & --- & " + _tex(note) + r" \\" + "\n\\hline\n"
        + r"Footway live load intensity & " + pressure
        + r" & kN/m\textsuperscript{2} & IRC 6 Cl. 206.1 \\" + "\n\\hline"
    )

    col_spec = "|L{5.2cm}|C{3.2cm}|C{2.4cm}|L{4.0cm}|"
    header = r"""\hline
\textbf{Parameter} & \textbf{Value} & \textbf{Unit} & \textbf{Reference / Note} \\
\hline"""

    return longtable_repeating_headers(
        col_spec,
        r"\caption{\textbf{Footpath Live Loads}}",
        header,
        body,
    )
