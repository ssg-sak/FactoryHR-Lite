from __future__ import annotations

import io
import logging
from datetime import datetime
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.services.fonts import REGISTERED_FONT_NAME, resolve_cjk_font

logger = logging.getLogger(__name__)

NAVY = colors.HexColor("#1b2430")
TEAL = colors.HexColor("#1f4e5f")
LINE = colors.HexColor("#d7dee4")
MUTED = colors.HexColor("#5c6b7a")
SURFACE = colors.HexColor("#f4f6f8")


def _register_fonts() -> tuple[str, str | None]:
    font = resolve_cjk_font()
    if not font.available or not font.path:
        return "Helvetica", font.warning
    try:
        kwargs: dict[str, object] = {}
        if font.path.lower().endswith(".ttc"):
            kwargs["subfontIndex"] = 0
        pdfmetrics.registerFont(TTFont(REGISTERED_FONT_NAME, font.path, **kwargs))
        _configure_matplotlib(font.path)
        return REGISTERED_FONT_NAME, None
    except Exception as exc:
        warning = f"Failed to register CJK font at {font.path}: {exc}"
        logger.warning(warning)
        return "Helvetica", warning


def _configure_matplotlib(font_path: str) -> None:
    try:
        font_manager.fontManager.addfont(font_path)
        prop = font_manager.FontProperties(fname=font_path)
        plt.rcParams["font.family"] = prop.get_name()
    except Exception as exc:
        logger.warning("Matplotlib CJK font setup failed: %s", exc)
    plt.rcParams["axes.unicode_minus"] = False


def _styles(font_name: str) -> dict[str, ParagraphStyle]:
    return {
        "cover": ParagraphStyle(
            "cover", fontName=font_name, fontSize=22, leading=28, textColor=NAVY
        ),
        "subtitle": ParagraphStyle(
            "subtitle", fontName=font_name, fontSize=12, leading=16, textColor=TEAL
        ),
        "h1": ParagraphStyle(
            "h1", fontName=font_name, fontSize=14, leading=18, textColor=NAVY, spaceBefore=4, spaceAfter=8
        ),
        "body": ParagraphStyle(
            "body", fontName=font_name, fontSize=9, leading=13, textColor=NAVY
        ),
        "muted": ParagraphStyle(
            "muted", fontName=font_name, fontSize=8, leading=11, textColor=MUTED
        ),
        "small": ParagraphStyle(
            "small", fontName=font_name, fontSize=8, leading=11, textColor=NAVY
        ),
    }


def _filter_lines(payload: dict[str, Any]) -> list[str]:
    filters = payload["filters"]
    labels = filters.get("labels") or {}
    date_from = filters.get("date_from") or "시작일 없음"
    date_to = filters.get("date_to") or "종료일 없음"
    lines = [f"Report Period: {date_from} ~ {date_to}"]
    mapping = [
        ("department", "Department"),
        ("factory", "Factory"),
        ("production_line", "Production Line"),
        ("shift", "Shift"),
    ]
    for key, title in mapping:
        lines.append(f"{title}: {labels.get(key) or '전체'}")
    return lines


def _table(data: list[list[str]], font_name: str, col_widths: list[float] | None = None) -> Table:
    table = Table(data, colWidths=col_widths, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, 0), font_name),
                ("FONTNAME", (0, 1), (-1, -1), font_name),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("BACKGROUND", (0, 0), (-1, 0), TEAL),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                ("TEXTCOLOR", (0, 1), (-1, -1), NAVY),
                ("GRID", (0, 0), (-1, -1), 0.4, LINE),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, SURFACE]),
            ]
        )
    )
    return table


def _chart_image(
    labels: list[str],
    values: list[float],
    xlabel: str,
    kind: str = "barh",
) -> Image | None:
    if not labels or not values or all(v == 0 for v in values):
        return None
    fig, ax = plt.subplots(figsize=(7.1, max(2.4, 0.42 * len(labels) + 1.2)))
    if kind == "barh":
        ax.barh(labels, values, color="#1f4e5f")
        ax.invert_yaxis()
        ax.set_xlabel(xlabel)
    elif kind == "bar":
        ax.bar(labels, values, color="#1f4e5f")
        ax.set_ylabel(xlabel)
        ax.tick_params(axis="x", rotation=20)
    else:
        ax.plot(labels, values, color="#1f4e5f", marker="o", linewidth=1.6)
        ax.set_ylabel(xlabel)
        ax.tick_params(axis="x", rotation=30)
        ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=120)
    plt.close(fig)
    buffer.seek(0)
    return Image(buffer, width=170 * mm, height=min(70 * mm, (18 + 7 * len(labels)) * mm))


