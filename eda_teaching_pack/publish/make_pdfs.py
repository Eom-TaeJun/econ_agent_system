"""
EDA Teaching Pack — PDF 재생성 스크립트
NanumGothic 폰트 사용, reportlab Platypus 구조
"""

from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ── 폰트 등록 ──────────────────────────────────────────────
FONT_DIR = "/usr/share/fonts/truetype/nanum"
pdfmetrics.registerFont(TTFont("NanumGothic", f"{FONT_DIR}/NanumGothic.ttf"))
pdfmetrics.registerFont(TTFont("NanumGothicBold", f"{FONT_DIR}/NanumGothicBold.ttf"))
pdfmetrics.registerFontFamily(
    "NanumGothic",
    normal="NanumGothic",
    bold="NanumGothicBold",
)

# ── 색상 팔레트 ─────────────────────────────────────────────
NAVY   = colors.HexColor("#1C2833")
BLUE   = colors.HexColor("#2980B9")
TEAL   = colors.HexColor("#1A8080")
LIGHT  = colors.HexColor("#EBF5FB")
WARN   = colors.HexColor("#FEF9E7")
RED_BG = colors.HexColor("#FDEDEC")
GRAY   = colors.HexColor("#7F8C8D")
GRAY_L = colors.HexColor("#F2F3F4")
WHITE  = colors.white
BLACK  = colors.black

W, H = A4
MARGIN = 18 * mm

# ── 스타일 정의 ─────────────────────────────────────────────
def build_styles():
    s = {}
    base = dict(fontName="NanumGothic", fontSize=10, leading=16)

    s["title"] = ParagraphStyle(
        "title", fontName="NanumGothicBold", fontSize=18, leading=24,
        textColor=WHITE, spaceAfter=4,
    )
    s["subtitle"] = ParagraphStyle(
        "subtitle", fontName="NanumGothic", fontSize=10, leading=14,
        textColor=colors.HexColor("#D5E8F5"), spaceAfter=0,
    )
    s["h2"] = ParagraphStyle(
        "h2", fontName="NanumGothicBold", fontSize=12, leading=18,
        textColor=NAVY, spaceBefore=10, spaceAfter=4,
        borderPad=4, leftIndent=0,
    )
    s["h3"] = ParagraphStyle(
        "h3", fontName="NanumGothicBold", fontSize=10.5, leading=16,
        textColor=TEAL, spaceBefore=8, spaceAfter=3,
    )
    s["body"] = ParagraphStyle(
        "body", **base, textColor=BLACK, spaceAfter=4,
    )
    s["bullet"] = ParagraphStyle(
        "bullet", **base, textColor=BLACK,
        leftIndent=10, bulletIndent=0, spaceAfter=3,
    )
    s["sub_bullet"] = ParagraphStyle(
        "sub_bullet", fontName="NanumGothic", fontSize=9, leading=14,
        textColor=BLACK, leftIndent=22, bulletIndent=12, spaceAfter=2,
    )
    s["note"] = ParagraphStyle(
        "note", fontName="NanumGothic", fontSize=9, leading=14,
        textColor=colors.HexColor("#6E2F2F"), backColor=RED_BG,
        leftIndent=8, rightIndent=8, spaceBefore=4, spaceAfter=4,
        borderPad=6,
    )
    s["warn"] = ParagraphStyle(
        "warn", fontName="NanumGothic", fontSize=9, leading=14,
        textColor=colors.HexColor("#7D5A00"), backColor=WARN,
        leftIndent=8, rightIndent=8, spaceBefore=4, spaceAfter=4,
        borderPad=6,
    )
    s["table_cell"] = ParagraphStyle(
        "table_cell", fontName="NanumGothic", fontSize=9.5, leading=14,
        textColor=BLACK,
    )
    s["table_head"] = ParagraphStyle(
        "table_head", fontName="NanumGothicBold", fontSize=9.5, leading=14,
        textColor=WHITE,
    )
    s["footer"] = ParagraphStyle(
        "footer", fontName="NanumGothic", fontSize=8, leading=12,
        textColor=GRAY, alignment=TA_CENTER,
    )
    return s

S = build_styles()

