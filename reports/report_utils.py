from osdagbridge.core.utils.common import (
    KEY_MP_GD_MEMBER_ID,
    KEY_MP_GD_SELECT_GIRDER,
    KEY_MP_GIRDER_DEPTH,
    KEY_TS_NO_OF_GIRDERS
)
from osdagbridge.core.reports import styles


def _tex(value):
    """Escape a Python value for safe LaTeX embedding."""
    s = str(value) if value is not None else ''
    if not s:
        return r''
    # Normalise non-ASCII glyphs from section designations (e.g. "∠ 100 ⅹ 100ⅹ 10")
    # that pdflatex cannot render.
    for uni, ascii_ in [('∠', 'L'), ('ⅹ', 'x'), ('×', 'x')]:
        s = s.replace(uni, ascii_)
    s = s.replace('\\', r'\textbackslash{}')
    for ch, esc in [('&', r'\&'), ('%', r'\%'), ('$', r'\$'), ('#', r'\#'),
                    ('{', r'\{'), ('}', r'\}'),
                    ('_', r'\_\allowbreak{}'),
                    ('~', r'\textasciitilde{}'), ('^', r'\^{}')]:
        s = s.replace(ch, esc)
    s = s.replace(':', r':\allowbreak{}')
    return s


def _render_value(source_dict, key, unit=""):
    val = source_dict.get(key)
    if val in ("", None):
        return ""
    return _tex(val) + unit


def get_girder_entries(input_dict):
    """
    Retrieve all girder labels and member IDs from backend keys.

    Usage Example:
    --------------------------
    girder_entries = get_girder_entries(bridge.input_dict)

    # 1. Fallback handling (if backend hasn't populated keys yet)
    if not girder_entries:
        n = int(bridge.input_dict.get(KEY_TS_NO_OF_GIRDERS, 1))
        girder_entries = [(f"Girder {i}", f"M1") for i in range(1, n + 1)]

    # 2. Get total number of girders safely
    n_girders = len(girder_entries)

    # 3. Iterate over the girders to build table rows
    for lbl, mid in girder_entries:
        # lbl will be e.g., "G1", mid will be e.g., "G1M1"
        # Access girder specific keys dynamically:
        # val = input_dict.get(f"{KEY_MP_GIRDER_DEPTH}.{lbl}.{mid}")
        pass

    Returns:
        List[Tuple[str, str]]
    """
    try:
        n = int(input_dict.get(KEY_TS_NO_OF_GIRDERS, 0) or 0)
    except (TypeError, ValueError):
        n = 0

    entries = []
    for i in range(1, n + 1):
        lbl = input_dict.get(f"{KEY_MP_GD_SELECT_GIRDER}.G{i}", "")
        mid = input_dict.get(f"{KEY_MP_GD_MEMBER_ID}.G{i}.M1", "")
        # Backend may set girder count before labels — never return blank IDs
        # (blank labels produce empty \\makecell{} multirows in Ch2/Ch5).
        if not str(lbl).strip():
            lbl = f"G{i}"
        if not str(mid).strip():
            mid = f"G{i}M1"
        entries.append((lbl, mid))

    return entries


