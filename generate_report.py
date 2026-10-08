import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, PageBreak, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvasCustom(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.75)
        self.line(38, 36, 595.28 - 38, 36)
        self.drawString(38, 24, "Spotter ML Engineer Assessment • Freight Rate Modeling")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(595.28 - 38, 24, page_str)
        self.restoreState()

output_pdf = "Freight_Rate_ML_Assessment_Report.pdf"
width, height = A4
margin = 38
printable_width = width - 2 * margin

styles = getSampleStyleSheet()

TEAL_DARK = colors.HexColor("#064A56")
TEAL_MED = colors.HexColor("#0D6E7E")
BORDER_COLOR = colors.HexColor("#E2E8F0")
TEXT_MAIN = colors.HexColor("#0F172A")
TEXT_MUTED = colors.HexColor("#475569")

kicker_style = ParagraphStyle("Kicker", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=8.5, leading=11, textColor=TEAL_MED, spaceAfter=2)
title_style = ParagraphStyle("MainTitle", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=18, leading=22, textColor=TEAL_DARK, spaceAfter=2)
subtitle_style = ParagraphStyle("SubTitle", parent=styles["Normal"], fontName="Helvetica", fontSize=9.5, leading=13, textColor=TEXT_MUTED, spaceAfter=4)
meta_style = ParagraphStyle("MetaBar", parent=styles["Normal"], fontName="Helvetica", fontSize=8.5, leading=12, textColor=TEXT_MAIN, spaceAfter=8)
h1_style = ParagraphStyle("SectionH1", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=11, leading=14, textColor=TEAL_DARK, spaceBefore=7, spaceAfter=4)
body_style = ParagraphStyle("BodyTextCustom", parent=styles["Normal"], fontName="Helvetica", fontSize=8.3, leading=11.4, textColor=TEXT_MAIN, spaceAfter=4)
bullet_style = ParagraphStyle("BulletCustom", parent=body_style, leftIndent=10, bulletIndent=2, spaceAfter=3)
th_style = ParagraphStyle("TH", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=7.8, leading=10, textColor=colors.white, alignment=0)
td_style = ParagraphStyle("TD", parent=styles["Normal"], fontName="Helvetica", fontSize=7.8, leading=10.5, textColor=TEXT_MAIN, alignment=0)
caption_style = ParagraphStyle("Caption", parent=styles["Normal"], fontName="Helvetica-Oblique", fontSize=7.8, leading=10, textColor=TEXT_MUTED, alignment=1, spaceBefore=3, spaceAfter=5)

doc = SimpleDocTemplate(output_pdf, pagesize=A4, leftMargin=margin, rightMargin=margin, topMargin=36, bottomMargin=44)
story = []

# --- PAGE 1 ---
story.append(Paragraph("ASSESSMENT SUBMISSION • MACHINE LEARNING ENGINEER", kicker_style))
story.append(Paragraph("Freight Rate ML Assessment Report", title_style))
story.append(Paragraph("Predictive Modeling Architecture, Validation Strategy & Out-of-Sample Performance", subtitle_style))

meta_text = (
    "<b>Candidate:</b> Dev Rathod &nbsp;&nbsp;|&nbsp;&nbsp; "
    "<b>Role:</b> Machine Learning Engineer &nbsp;&nbsp;|&nbsp;&nbsp; "
    "<b>Company:</b> Spotter &nbsp;&nbsp;|&nbsp;&nbsp; "
    "<b>Status:</b> <font color='#059669'><b>Verified via score.py</b></font>"
)
story.append(Paragraph(meta_text, meta_style))
story.append(HRFlowable(width="100%", thickness=1.2, color=TEAL_MED, spaceBefore=0, spaceAfter=6))

story.append(Paragraph("1. Executive Summary & Problem Formulation", h1_style))
exec_text = (
    "This evaluation addresses the challenge of predicting spot freight load rates (<code>posted_rate</code> in USD) across dynamic "
    "logistics networks. The objective requires learning from 48,000 historical loads spanning January through October "
    "2025, handling data quality nuances, and generating robust out-of-sample rate forecasts for 12,000 unobserved loads "
    "in November–December 2025, alongside daily December rate predictions for a fixed benchmark corridor."
)
story.append(Paragraph(exec_text, body_style))