# ── 헤더 배너 ───────────────────────────────────────────────
def make_header(title_text, subtitle_text):
    """네이비 배경 헤더 테이블"""
    t_row = [
        [
            Paragraph(title_text, S["title"]),
            Paragraph(subtitle_text, S["subtitle"]),
        ]
    ]
    t = Table(t_row, colWidths=[W - 2*MARGIN])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("TOPPADDING",    (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
        ("LEFTPADDING",   (0, 0), (-1, -1), 16),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 16),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return t

def section_title(text):
    return Paragraph(text, S["h2"])

def h3(text):
    return Paragraph(text, S["h3"])

def body(text):
    return Paragraph(text, S["body"])

def bullet(text, level=0):
    st = S["bullet"] if level == 0 else S["sub_bullet"]
    prefix = "•  " if level == 0 else "–  "
    return Paragraph(prefix + text, st)

def note(text):
    return Paragraph("⚠  " + text, S["note"])

def warn(text):
    return Paragraph("ℹ  " + text, S["warn"])

def hr():
    return HRFlowable(width="100%", thickness=0.5, color=GRAY, spaceAfter=6, spaceBefore=2)

def spacer(h=6):
    return Spacer(1, h)

# ── 01 문제지 ───────────────────────────────────────────────
def build_01():
    doc = SimpleDocTemplate(
        "publish/pdf/01_problem_sheet_draft.pdf",
        pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN, bottomMargin=MARGIN + 8,
        title="EDA 실습 문제지",
    )
    story = []

    story.append(make_header(
        "EDA 실습 문제지 (초안)",
        "데이터 전처리 · 결측치 · 이상치 분석 | 서울 공공자전거 수요 데이터"
    ))
    story.append(spacer(10))

    # 1. 실습 목적
    story.append(section_title("1. 실습 목적"))
    story.append(hr())
    for t in [
        "데이터 전처리, 결측치 처리, 이상치 처리의 필요성을 전/후 비교로 이해한다.",
        "시각화 결과를 근거로 분석 결론을 작성한다.",
    ]:
        story.append(bullet(t))
    story.append(spacer(8))

    # 2. 실습 데이터
    story.append(section_title("2. 실습 데이터"))
    story.append(hr())
    for t in [
        "기본 파일: <font face='NanumGothicBold'>data/raw_dirty.csv</font>",
        "비교 파일(선택): <font face='NanumGothicBold'>data/raw_clean.csv</font>",
        "주요 타깃: <font face='NanumGothicBold'>Rented Bike Count</font>",
    ]:
        story.append(bullet(t))
    story.append(spacer(8))

    # 3. 과제 문항
    story.append(section_title("3. 과제 문항"))
    story.append(hr())

    questions = [
        ("Q1. 데이터 스키마 점검",
         ["변수 타입, 행/열 수, 기초 통계량을 정리한다."],
         None),
        ("Q2. 결측치 진단",
         ["변수별 결측 비율을 계산하고 결측 패턴을 시각화한다."],
         None),
        ("Q3. 결측치 처리 전략 비교",
         ["<font face='NanumGothicBold'>drop</font>과 <font face='NanumGothicBold'>group_median</font>을 각각 적용하고 전/후 차이를 비교한다.",
          "⚠ drop 적용 시 손실 행 수와 손실 비율을 반드시 보고한다."],
         None),
        ("Q4. 이상치 탐지",
         ["아래 두 단계로 이상치 후보를 식별한다:"],
         ["1단계 — 도메인 규칙 확인: 물리적으로 불가능한 값이 있는가? (예: 대여 수 &lt; 0)",
          "2단계 — 통계 기준 적용: IQR 또는 Z-score로 극단값 식별",
          "필수 결과: 박스플롯 + 도메인 규칙 위반 건수 표"]),
        ("Q5. 이상치 처리 전략 비교",
         ["<font face='NanumGothicBold'>remove</font>와 <font face='NanumGothicBold'>cap</font>을 각각 적용하고 통계량 변화를 비교한다."],
         None),
        ("Q6. 중복/타입 오류 점검",
         ["중복 행, 날짜 파싱 오류, 비정상 범주를 점검하고 수정한다."],
         None),
        ("Q7. 파생 변수 생성",
         ["시간대, 주말/평일, 계절 등 파생 변수를 생성한다."],
         None),
        ("Q8. 핵심 질문 1",
         ["질문: 수요 피크 시간은 언제인가?",
          "처리 전/후 결과를 같은 축으로 비교한다."],
         None),
        ("Q9. 핵심 질문 2",
         ["질문: 날씨와 수요의 관계는 어떤가?",
          "상관/산점도 기반으로 해석한다."],
         None),
        ("Q10. 결론",
         ["인사이트 3개, 운영 제안 1개, 한계 2개를 작성한다."],
         None),
    ]

    for qnum, (qtitle, items, sub_items) in enumerate(questions):
        story.append(h3(qtitle))
        for it in items:
            story.append(bullet(it))
        if sub_items:
            for sit in sub_items:
                story.append(bullet(sit, level=1))
        story.append(spacer(4))

    # 4. 제출물
    story.append(section_title("4. 제출물"))
    story.append(hr())
    for t in [
        "분석 노트북 1개",
        "요약 보고서 1개 (2~4페이지)",
        "비교 시각화 6개 이상",
    ]:
        story.append(bullet(t))
    story.append(spacer(8))

    # 5. 필수 작성 규칙
    story.append(section_title("5. 필수 작성 규칙"))
    story.append(hr())
    story.append(bullet("전/후 비교 그래프는 같은 축 범위를 사용한다."))
    story.append(bullet("아래 지표를 숫자로 반드시 보고한다:"))
    for sub in ["행 수 변화", "결측률 변화", "평균/중앙값 변화", "IQR(또는 표준편차) 변화"]:
        story.append(bullet(sub, level=1))

    doc.build(story)
    print("01 done")


# ── 02 예시 및 평가기준 ─────────────────────────────────────
def build_02():
    doc = SimpleDocTemplate(
        "publish/pdf/02_example_and_rubric_draft.pdf",
        pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN, bottomMargin=MARGIN + 8,
        title="EDA 제출 예시 및 평가기준",
    )
    story = []

    story.append(make_header(
        "EDA 제출 예시 및 평가기준 (초안)",
        "기준값 raw_dirty.csv: 8,803행 / 결측 1,578셀 / 타깃 평균 230.7"
    ))
    story.append(spacer(10))

    # 1. 결과 요약표 예시
    story.append(section_title("1. 결과 요약표 예시"))
    story.append(hr())
    story.append(warn(
        "아래 기준값(처리 전)은 raw_dirty.csv 실측값입니다. "
        "처리 후 \"?\" 값은 학습자가 직접 계산합니다."
    ))
    story.append(spacer(4))

    # 요약 표
    col_w = [(W - 2*MARGIN) * r for r in [0.30, 0.175, 0.25, 0.275]]
    th = S["table_head"]
    tc = S["table_cell"]
    table_data = [
        [Paragraph("항목", th), Paragraph("처리 전", th),
         Paragraph("결측 처리 후\n(drop)", th),
         Paragraph("결측 처리 후\n(group_median)", th)],
        [Paragraph("총 행 수", tc), Paragraph("8,803", tc),
         Paragraph("?", tc), Paragraph("?", tc)],
        [Paragraph("결측 셀 수", tc), Paragraph("1,578", tc),
         Paragraph("0", tc), Paragraph("0", tc)],
        [Paragraph("타깃 평균", tc), Paragraph("230.7", tc),
         Paragraph("?", tc), Paragraph("?", tc)],
        [Paragraph("타깃 중앙값", tc), Paragraph("223.0", tc),
         Paragraph("?", tc), Paragraph("?", tc)],
        [Paragraph("타깃 IQR", tc), Paragraph("147.0", tc),
         Paragraph("?", tc), Paragraph("?", tc)],
    ]
    t = Table(table_data, colWidths=col_w)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("BACKGROUND", (0, 1), (-1, -1), GRAY_L),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, GRAY_L]),
        ("GRID",        (0, 0), (-1, -1), 0.5, colors.HexColor("#BDC3C7")),
        ("ALIGN",       (1, 0), (-1, -1), "CENTER"),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
    ]))
    story.append(t)
    story.append(note(
        "drop 전략 적용 시: Date 컬럼 결측(261행)이 타 컬럼 결측과 중복되어 "
        "실제 손실이 약 1,464행(16.6%)에 달할 수 있습니다. 손실률을 반드시 보고하세요."
    ))
    story.append(spacer(8))

    # 2. 필수 시각화
    story.append(section_title("2. 필수 시각화 목록"))
    story.append(hr())
    vizs = [
        "결측 비율 막대그래프",
        "결측 패턴 히트맵",
        "타깃 히스토그램 (전/후 비교)",
        "타깃 박스플롯 (전/후 비교)",
        "시간대별 수요 라인차트 (전/후 오버레이)",
        "기상 변수 vs 수요 산점도 또는 상관 히트맵",
    ]
    for i, v in enumerate(vizs, 1):
        story.append(bullet(f"{i}.  {v}"))
    story.append(spacer(8))

    # 3. 캡션 예시
    story.append(section_title("3. 캡션 문장 예시"))
    story.append(hr())
    for cap in [
        "결측치 단순 제거 후 표본이 3.9% 감소했고, 출근 시간대 피크가 완만해졌다.",
        "윈저라이징 적용 후 IQR이 9.2% 감소하여 극단값 영향이 줄었다.",
        "처리 전 상관계수는 과대 추정 경향을 보였고, 처리 후 관계 강도가 안정화되었다.",
    ]:
        story.append(bullet(cap))
    story.append(spacer(8))

    # 4. 채점 기준
    story.append(section_title("4. 채점 기준 (총 100점)"))
    story.append(hr())

    rubric = [
        ("4.1 데이터 진단/전처리 설계", "25점", "진단 완전성, 처리 전략 근거, 재현 가능성"),
        ("4.2 결측치/이상치 처리 실행", "25점", "최소 2개 전략 비교, 전/후 정량 보고"),
        ("4.3 시각화 품질",             "20점", "질문 대응성, 축·단위 일관성, 비교 명확성"),
        ("4.4 해석/스토리텔링",          "20점", "사실-근거-제안 구조로 인사이트 제시"),
        ("4.5 문서화/재현성",            "10점", "실행 순서와 산출물 설명의 명확성"),
    ]
    rub_w = [(W - 2*MARGIN) * r for r in [0.40, 0.12, 0.48]]
    rub_data = [[
        Paragraph("항목", th), Paragraph("배점", th), Paragraph("평가 기준", th)
    ]]
    for row in rubric:
        rub_data.append([Paragraph(row[0], tc), Paragraph(row[1], tc), Paragraph(row[2], tc)])
    rt = Table(rub_data, colWidths=rub_w)
    rt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), TEAL),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT]),
        ("GRID",        (0, 0), (-1, -1), 0.5, colors.HexColor("#BDC3C7")),
        ("ALIGN",       (1, 0), (1, -1), "CENTER"),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
    ]))
    story.append(rt)
    story.append(spacer(8))

    # 5. 감점 기준
    story.append(section_title("5. 감점 기준"))
    story.append(hr())
    for item in [
        "전/후 그래프 축 불일치: <font face='NanumGothicBold'>-3점</font>",
        "핵심 지표 누락: <font face='NanumGothicBold'>-5점</font>",
        "근거 없는 임계값 사용: <font face='NanumGothicBold'>-3점</font>",
    ]:
        story.append(bullet(item))

    doc.build(story)
    print("02 done")


