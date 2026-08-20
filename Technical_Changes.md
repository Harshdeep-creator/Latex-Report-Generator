# Technical Changes — OsdagBridge Report Generator

Refactor of the OsdagBridge design-report generator (`core/reports/`). Scope is the six items in the screening task.

## Requirement checklist

| Requirement | Status | Where to verify |
|-------------|--------|-----------------|
| Repeating table headers on page breaks | Done | Any multi-page longtable: header row + “Continued on next page” |
| Footer overlap / vertical spacing | Done | Bottom margin 1.25 in; no row bleed into the footer rule |
| Vehicle LL table (task example) | Done | Chapter 3 — Vehicle Live Loads |
| Footpath LL table (separate, with units) | Done | Chapter 3 — Footpath Live Loads |
| Centrifugal force (units) | Done | Chapter 3 — Centrifugal Force (IRC 6 Cl. 212) |
| Vehicles from Loading tab | Done | Rows follow Additional Inputs → Loading selections |
| UR bar charts, four families, UR = 1.0 line | Done | Section 5.5 — Utilization Ratio Visualisation |
| Material quantity charts | Done | Chapter 7 — Material Quantity Visualisation |
| Centralized `styles.py` | Done | Geometry, colours, table padding, header/footer, title-page logo |
| Osdag mark on the opening page | Done | Title page |

Open **Report_Before.pdf**, then **Report_After.pdf**.

## 1. Repeated table headers

`longtable_repeating_headers()` and `simple_longtable()` in `report_utils.py` emit `\endfirsthead`, `\endhead`, `\endfoot`, and `\endlastfoot`.

`retrofit_longtables()` is applied to the assembled document in `generate_report()` so every chapter longtable, including older Chapter 2 / 4 / 5 tables, repeats its header after a page break.

## 2. Layout and footer clearance

Page bottom margin is 1.25 in. Negative footer `\vspace` that pulled body rows into the green footrule was removed. `\needspace{8\baselineskip}` is issued before `table` and `longtable`. Footer clearance and rule spacing come from `styles.py`.

## 3. Live-load tables (Chapter 3)

The former merged Live Loads / Footway block is three tables:

1. **Vehicle Live Loads (LL)** — same columns as the task example:
   Vehicle | Total Load (kN) | Impact Factor | Braking Load (Considered? / Value / Eccentricity).
   Two-row header without `\multirow`, so body cells are not painted over. Column widths fit A4.
2. **Centrifugal Force (IRC 6 Cl. 212)** — Vehicle | Considered? | Value (kN) | Radius (m) | Speed (km/h).
   Straight bridges: Considered = No. Curved: \(F = W v^2 / (127 R)\).
3. **Footpath Live Loads** — Parameter | Value | Unit | Reference.

Vehicle rows are built from Loading-tab keys (`KEY_LL_IRC_*`). Class SV braking uses `KEY_BL_IRC_CLASS_SV`. A single 70R selection is labelled **Class 70R** (as in the example); multiple 70R variants keep Wheeled / Tracked / Bogie suffixes.

Numeric cells always print a value or `---`. Totals use the same Newton → kN conversion as the analyser (`sum(wheel_loads) / kN`). Braking is the carriageway force (Cl. 211.2), shown on rows for which braking is considered.

## 4. Utilization ratio charts (Section 5.5)

After Table 5.22 a bar chart is written to `assets/ur_summary.png` and embedded. Families: Steel Plate Girders, Concrete Deck Slab, Cross Bracing, End Diaphragms. Y-axis is UR. A red dashed line is drawn at UR = 1.0. Pass/fail colouring uses `styles.COLOR_UR_PASS` / `COLOR_UR_FAIL`.

## 5. Material quantity charts (Chapter 7)

During report compile:

- Structural steel tonnage — girders, cross bracing, end diaphragms (`assets/steel_tonnage.png`)
- Concrete volume (m³) vs reinforcement steel (MT) on independent axes (`assets/concrete_rebar.png`)

Embedded with `\includegraphics`.

## 6. Centralized formatting (`styles.py`)

Single source for paper size, margins, brand colour, table padding (`TABCOLSEP`, `TABCOLSEP_COMPACT`, `TABCOLSEP_ANALYSIS`, `TABCOLSEP_CODES`), header/footer rule metrics, title-page logo width, chart colours, UR threshold, and figure widths.

Chapter files call `styles.compact_table_begingroup()`, `styles.analysis_table_begingroup()`, `styles.codes_table_begingroup()`, and `styles.local_table_spacing(...)` instead of hard-coded `\tabcolsep` values.

## Title page

The Osdag wordmark is centred on the opening page (`core/reports/assets/osdag_logo.png`), with a green rule, the OsdagBridge product line, and the project metadata table.

## Files altered

| Path | Change |
|------|--------|
| `core/reports/styles.py` | Theme, geometry, table spacing helpers, title-page metrics |
| `core/reports/report_charts.py` | UR and material charts (four UR families always plotted) |
| `core/reports/live_load_tables.py` | Vehicle / centrifugal / footpath tables |
| `core/reports/report_utils.py` | Longtable helpers and global retrofit |
| `core/reports/report_generator.py` | Styles preamble, logo resolution, title page, retrofit |
| `core/reports/chap2.py` | Compact table spacing from `styles.py` |
| `core/reports/chap3.py` | Three live-load tables |
| `core/reports/chap4.py` | Analysis table spacing from `styles.py` |
| `core/reports/chap5.py` | UR chart; compact spacing from `styles.py` |
| `core/reports/chap7.py` | Material charts |
| `core/reports/chap8.py` | Code-table spacing from `styles.py` |
| `core/reports/assets/osdag_logo.png` | Title-page mark |

## Rationale

The generator builds LaTeX as strings. Repeating headers use `longtable` `\endfirsthead` / `\endhead` (allowed by the brief) plus a document-level retrofit so every chapter table keeps its header after a page break.

The vehicle table follows the published example on A4. Centrifugal force is a separate unit-aware table so those columns stay readable without crowding the braking header.

Charts are written as PNG during compile and embedded with `\includegraphics`. Matplotlib (Agg) is preferred; Pillow is used when Agg is unavailable. Font lookup uses Matplotlib’s bundled DejaVu, then system fonts. Section 5.5 builds the UR series locally when writing the chart.

## Outputs

- `Report_Before.pdf` — baseline generator
- `Report_After.pdf` — enhanced generator
- this document — file-level log of the changes