def make_kpi_card(title, value, sub):
    return [
        Paragraph(f"<font size=7.5 color='#475569'><b>{title}</b></font>", ParagraphStyle('KPI_T', alignment=1)),
        Spacer(1, 2),
        Paragraph(f"<font size=14 color='#064A56'><b>{value}</b></font>", ParagraphStyle('KPI_V', alignment=1)),
        Spacer(1, 1),
        Paragraph(f"<font size=7 color='#64748B'>{sub}</font>", ParagraphStyle('KPI_S', alignment=1)),
    ]

kpi1 = make_kpi_card("HOLDOUT MAE", "$151.66", "Mean Absolute Error")
kpi2 = make_kpi_card("HOLDOUT RMSE", "$642.15", "Root Mean Squared Error")
kpi3 = make_kpi_card("HOLDOUT R² SCORE", "0.8229", "82.3% Variance Explained")

card_w = printable_width / 3.0 - 4
kpi_table = Table([[kpi1, kpi2, kpi3]], colWidths=[card_w, card_w, card_w])
kpi_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
    ('BOX', (0, 0), (0, 0), 1, colors.HexColor("#E2E8F0")),
    ('BOX', (1, 0), (1, 0), 1, colors.HexColor("#E2E8F0")),
    ('BOX', (2, 0), (2, 0), 1, colors.HexColor("#E2E8F0")),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('TOPPADDING', (0, 0), (-1, -1), 5),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
]))
story.append(Spacer(1, 2))
story.append(kpi_table)
story.append(Spacer(1, 4))

story.append(Paragraph("2. Validation Strategy & Leakage Prevention", h1_style))
val_p1 = (
    "In freight logistics markets, rates are heavily influenced by temporal macro trends (fuel cycles, diesel surcharges, "
    "seasonal inventory restocking, and fluctuating carrier capacity). Performing naive random K-Fold cross-validation "
    "leaks contiguous future signals into the training phase, artificially inflating accuracy while failing during forward deployment."
)
story.append(Paragraph(val_p1, body_style))

split_data = [
    [Paragraph("Dataset Phase", th_style), Paragraph("Time Horizon", th_style), Paragraph("Row Count", th_style), Paragraph("Role & Objective", th_style)],
    [Paragraph("<b>Train Window</b>", td_style), Paragraph("Jan 01, 2025 – Aug 31, 2025", td_style), Paragraph("38,400 loads", td_style), Paragraph("Base model fitting across multi-quarter seasonality", td_style)],
    [Paragraph("<b>Local Holdout Split</b>", td_style), Paragraph("Sep 01, 2025 – Oct 31, 2025", td_style), Paragraph("9,600 loads", td_style), Paragraph("Out-of-sample forward evaluation (2-month mirror)", td_style)],
    [Paragraph("<b>Blind Validation Set</b>", td_style), Paragraph("Nov 01, 2025 – Dec 31, 2025", td_style), Paragraph("12,000 loads", td_style), Paragraph("Final submission scoring file (<code>validation.csv</code>)", td_style)],
    [Paragraph("<b>December Fixed Corridor</b>", td_style), Paragraph("Dec 01, 2025 – Dec 31, 2025", td_style), Paragraph("31 daily loads", td_style), Paragraph("Fixed lane rate trajectory (Lexington → Fort Wayne)", td_style)]
]
t_split = Table(split_data, colWidths=[105, 120, 68, printable_width - 293])
t_split.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), TEAL_DARK),
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ('TOPPADDING', (0, 0), (-1, -1), 3),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
]))
story.append(t_split)
story.append(Spacer(1, 4))

story.append(Paragraph("3. Data Quality Hygiene & Imputation", h1_style))
data_q_intro = (
    "Two distinct data-quality issues were identified in the training corpus: missing cargo weight values (300 rows) and "
    "unobserved <code>market_index</code> metrics (374 rows). Rather than discarding records or using naive global means, "
    "domain-specific strategies were applied:"
)
story.append(Paragraph(data_q_intro, body_style))

dq1 = "<b>Equipment-Conditioned Weight Imputation:</b> Heavy freight payloads correlate strongly with equipment specifications. Missing weights were imputed using the median weight per equipment class (Dry Van: ~31,000 lbs, Reefer: ~33,000 lbs, Flatbed: ~35,000 lbs), preserving realistic cargo distributions."
story.append(Paragraph(f"• {dq1}", bullet_style))