# ── 03 답안 가이드 ─────────────────────────────────────────
def build_03():
    doc = SimpleDocTemplate(
        "publish/pdf/03_solution_guide_draft.pdf",
        pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN, bottomMargin=MARGIN + 8,
        title="EDA 답안 가이드",
    )
    story = []

    story.append(make_header(
        "EDA 답안 가이드 (초안)",
        "강의자용 · 학습자 미공개 권장 | 의사결정 근거 중심 해설"
    ))
    story.append(spacer(10))

    # 1. 작성 원칙
    story.append(section_title("1. 답안 작성 원칙"))
    story.append(hr())
    for t in [
        "코드보다 의사결정 근거를 우선 설명한다.",
        "전처리 전/후를 같은 질문과 같은 축으로 비교한다.",
        "결론은 정량 수치와 함께 작성한다.",
    ]:
        story.append(bullet(t))
    story.append(spacer(8))

    # 2. 문항별 답안 방향
    story.append(section_title("2. 문항별 답안 방향"))
    story.append(hr())

    qa = [
        ("Q1–Q2 진단 단계", [
            "스키마 표, 결측 비율 표, 결측 패턴 히트맵을 우선 제시한다.",
            "결측이 특정 시간대/범주에 몰려 있는지 확인한다.",
        ], None),
        ("Q3 결측치 처리", [
            "<font face='NanumGothicBold'>drop</font>과 <font face='NanumGothicBold'>group_median</font>을 둘 다 시도한다.",
            "체크포인트: drop 시 손실이 예상보다 클 수 있음 — Date 컬럼 결측이 다른 결측과 겹치기 때문.",
            "표본 손실률과 분포 왜곡을 비교해 최종 전략을 선택한다.",
        ], None),
        ("Q4–Q5 이상치 처리", [
            "먼저 도메인 규칙 위반 값을 확인한다 (예: 대여량 &lt; 0 = 물리적 불가능 값).",
            "IQR 기준 탐지 근거를 명시한다 (Q3 → Q4 순서 중요).",
            "<font face='NanumGothicBold'>remove</font>와 <font face='NanumGothicBold'>cap</font> 결과의 평균/중앙값/IQR 변화를 비교한다.",
            "희귀 이벤트 보존 필요성을 함께 논의한다.",
        ], None),
        ("Q6 데이터 오류 정리", [
            "중복 건수, 날짜 파싱 실패 건수, 비정상 범주를 보고한다.",
            "수정 전/후 레코드 예시를 최소 1개 제시한다.",
        ], None),
        ("Q7 파생 변수", [
            "시간대 구간, 주말/평일, 계절 변수를 만든다.",
            "주의: Date 결측 처리가 Q7 이전에 완료되어야 시간 기반 파생 변수 생성 가능.",
            "파생 변수로 설명력이 올라가는지 그래프로 확인한다.",
        ], None),
        ("Q8–Q9 핵심 질문 분석", [
            "질문 1: 수요 피크 시간 — 처리 전/후 오버레이 라인차트",
            "질문 2: 날씨와 수요 관계 — 상관 히트맵 + 산점도",
            "두 질문 모두 전/후 오버레이 그래프와 정량 비교를 포함한다.",
        ], None),
        ("Q10 결론", [
            "인사이트 3개, 운영 제안 1개, 분석 한계 2개를 제시한다.",
        ], None),
    ]

    for qtitle, items, _ in qa:
        story.append(h3(qtitle))
        for it in items:
            story.append(bullet(it))
        story.append(spacer(4))

    story.append(spacer(4))

    # 3. 모범 답안 템플릿
    story.append(section_title("3. 모범 답안 문장 템플릿"))
    story.append(hr())
    template_data = [
        [Paragraph("구조", S["table_head"]),
         Paragraph("예시 문장", S["table_head"])],
        [Paragraph("사실", S["table_cell"]),
         Paragraph("오전 8시와 오후 6시에 수요가 집중된다.", S["table_cell"])],
        [Paragraph("근거", S["table_cell"]),
         Paragraph("전처리 후에도 동일 패턴이 유지되며, 평균 대비 1.8배 높다.", S["table_cell"])],
        [Paragraph("제안", S["table_cell"]),
         Paragraph("해당 시간대에 자전거 재배치를 우선 배정한다.", S["table_cell"])],
    ]
    tw = [(W - 2*MARGIN) * r for r in [0.18, 0.82]]
    tt = Table(template_data, colWidths=tw)
    tt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), TEAL),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT]),
        ("GRID",     (0, 0), (-1, -1), 0.5, colors.HexColor("#BDC3C7")),
        ("VALIGN",   (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
    ]))
    story.append(tt)
    story.append(spacer(8))

    # 4. 자주 발생하는 오류
    story.append(section_title("4. 자주 발생하는 오류"))
    story.append(hr())
    for err in [
        "결측치 제거만 수행하고 손실률을 보고하지 않음",
        "이상치 임계값을 근거 없이 임의 설정",
        "그래프 축을 다르게 써서 차이를 과장",
        "인사이트에 실행 제안이 없음",
        "도메인 규칙 확인 없이 IQR만으로 이상치 판단",
    ]:
        story.append(bullet(err))

    doc.build(story)
    print("03 done")


if __name__ == "__main__":
    import os
    os.chdir(Path(__file__).resolve().parent.parent)
    build_01()
    build_02()
    build_03()
    print("모든 PDF 생성 완료")