def longtable_repeating_headers(
    col_spec: str,
    caption: str,
    header_latex: str,
    body_latex: str,
    *,
    continued_caption: str | None = None,
) -> str:
    """
    Build a longtable with repeating column headers on every page break.

    ``header_latex`` should include leading/trailing ``\\hline`` around the
    header row(s). ``caption`` may be a plain title or a full ``\\caption{...}``.
    """
    if caption.startswith(r"\caption"):
        first_cap = caption
        # Build a continued caption by injecting " (continued)" before the closing brace
        if continued_caption is not None:
            cont_cap = continued_caption
        else:
            if caption.endswith("}"):
                cont_cap = caption[:-1] + r" (continued)}"
                # Switch to \caption[] so the continued page is not re-listed in LoT
                if cont_cap.startswith(r"\caption{"):
                    cont_cap = r"\caption[]{" + cont_cap[len(r"\caption{"):]
                elif cont_cap.startswith(r"\caption["):
                    pass
            else:
                cont_cap = caption + r" (continued)"
    else:
        first_cap = rf"\caption{{\textbf{{{caption}}}}}"
        cont_cap = continued_caption or rf"\caption[]{{\textbf{{{caption} (continued)}}}}"

    n_cols = _col_count(col_spec)
    return (
        rf"\begin{{longtable}}{{{col_spec}}}" + "\n"
        + first_cap + r"\\" + "\n"
        + header_latex + "\n"
        + r"\endfirsthead" + "\n"
        + cont_cap + r"\\" + "\n"
        + header_latex + "\n"
        + r"\endhead" + "\n"
        + r"\hline" + "\n"
        + rf"\multicolumn{{{n_cols}}}{{r}}{{\footnotesize\textit{{Continued on next page}}}}\\" + "\n"
        + r"\endfoot" + "\n"
        + r"\endlastfoot" + "\n"
        + body_latex + "\n"
        + r"\end{longtable}"
    )


def _col_count(col_spec: str) -> str:
    """Best-effort column count from a longtable column specification."""
    depth = 0
    count = 0
    for ch in col_spec:
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth = max(0, depth - 1)
        elif depth == 0 and ch in "lcrLCRXm":
            count += 1
    return str(max(count, 1))


def simple_longtable(
    col_spec: str,
    caption: str,
    header_row: str,
    body_rows: str,
) -> str:
    """
    Longtable with a single repeating header row.

    ``header_row`` example:
        r"\\textbf{parameter} & \\textbf{value} \\\\[6pt]"
    """
    header = (
        r"\hline" + "\n"
        + header_row + "\n"
        + r"\hline"
    )
    return longtable_repeating_headers(col_spec, caption, header, body_rows)


def _matching_brace(s: str, open_idx: int) -> int:
    """Return index just past the matching ``}`` for ``s[open_idx] == '{'``."""
    depth = 0
    for i in range(open_idx, len(s)):
        if s[i] == "{":
            depth += 1
        elif s[i] == "}":
            depth -= 1
            if depth == 0:
                return i + 1
    return -1


def _ensure_longtable_endfoot(col_spec: str, inner: str) -> str:
    """If a longtable already has endfirsthead/endhead but no endfoot, add it."""
    if r"\endfoot" in inner:
        return inner
    n_cols = _col_count(col_spec)
    foot = (
        r"\hline" + "\n"
        + rf"\multicolumn{{{n_cols}}}{{r}}{{\footnotesize\textit{{Continued on next page}}}}\\" + "\n"
        + r"\endfoot" + "\n"
        + r"\endlastfoot" + "\n"
    )
    marker = r"\endhead"
    idx = inner.find(marker)
    if idx < 0:
        return inner
    insert_at = idx + len(marker)
    # skip trailing newline after \endhead
    while insert_at < len(inner) and inner[insert_at] in "\r\n":
        insert_at += 1
    return inner[:insert_at] + foot + inner[insert_at:]


def _split_caption_header_body(inner: str):
    """
    Split a raw longtable body into (caption, header_with_hlines, body_rows).

    Supports the common chapter pattern::

        \\caption{...}
        \\hline
        <header row(s) containing \\textbf{...}>
        \\hline
        <body>
    """
    import re

    s = inner.lstrip("\n")
    caption = ""
    rest = s

    if rest.startswith(r"\caption"):
        brace = rest.find("{")
        if brace != -1:
            end = _matching_brace(rest, brace)
            if end != -1:
                caption = rest[:end].rstrip()
                rest = rest[end:].lstrip()
                if rest.startswith(r"\\"):
                    rest = rest[2:].lstrip()

    # Prefer header blocks that include at least one \textbf (column titles).
    m = re.match(
        r"(\\hline[ \t]*\n(?:.*\\textbf[\s\S]*?\n)+\\hline[ \t]*\n)([\s\S]*)",
        rest,
    )
    if m:
        return caption, m.group(1).strip(), m.group(2).strip()

    # Fallback: no identifiable bold header (e.g. stiffener summary) —
    # keep a single rule and put everything in the body.
    if rest.startswith(r"\hline"):
        return caption, r"\hline", rest
    return caption, r"\hline", rest