def _line_chart(points: list[dict[str, Any]]) -> Image | None:
    if not points:
        return None
    labels = [str(p["work_date"])[5:] for p in points]
    absence = [float(p["absence_rate"]) for p in points]
    late = [float(p["late_rate"]) for p in points]
    fig, ax = plt.subplots(figsize=(7.1, 3.2))
    ax.plot(labels, absence, label="결근 비율(%)", color="#b45309", marker="o", linewidth=1.5)
    ax.plot(labels, late, label="지각 비율(%)", color="#1f4e5f", marker="o", linewidth=1.5)
    ax.legend(frameon=False)
    ax.set_ylabel("%")
    ax.tick_params(axis="x", rotation=40)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=120)
    plt.close(fig)
    buffer.seek(0)
    return Image(buffer, width=170 * mm, height=62 * mm)


def _empty(styles: dict[str, ParagraphStyle]) -> Paragraph:
    return Paragraph("선택한 조건에 해당하는 데이터가 없습니다.", styles["muted"])


def build_workforce_pdf(payload: dict[str, Any]) -> bytes:
    font_name, font_warning = _register_fonts()
    styles = _styles(font_name)
    summary = payload["summary"]
    workforce = payload["workforce"]
    attendance = payload["attendance"]
    overtime = payload["overtime"]
    tenure = payload["tenure"]
    quality = payload["data_quality"]
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    story: list[object] = []
    story.append(Paragraph("FactoryHR Lite", styles["cover"]))
    story.append(Paragraph("Manufacturing Workforce Report", styles["subtitle"]))
    story.append(Spacer(1, 8))
    story.append(Paragraph(f"Generated At: {generated_at}", styles["body"]))
    for line in _filter_lines(payload):
        story.append(Paragraph(line, styles["body"]))
    if font_warning:
        story.append(Spacer(1, 6))
        story.append(Paragraph(f"Font warning: {font_warning}", styles["muted"]))

    story.append(PageBreak())
    story.append(Paragraph("SECTION 1. Executive Summary", styles["h1"]))
    story.append(
        Paragraph(
            "아래 수치는 선택한 필터와 기간의 attendance / employee row에서 계산합니다.",
            styles["muted"],
        )
    )
    kpi_rows = [
        ["지표", "값", "정의"],
        ["현재 재직 인원", str(summary["active_employees"]), "status=active"],
        [
            "선택 기간 퇴사 인원",
            str(summary["resigned_in_period"]),
            "resigned_at이 선택 기간에 포함",
        ],
        [
            "평균 근속 개월",
            str(summary["average_tenure_months"]),
            "근속일 / 30.4375",
        ],
        [
            "평균 잔업시간",
            str(summary["average_overtime_hours"]),
            "기간 내 overtime_hours 평균",
        ],
        [
            "결근 기록 비율(%)",
            str(summary["absence_rate"]),
            "absent / attendance records",
        ],
        [
            "지각 기록 비율(%)",
            str(summary["late_rate"]),
            "late / attendance records",
        ],
        ["근태 기록 수", str(summary["attendance_records"]), "선택 기간 attendance rows"],
    ]
    story.append(_table(kpi_rows, font_name, [40 * mm, 30 * mm, 95 * mm]))

    story.append(PageBreak())
    story.append(Paragraph("SECTION 2. Workforce Structure", styles["h1"]))
    story.append(Paragraph("재직 인원(status=active) 기준입니다. 퇴사자는 포함하지 않습니다.", styles["muted"]))
    for title, rows, unit in (
        ("공장별 재직인원", workforce["active_by_factory"], "명"),
        ("생산라인별 재직인원", workforce["active_by_line"], "명"),
        ("교대조별 재직인원", workforce["active_by_shift"], "명"),
    ):
        story.append(Paragraph(title, styles["body"]))
        chart = _chart_image(
            [item["name"] for item in rows],
            [float(item["count"]) for item in rows],
            unit,
            "barh" if "교대" not in title else "bar",
        )
        story.append(chart if chart else _empty(styles))
        story.append(Spacer(1, 8))

    story.append(PageBreak())
    story.append(Paragraph("SECTION 3. Attendance & Overtime", styles["h1"]))
    story.append(Paragraph("결근/지각 비율은 해당 날짜 attendance records 중 상태 비율입니다.", styles["muted"]))
    trend = _line_chart(attendance["points"])
    story.append(trend if trend else _empty(styles))
    story.append(Spacer(1, 8))
    story.append(Paragraph("생산라인별 평균 잔업시간", styles["body"]))
    line_ot = overtime["by_production_line"]
    chart = _chart_image(
        [item["name"] for item in line_ot],
        [float(item["average_overtime_hours"]) for item in line_ot],
        "시간",
        "bar",
    )
    story.append(chart if chart else _empty(styles))
    story.append(Paragraph("교대조별 평균 잔업시간", styles["body"]))
    shift_ot = overtime["by_shift"]
    chart = _chart_image(
        [item["name"] for item in shift_ot],
        [float(item["average_overtime_hours"]) for item in shift_ot],
        "시간",
        "bar",
    )
    story.append(chart if chart else _empty(styles))

    story.append(PageBreak())
    story.append(Paragraph("SECTION 4. Tenure / Workforce Change", styles["h1"]))
    story.append(Paragraph(str(tenure["definition"]), styles["muted"]))
    bands = tenure["bands"]
    chart = _chart_image(
        [item["label"] for item in bands],
        [float(item["count"]) for item in bands],
        "명",
        "bar",
    )
    story.append(chart if chart else _empty(styles))
    story.append(Spacer(1, 8))
    story.append(Paragraph("기간 내 퇴사 인원 (부서)", styles["body"]))
    res_dept = workforce["resignations_by_department"]
    chart = _chart_image(
        [item["name"] for item in res_dept],
        [float(item["count"]) for item in res_dept],
        "명",
        "bar",
    )
    story.append(chart if chart else _empty(styles))
    story.append(
        Paragraph(
            "이 수치는 기간 내 퇴사 인원입니다. 평균 재직인원 분모가 없어 turnover rate로 해석하지 않습니다.",
            styles["muted"],
        )
    )

    story.append(PageBreak())
    story.append(Paragraph("SECTION 5. Data Quality", styles["h1"]))
    story.append(Paragraph("DB constraint와 동일한 규칙을 다시 조회한 결과입니다. 점수는 산출하지 않습니다.", styles["muted"]))
    quality_rows = [
        ["검사 항목", "건수"],
        ["Employees", str(quality["total_employees"])],
        ["Attendance Records", str(quality["total_attendance_records"])],
        ["Duplicate Employee Numbers", str(quality["duplicate_employee_numbers"])],
        ["Duplicate Employee-Date Attendance", str(quality["duplicate_attendance"])],
        ["Invalid Work Hours", str(quality["invalid_work_hours"])],
        ["Invalid Overtime Hours", str(quality["invalid_overtime_hours"])],
        ["Attendance Before Hire Date", str(quality["attendance_before_hire_date"])],
        ["Attendance After Resignation", str(quality["attendance_after_resignation"])],
        ["Factory-Line Mismatch", str(quality["factory_line_mismatch"])],
    ]
    story.append(_table(quality_rows, font_name, [120 * mm, 45 * mm]))

    story.append(Spacer(1, 16))
    story.append(Paragraph("SECTION 6. Metric Definitions & Limitations", styles["h1"]))
    definitions = [
        "Absence Record Rate = 선택 기간 attendance records 중 attendance_status=absent 비율.",
        "Late Record Rate = 선택 기간 attendance records 중 attendance_status=late 비율.",
        "Average Overtime Hours = 선택 기간 attendance.overtime_hours 평균.",
        "Average Tenure = 재직은 hired_at~report date, 퇴사는 hired_at~resigned_at, 일수를 30.4375로 나눔.",
        "공장/라인/교대 재직인원은 현재 status=active 기준이며, 과거 배치 이력을 반영하지 않음.",
        "근태의 공장/라인/교대 속성은 기록 당시가 아니라 직원의 현재 배치를 사용함.",
        "데이터는 synthetic seed이며 출입기/ERP 연동 값이 아님.",
        "생산량, 품질, 임금, 법률/노무 판단은 포함하지 않음.",
        "상관관계는 인과관계로 해석할 수 없음.",
    ]
    for item in definitions:
        story.append(Paragraph(f"• {item}", styles["small"]))

    buffer = io.BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title="FactoryHR Lite Workforce Report",
        author="FactoryHR Lite",
    )
    document.build(story)
    return buffer.getvalue()
