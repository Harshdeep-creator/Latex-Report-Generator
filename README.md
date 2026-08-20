# OsdagBridge LaTeX Report Generator

Work on the OsdagBridge design-report pipeline (`core/reports/`).

**Harshdeep Singh** · JIIT Noida · FOSSEE, IIT Bombay

## Contents

| Item | Path |
|------|------|
| Technical report | [docs/OsdagBridge_Screening_Task_Report.pdf](docs/OsdagBridge_Screening_Task_Report.pdf) |
| Video | [video/OsdagBridge_Demo_Video.mp4](video/OsdagBridge_Demo_Video.mp4) |
| Baseline design report | [design_reports/Report_Before.pdf](design_reports/Report_Before.pdf) |
| Enhanced design report | [design_reports/Report_After.pdf](design_reports/Report_After.pdf) |
| Change log | [Technical_Changes.md](Technical_Changes.md) |
| Python modules | [reports/](reports/) |

Add **Nidhikhare12** as a collaborator on the GitHub repository. Resume and NOC are submitted through the form (NOC may follow after selection).

## Layout

```
README.md
Technical_Changes.md
docs/              technical report
video/             silent walkthrough of the six report fixes
design_reports/    Report_Before.pdf, Report_After.pdf
reports/           modules for src/osdagbridge/core/reports/
```

## Scope

1. Repeating `longtable` headers
2. Footer overlap and page geometry
3. Vehicle, centrifugal, and footpath live-load tables (Loading tab)
4. Utilization-ratio charts, red dashed line at UR = 1.0
5. Chapter 7 material-quantity charts
6. Centralized formatting in [`reports/styles.py`](reports/styles.py)

`generate_report(payload, request)` in [`reports/report_generator.py`](reports/report_generator.py) is the compile entry used by **Generate Report**.