def retrofit_longtables(tex: str) -> str:
    """
    Ensure every ``longtable`` in ``tex`` repeats headers across page breaks.

    - Tables that already use ``\\endfirsthead`` get an ``\\endfoot`` if missing.
    - Raw chapter tables (caption + header + body) are rebuilt via
      ``longtable_repeating_headers``.
    """
    token = r"\begin{longtable}"
    out: list[str] = []
    pos = 0
    n = len(tex)

    while pos < n:
        i = tex.find(token, pos)
        if i < 0:
            out.append(tex[pos:])
            break
        out.append(tex[pos:i])
        j = i + len(token)
        while j < n and tex[j].isspace():
            j += 1
        if j >= n or tex[j] != "{":
            out.append(tex[i:i + len(token)])
            pos = i + len(token)
            continue
        spec_end = _matching_brace(tex, j)
        if spec_end < 0:
            out.append(tex[i:])
            break
        col_spec = tex[j + 1 : spec_end - 1]
        end_tok = r"\end{longtable}"
        end_i = tex.find(end_tok, spec_end)
        if end_i < 0:
            out.append(tex[i:])
            break
        inner = tex[spec_end:end_i]

        if r"\endfirsthead" in inner:
            fixed_inner = _ensure_longtable_endfoot(col_spec, inner)
            out.append(token + "{" + col_spec + "}" + fixed_inner + end_tok)
        else:
            caption, header, body = _split_caption_header_body(inner)
            if not caption:
                caption = r"\caption{}"
            out.append(
                longtable_repeating_headers(col_spec, caption, header, body)
            )
        pos = end_i + len(end_tok)

    return "".join(out)


def _fig_or_placeholder(path, caption, width=None):
    """Embed figure if path is provided (file already copied to assets), else show placeholder box.
    path is the relative path as pdflatex will see it (e.g. 'assets/plan.png').
    """
    if width is None:
        width = styles.FIGURE_WIDTH_DEFAULT
    if path:
        p = path.replace('\\', '/')
        return (r'\begin{figure}[H]' + '\n'
                r'\centering' + '\n'
                r'\includegraphics[width=' + width + ']{' + p + '}\n'
                r'\caption*{' + caption + '}\n'
                r'\end{figure}')
    return (r'\begin{figure}[H]' + '\n'
            r'\centering' + '\n'
            r'\fbox{\parbox{0.97\textwidth}{' + '\n'
            r'\textit{[ PLACEHOLDER: ' + caption + r' ]}' + '\n'
            r'}}' + '\n'
            r'\caption*{' + caption + '}\n'
            r'\end{figure}')


def _fig_embed(path, caption, width=None, height=None):
    """Embed a real figure when path is provided (already copied); otherwise use an fbox placeholder."""
    if width is None:
        width = styles.FIGURE_WIDTH_DEFAULT
    if path:
        p = path.replace('\\', '/')
        opts = 'width=' + width
        if height:
            opts += ',height=' + height + ',keepaspectratio'
        # Avoid negative vspace — it was a source of footer/table overlap.
        return (r'\begin{figure}[H]' + '\n'
                r'\centering' + '\n'
                r'\includegraphics[' + opts + ']{' + p + '}\n'
                rf'\vspace{{{styles.FIGURE_CAPTION_SKIP_BEFORE}}}' + '\n'
                r'\caption*{\small ' + caption + '}\n'
                rf'\vspace{{{styles.FIGURE_CAPTION_SKIP_AFTER}}}' + '\n'
                r'\end{figure}')
    # fbox placeholder — matches template exactly
    return (r'\noindent\fbox{\parbox{0.97\textwidth}{' + '\n'
            r'\textit{[ PLACEHOLDER: ' + caption + r' ]}' + '\n'
            r'}}')


