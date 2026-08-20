# =============================================================================
# Chart helpers for the design report (UR summary + material BOQ).
# Matplotlib (Agg) first; Pillow if Agg is unavailable.
# =============================================================================

from __future__ import annotations

import os
import sys
import tempfile
from typing import Dict, List, Optional, Sequence, Tuple

from osdagbridge.core.reports import styles

# Cached result of the first Matplotlib attempt this process (None = not tried).
_MPL_AVAILABLE: Optional[bool] = None


def _safe_float(value) -> Optional[float]:
    if value is None:
        return None
    try:
        s = str(value)
        if "textcolor" in s:
            start = s.rfind("{")
            end = s.rfind("}")
            if start != -1 and end > start:
                s = s[start + 1 : end]
        return float(s.replace(",", "").strip().split()[0])
    except (TypeError, ValueError, IndexError):
        return None


def _hex_to_rgb(hx: str) -> Tuple[int, int, int]:
    h = hx.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def _blend(c1: Tuple[int, int, int], c2: Tuple[int, int, int], t: float) -> Tuple[int, int, int]:
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


def _mpl_config_dir() -> str:
    for cand in (
        os.path.join(tempfile.gettempdir(), "osdagbridge_mplconfig"),
        os.path.join(os.getcwd(), "_mplconfig"),
    ):
        try:
            os.makedirs(cand, exist_ok=True)
            return cand
        except Exception:
            continue
    return tempfile.gettempdir()