dq2 = "<b>Cross-Sectional Market Signal Imputation:</b> Macro market indicators represent date-wide pricing pressure. Missing <code>market_index</code> values were imputed from the cross-sectional daily mean across contemporaneous transactions, falling back to the series median."
story.append(Paragraph(f"• {dq2}", bullet_style))

# End of Page 1
story.append(PageBreak())

# --- PAGE 2 ---
story.append(Paragraph("4. Feature Engineering & Model Architecture", h1_style))
feat_intro = "A Gradient Boosted Decision Tree (LightGBM) framework was chosen over linear baselines and deep architectures due to its native handling of categorical features, robustness against extreme outliers, and non-linear interactions across spatial and cost variables."
story.append(Paragraph(feat_intro, body_style))

feat_table_data = [
    [Paragraph("Feature Domain", th_style), Paragraph("Constructed Predictors", th_style), Paragraph("Logistics Rationale", th_style)],
    [Paragraph("<b>Geospatial Geometry</b>", td_style), Paragraph("<code>lat_diff, lon_diff, euclidean_dist</code>", td_style), Paragraph("Captures directional lane terrain and circuity beyond nominal road mileage.", td_style)],
    [Paragraph("<b>Market Interactions</b>", td_style), Paragraph("<code>dist_quote_inter, dist_market_inter</code>", td_style), Paragraph("Scales effective per-mile rate against real-time broker quoting pressure.", td_style)],
    [Paragraph("<b>Payload Density</b>", td_style), Paragraph("<code>weight_per_mile</code>", td_style), Paragraph("Quantifies equipment wear and fuel consumption penalty per distance unit.", td_style)],
    [Paragraph("<b>Calendar Seasonality</b>", td_style), Paragraph("<code>dayofweek, is_weekend, day, month</code>", td_style), Paragraph("Isolates intra-week carrier dispatch cadence and end-of-month volume spikes.", td_style)]
]
t_feat = Table(feat_table_data, colWidths=[105, 135, printable_width - 240])
t_feat.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), TEAL_DARK),
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ('TOPPADDING', (0, 0), (-1, -1), 3),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
]))
story.append(t_feat)
story.append(Spacer(1, 4))

story.append(Paragraph("5. December Fixed Corridor Trajectory Analysis", h1_style))
dec_intro = "For the 31-day December benchmark corridor (<b>Lexington → Fort Wayne</b>, 360 miles, Dry Van, 32,000 lbs), daily macro market indices and quote signals were projected from the concurrent validation time series, ensuring calibrated rate trajectories."
story.append(Paragraph(dec_intro, body_style))

# Automatically find candidate_december chart in scorer_results or current folder
chart_path = os.path.join("scorer_results", "candidate_december.png")
if not os.path.exists(chart_path):
    chart_path = "candidate_december.png"

img_w = printable_width
img_h = img_w * (626 / 1922)
story.append(RLImage(chart_path, width=img_w, height=img_h))
story.append(Paragraph("<b>Figure 1:</b> December 2025 predicted rate trajectory generated by <code>score.py</code> (Fixed Route: Lexington to Fort Wayne, 360 miles, Dry Van).", caption_style))
story.append(Spacer(1, 3))

story.append(Paragraph("6. Submission Compliance & Verification", h1_style))
comp_intro = "The complete pipeline was validated using the provided <code>score.py</code> evaluation harness without exceptions. Both deliverables meet all schema constraints:"
story.append(Paragraph(comp_intro, body_style))

c1 = "<b>VERIFIED 12,000 Final Predictions:</b> Exactly matching template schema (<code>load_id, predicted_rate</code>), strict positivity, and zero missing identifiers."
story.append(Paragraph(f"• {c1}", bullet_style))

c2 = "<b>VERIFIED 31 December Daily Forecasts:</b> Preserving original schema, monotonic chronological daily ordering, and realistic spot pricing behavior."
story.append(Paragraph(f"• {c2}", bullet_style))

c3 = "<b>REPRODUCIBILITY Single-Command Execution:</b> Deterministic seed control (<code>seed=42</code>) in <code>run_solution.py</code> ensuring complete pipeline reproducibility."
story.append(Paragraph(f"• {c3}", bullet_style))

doc.build(story, canvasmaker=NumberedCanvasCustom)
print("SUCCESS: Freight_Rate_ML_Assessment_Report.pdf created directly in your folder!")