def _try_matplotlib_bar_chart(
    labels: Sequence[str],
    values: Sequence[float],
    colors: Sequence[str],
    output_path: str,
    title: str,
    ylabel: str,
    threshold: Optional[float] = None,
    threshold_label: str = "",
    width_in: float = 9.0,
    height_in: float = 4.6,
    dpi: int = 180,
    legend_items: Optional[Sequence[Tuple[str, str]]] = None,
) -> bool:
    """Render a bar chart with Matplotlib Agg. Returns True on success."""
    global _MPL_AVAILABLE
    if _MPL_AVAILABLE is False:
        return False

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    cfg = _mpl_config_dir()
    prev_backend = os.environ.get("MPLBACKEND")
    prev_cfg = os.environ.get("MPLCONFIGDIR")
    try:
        os.environ["MPLBACKEND"] = "Agg"
        os.environ["MPLCONFIGDIR"] = cfg
        import matplotlib

        matplotlib.use("Agg", force=True)
        import matplotlib.pyplot as plt
        from matplotlib.patches import Patch

        fig, ax = plt.subplots(figsize=(width_in, height_in), dpi=dpi)
        bars = ax.bar(
            list(labels),
            [float(v) for v in values],
            color=list(colors),
            edgecolor="#263238",
            linewidth=0.6,
            width=0.55,
        )
        ax.set_title(title, fontsize=13, fontweight="bold", pad=12, color="#1C241C")
        ax.set_ylabel(ylabel, fontsize=11, color="#424A42")
        vmax = max(values) if values else 1.0
        if threshold is not None:
            vmax = max(vmax, threshold)
        ax.set_ylim(0, vmax * 1.22 if vmax > 0 else 1.0)
        ax.yaxis.grid(True, linestyle=":", alpha=0.55)
        ax.set_axisbelow(True)
        for bar, val in zip(bars, values):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height(),
                f"{float(val):.2f}",
                ha="center",
                va="bottom",
                fontsize=9,
                fontweight="bold",
            )
        if threshold is not None:
            ax.axhline(threshold, color=styles.COLOR_UR_THRESHOLD, ls="--", lw=1.8, zorder=3)
            if threshold_label:
                ax.text(
                    0.98,
                    threshold,
                    threshold_label,
                    transform=ax.get_yaxis_transform(),
                    ha="right",
                    va="bottom",
                    color=styles.COLOR_UR_THRESHOLD,
                    fontsize=9,
                    bbox=dict(
                        boxstyle="round,pad=0.25",
                        facecolor="#FFF5F5",
                        edgecolor=styles.COLOR_UR_THRESHOLD,
                        linewidth=0.8,
                    ),
                )
        if legend_items:
            ax.legend(
                handles=[
                    Patch(facecolor=c, edgecolor="#333", label=lab) for lab, c in legend_items
                ],
                loc="upper right",
                frameon=True,
                fontsize=9,
            )
        fig.tight_layout()
        fig.savefig(output_path, dpi=dpi, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        ok = os.path.isfile(output_path) and os.path.getsize(output_path) > 1000
        _MPL_AVAILABLE = ok
        return ok
    except Exception:
        _MPL_AVAILABLE = False
        return False
    finally:
        if prev_backend is None:
            os.environ.pop("MPLBACKEND", None)
        else:
            os.environ["MPLBACKEND"] = prev_backend
        if prev_cfg is None:
            os.environ.pop("MPLCONFIGDIR", None)
        else:
            os.environ["MPLCONFIGDIR"] = prev_cfg


def _font_candidates(bold: bool = False) -> List[str]:
    """Cross-platform TTF search order: bundled DejaVu first, then OS fonts."""
    names = (
        ("DejaVuSans-Bold.ttf", "Arial Bold.ttf", "arialbd.ttf", "LiberationSans-Bold.ttf")
        if bold
        else ("DejaVuSans.ttf", "Arial.ttf", "arial.ttf", "LiberationSans-Regular.ttf")
    )
    paths: List[str] = []

    # 1. Matplotlib bundled fonts (Linux / macOS / Windows / CI)
    try:
        import matplotlib

        mpl_ttf = os.path.join(os.path.dirname(matplotlib.__file__), "mpl-data", "fonts", "ttf")
        for name in names:
            paths.append(os.path.join(mpl_ttf, name))
    except Exception:
        pass

    # 2. Bare names (Pillow / fontconfig may resolve)
    paths.extend(names)

    # 3. Linux system fonts
    for root in ("/usr/share/fonts", "/usr/local/share/fonts"):
        for name in names:
            paths.append(os.path.join(root, "truetype", "dejavu", name))
            paths.append(os.path.join(root, "TTF", name))
            paths.append(os.path.join(root, name))

    # 4. macOS
    mac_dir = "/Library/Fonts"
    user_mac = os.path.expanduser("~/Library/Fonts")
    for name in names:
        paths.append(os.path.join(mac_dir, name))
        paths.append(os.path.join(user_mac, name))
    if bold:
        paths.extend(
            [
                "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
                "/Library/Fonts/Arial Bold.ttf",
            ]
        )
    else:
        paths.extend(
            [
                "/System/Library/Fonts/Supplemental/Arial.ttf",
                "/Library/Fonts/Arial.ttf",
            ]
        )

    # 5. Windows (last — never preferred on Linux CI)
    windir = os.environ.get("WINDIR", r"C:\Windows")
    win_fonts = os.path.join(windir, "Fonts")
    if bold:
        paths.extend(
            [
                os.path.join(win_fonts, "arialbd.ttf"),
                os.path.join(win_fonts, "segoeuib.ttf"),
            ]
        )
    else:
        paths.extend(
            [
                os.path.join(win_fonts, "arial.ttf"),
                os.path.join(win_fonts, "segoeui.ttf"),
            ]
        )

    # Deduplicate while preserving order
    seen: set[str] = set()
    ordered: List[str] = []
    for p in paths:
        key = p.lower() if sys.platform == "win32" else p
        if key not in seen:
            seen.add(key)
            ordered.append(p)
    return ordered


def _load_fonts():
    from PIL import ImageFont

    candidates = _font_candidates(bold=False)
    bold_candidates = _font_candidates(bold=True)

    def _try(paths, size):
        for p in paths:
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
        return ImageFont.load_default()

    return {
        "title": _try(bold_candidates, 22),
        "label": _try(candidates, 15),
        "tick": _try(candidates, 13),
        "value": _try(bold_candidates, 14),
        "legend": _try(candidates, 13),
        "axis": _try(candidates, 14),
    }


def _wrap_label(text: str, max_chars: int = 12) -> List[str]:
    words = str(text).replace("/", " / ").split()
    lines: List[str] = []
    cur = ""
    for w in words:
        trial = (cur + " " + w).strip()
        if len(trial) <= max_chars:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines or [str(text)[:max_chars]]


def _draw_rounded_rect(draw, xy, radius, fill, outline=None, width=1):
    x0, y0, x1, y1 = xy
    r = max(0, min(radius, int(min(x1 - x0, y1 - y0) / 2)))
    draw.rounded_rectangle([x0, y0, x1, y1], radius=r, fill=fill, outline=outline, width=width)


def _draw_bar_chart(
    labels: Sequence[str],
    values: Sequence[float],
    colors: Sequence[str],
    output_path: str,
    title: str,
    ylabel: str,
    threshold: Optional[float] = None,
    threshold_label: str = "",
    width: int = 1280,
    height: int = 640,
    value_fmt: str = "{:.2f}",
    legend_items: Optional[Sequence[Tuple[str, str]]] = None,
) -> str:
    if _try_matplotlib_bar_chart(
        labels, values, colors, output_path, title, ylabel,
        threshold=threshold, threshold_label=threshold_label,
        width_in=max(width / styles.CHART_DPI, 6.0),
        height_in=max(height / styles.CHART_DPI, 3.5),
        dpi=styles.CHART_DPI,
        legend_items=legend_items,
    ):
        return output_path

    from PIL import Image, ImageDraw

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    fonts = _load_fonts()

    bg = (252, 253, 250)
    grid = (232, 236, 230)
    axis = (66, 74, 66)
    title_c = (28, 36, 28)

    img = Image.new("RGB", (width, height), bg)
    draw = ImageDraw.Draw(img)

    margin_l, margin_r = 92, 48
    margin_t = 78 if legend_items else 64
    margin_b = 108
    plot_w = width - margin_l - margin_r
    plot_h = height - margin_t - margin_b

    vmax = max(values) if values else 1.0
    if threshold is not None:
        vmax = max(vmax, threshold)
    ymax = vmax * 1.22 if vmax > 0 else 1.0

    draw.text((margin_l, 18), title, fill=title_c, font=fonts["title"])

    if legend_items:
        lx = margin_l
        ly = 48
        for lab, col in legend_items:
            _draw_rounded_rect(draw, [lx, ly, lx + 14, ly + 14], 3, _hex_to_rgb(col), outline=(50, 50, 50))
            draw.text((lx + 20, ly - 1), lab, fill=axis, font=fonts["legend"])
            lx += 20 + max(70, len(lab) * 8) + 18

    x0, y0 = margin_l, margin_t + plot_h
    x1, y1 = margin_l + plot_w, margin_t

    # Soft plot panel
    _draw_rounded_rect(draw, [x0 - 8, y1 - 8, x1 + 8, y0 + 8], 10, (255, 255, 255), outline=(220, 226, 216))

    for i in range(5):
        frac = i / 4.0
        y = y0 - frac * plot_h
        val = ymax * frac
        draw.line([(x0, y), (x1, y)], fill=grid, width=1)
        draw.text((14, y - 8), f"{val:.2f}", fill=axis, font=fonts["tick"])

    draw.line([(x0, y0), (x1, y0)], fill=axis, width=2)
    draw.line([(x0, y0), (x0, y1)], fill=axis, width=2)
    draw.text((14, 42), ylabel, fill=axis, font=fonts["axis"])

    n = max(len(labels), 1)
    slot = plot_w / n
    bar_w = min(slot * 0.58, 96)

    for i, (lab, val, col) in enumerate(zip(labels, values, colors)):
        cx = x0 + (i + 0.5) * slot
        bh = (val / ymax) * plot_h if ymax else 0
        left = cx - bar_w / 2
        top = y0 - bh
        fill = _hex_to_rgb(col)
        # subtle top highlight
        _draw_rounded_rect(
            draw,
            [left, top, left + bar_w, y0],
            radius=8,
            fill=fill,
            outline=_blend(fill, (20, 20, 20), 0.25),
            width=1,
        )
        # value badge
        vtxt = value_fmt.format(val)
        tw = draw.textlength(vtxt, font=fonts["value"]) if hasattr(draw, "textlength") else len(vtxt) * 8
        bx0 = cx - tw / 2 - 6
        by0 = top - 28
        _draw_rounded_rect(draw, [bx0, by0, bx0 + tw + 12, by0 + 20], 6, (255, 255, 255), outline=fill, width=1)
        draw.text((bx0 + 6, by0 + 2), vtxt, fill=title_c, font=fonts["value"])

        lines = _wrap_label(lab, max_chars=13)
        for li, line in enumerate(lines[:3]):
            lw = draw.textlength(line, font=fonts["label"]) if hasattr(draw, "textlength") else len(line) * 7
            draw.text((cx - lw / 2, y0 + 10 + li * 16), line, fill=axis, font=fonts["label"])

    if threshold is not None:
        ty = y0 - (threshold / ymax) * plot_h
        dash_col = _hex_to_rgb(styles.COLOR_UR_THRESHOLD)
        x = x0
        while x < x1:
            draw.line([(x, ty), (min(x + 12, x1), ty)], fill=dash_col, width=3)
            x += 20
        if threshold_label:
            ttw = draw.textlength(threshold_label, font=fonts["legend"]) if hasattr(draw, "textlength") else 160
            tx = min(x1 - ttw - 8, x1 - 220)
            _draw_rounded_rect(
                draw,
                [tx - 4, ty - 22, tx + ttw + 8, ty - 4],
                5,
                (255, 245, 245),
                outline=dash_col,
            )
            draw.text((tx, ty - 20), threshold_label, fill=dash_col, font=fonts["legend"])

    # Brand accent strip
    brand = _hex_to_rgb("#" + styles.COLOR_OSDAG_GREEN)
    draw.rectangle([0, height - 6, width, height], fill=brand)

    img.save(output_path, format="PNG", optimize=True)
    return output_path


def _draw_dual_quantity_chart(
    left_label: str,
    left_value: float,
    left_unit: str,
    left_color: str,
    right_label: str,
    right_value: float,
    right_unit: str,
    right_color: str,
    output_path: str,
    title: str,
    width: int = 1280,
    height: int = 620,
) -> str:
    """Side-by-side panels with independent axes (avoids mixing m³ and MT)."""
    from PIL import Image, ImageDraw

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    fonts = _load_fonts()
    img = Image.new("RGB", (width, height), (252, 253, 250))
    draw = ImageDraw.Draw(img)
    brand = _hex_to_rgb("#" + styles.COLOR_OSDAG_GREEN)
    draw.text((48, 18), title, fill=(28, 36, 28), font=fonts["title"])

    panels = [
        (48, left_label, left_value, left_unit, left_color),
        (width // 2 + 12, right_label, right_value, right_unit, right_color),
    ]
    panel_w = width // 2 - 60
    panel_top, panel_bot = 70, height - 40

    for px, lab, val, unit, col in panels:
        _draw_rounded_rect(
            draw,
            [px, panel_top, px + panel_w, panel_bot],
            12,
            (255, 255, 255),
            outline=(220, 226, 216),
        )
        draw.text((px + 20, panel_top + 16), lab, fill=(40, 48, 40), font=fonts["axis"])
        draw.text((px + 20, panel_top + 40), f"Unit: {unit}", fill=(100, 108, 100), font=fonts["tick"])

        axis_x = px + 54
        axis_y0 = panel_bot - 50
        axis_y1 = panel_top + 90
        plot_h = axis_y0 - axis_y1
        ymax = val * 1.25 if val > 0 else 1.0

        for i in range(4):
            frac = i / 3.0
            y = axis_y0 - frac * plot_h
            draw.line([(axis_x, y), (px + panel_w - 24, y)], fill=(232, 236, 230), width=1)
            draw.text((px + 12, y - 8), f"{ymax * frac:.1f}", fill=(70, 78, 70), font=fonts["tick"])

        draw.line([(axis_x, axis_y0), (px + panel_w - 24, axis_y0)], fill=(66, 74, 66), width=2)
        draw.line([(axis_x, axis_y0), (axis_x, axis_y1)], fill=(66, 74, 66), width=2)

        bar_w = 90
        cx = px + panel_w / 2 + 10
        bh = (val / ymax) * plot_h if ymax else 0
        top = axis_y0 - bh
        fill = _hex_to_rgb(col)
        _draw_rounded_rect(
            draw,
            [cx - bar_w / 2, top, cx + bar_w / 2, axis_y0],
            10,
            fill,
            outline=_blend(fill, (20, 20, 20), 0.25),
        )
        vtxt = f"{val:.2f} {unit}"
        tw = draw.textlength(vtxt, font=fonts["value"]) if hasattr(draw, "textlength") else len(vtxt) * 8
        draw.text((cx - tw / 2, top - 26), vtxt, fill=(28, 36, 28), font=fonts["value"])

    draw.rectangle([0, height - 6, width, height], fill=brand)
    img.save(output_path, format="PNG", optimize=True)
    return output_path


def save_ur_summary_chart(
    ur_by_element: Dict[str, Optional[float]],
    output_path: str,
    title: str = "Utilization Ratio Summary — Primary Elements",
) -> Optional[str]:
    required = [
        "Steel Plate Girders",
        "Concrete Deck Slab",
        "Cross Bracing",
        "End Diaphragms",
    ]
    labels: List[str] = []
    values: List[float] = []
    colors: List[str] = []
    source = ur_by_element or {}
    for name in required:
        f = _safe_float(source.get(name))
        if f is None:
            f = 0.0
        labels.append(name)
        values.append(f)
        colors.append(styles.COLOR_UR_FAIL if f > styles.UR_THRESHOLD else styles.COLOR_UR_PASS)

    return _draw_bar_chart(
        labels,
        values,
        colors,
        output_path,
        title=title,
        ylabel="UR (Demand / Capacity)",
        threshold=styles.UR_THRESHOLD,
        threshold_label=f"UR = {styles.UR_THRESHOLD:.1f} threshold",
        width=int(styles.CHART_FIGSIZE_UR[0] * styles.CHART_DPI),
        height=int(styles.CHART_FIGSIZE_UR[1] * styles.CHART_DPI),
        legend_items=[
            ("Pass (UR ≤ 1.0)", styles.COLOR_UR_PASS),
            ("Fail (UR > 1.0)", styles.COLOR_UR_FAIL),
        ],
    )


def save_steel_tonnage_chart(
    series: Sequence[Tuple[str, float]],
    output_path: str,
    title: str = "Structural Steel Tonnage",
) -> Optional[str]:
    labels = [s[0] for s in series if s[1] is not None]
    values = [max(float(s[1]), 0.0) for s in series if s[1] is not None]
    if not labels:
        return None
    palette = [
        styles.COLOR_CHART_STEEL,
        styles.COLOR_CHART_BRACING,
        "#00695C",
        "#455A64",
        styles.COLOR_CHART_DIAPHRAGM,
    ]
    colors = [palette[i % len(palette)] for i in range(len(labels))]
    return _draw_bar_chart(
        labels,
        values,
        colors,
        output_path,
        title=title,
        ylabel="Weight (MT)",
        width=int(styles.CHART_FIGSIZE_MATERIAL[0] * styles.CHART_DPI),
        height=int(styles.CHART_FIGSIZE_MATERIAL[1] * styles.CHART_DPI),
        value_fmt="{:.2f}",
    )


def save_concrete_vs_rebar_chart(
    concrete_m3: Optional[float],
    rebar_mt: Optional[float],
    output_path: str,
    title: str = "Concrete Volume vs Reinforcement Steel",
) -> Optional[str]:
    has_c = concrete_m3 is not None and concrete_m3 > 0
    has_r = rebar_mt is not None and rebar_mt > 0
    if not has_c and not has_r:
        return None
    # Independent axes — never plot m³ and MT on one shared scale.
    return _draw_dual_quantity_chart(
        left_label="Concrete Deck Slab",
        left_value=float(concrete_m3 or 0.0),
        left_unit="m³",
        left_color=styles.COLOR_CHART_CONCRETE,
        right_label="Reinforcement Steel",
        right_value=float(rebar_mt or 0.0),
        right_unit="MT",
        right_color=styles.COLOR_CHART_REBAR,
        output_path=output_path,
        title=title,
        width=int(styles.CHART_FIGSIZE_MATERIAL[0] * styles.CHART_DPI),
        height=int(styles.CHART_FIGSIZE_MATERIAL[1] * styles.CHART_DPI),
    )


def parse_quantity_number(raw) -> Optional[float]:
    if raw is None:
        return None
    s = str(raw).strip()
    if not s or s.upper() in {"N.A.", "NA", "N/A", "---", "-"}:
        return None
    try:
        return float(s.replace(",", "").split()[0])
    except (TypeError, ValueError):
        return None
