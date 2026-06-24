import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date
import re

st.set_page_config(
    page_title="Health Hunters",
    page_icon="🩺",
    layout="wide"
)

DB_PATH = "health_hunters.db"

# -----------------------------
# Database
# -----------------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS symptom_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            log_date TEXT,
            pain_score INTEGER,
            fatigue_score INTEGER,
            medication_taken TEXT,
            sleep_hours REAL,
            memo TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()


def save_log(log_date, pain_score, fatigue_score, medication_taken, sleep_hours, memo):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO symptom_logs
        (log_date, pain_score, fatigue_score, medication_taken, sleep_hours, memo, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        str(log_date), pain_score, fatigue_score, medication_taken,
        sleep_hours, memo, datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    conn.commit()
    conn.close()


def load_logs():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM symptom_logs ORDER BY log_date", conn)
    conn.close()
    if not df.empty:
        df["log_date"] = pd.to_datetime(df["log_date"])
    return df


init_db()

# -----------------------------
# Simple rule-based AI demo
# -----------------------------
MEDICAL_TERMS = {
    "CKD": "만성신장질환",
    "eGFR": "신장 기능을 보여주는 검사 수치",
    "Cr": "크레아티닌, 신장 기능과 관련된 수치",
    "Hb": "헤모글로빈, 빈혈 여부를 보는 수치",
    "BP": "혈압",
    "HTN": "고혈압",
    "DM": "당뇨병",
    "CHF": "심부전",
    "LDL": "나쁜 콜레스테롤",
    "TG": "중성지방",
    "F/U": "추적관찰",
    "FU": "추적관찰",
    "q.d": "하루 한 번",
    "bid": "하루 두 번",
    "tid": "하루 세 번",
    "po": "먹는 약",
    "prn": "필요할 때 복용",
}


def explain_chart(text: str):
    if not text.strip():
        return "입력된 진료 내용이 없습니다.", []

    found_terms = []
    for term, meaning in MEDICAL_TERMS.items():
        if re.search(rf"\b{re.escape(term)}\b", text, re.IGNORECASE):
            found_terms.append((term, meaning))

    lower_text = text.lower()
    explanations = []

    if "ckd" in lower_text or "egfr" in lower_text or "신장" in text:
        explanations.append("신장 기능을 정기적으로 확인해야 하는 상태일 수 있습니다. 검사 수치 변화와 복약 여부를 꾸준히 기록하는 것이 중요합니다.")
    if "dm" in lower_text or "당뇨" in text or "glucose" in lower_text:
        explanations.append("혈당 관리가 필요한 내용이 포함되어 있습니다. 식사, 운동, 복약 기록을 함께 관리하면 다음 진료에 도움이 됩니다.")
    if "htn" in lower_text or "bp" in lower_text or "혈압" in text:
        explanations.append("혈압 관리와 관련된 내용이 있습니다. 가정 혈압 기록과 약 복용 여부를 함께 확인하는 것이 좋습니다.")
    if "pain" in lower_text or "통증" in text:
        explanations.append("통증 변화가 중요한 관찰 항목입니다. 통증 점수를 매일 기록하면 증상 변화를 의료진에게 설명하기 쉽습니다.")
    if "암" in text or "cancer" in lower_text or "chemo" in lower_text:
        explanations.append("장기 추적관찰이 필요한 질환 관련 내용이 포함되어 있습니다. 증상 변화, 복약, 식사 상태를 기록해 두는 것이 좋습니다.")

    if not explanations:
        explanations.append("입력된 진료 내용을 쉬운 말로 정리하면, 현재 상태를 꾸준히 관찰하고 다음 진료 때 변화 내용을 의료진에게 전달하는 것이 중요합니다.")

    summary = "\n\n".join(explanations)
    return summary, found_terms


def make_care_guide(text: str):
    lower_text = text.lower()
    guides = [
        "처방받은 약은 임의로 중단하지 말고 정해진 시간에 복용하세요.",
        "증상 변화가 있으면 날짜와 함께 간단히 기록하세요.",
        "다음 진료 전 최근 증상, 복약 여부, 궁금한 점을 정리하세요."
    ]

    if "ckd" in lower_text or "egfr" in lower_text or "신장" in text:
        guides += ["염분 섭취를 줄이고, 의료진이 안내한 수분 섭취 기준을 따르세요.", "부종, 소변량 변화, 심한 피로감을 기록하세요."]
    if "dm" in lower_text or "당뇨" in text or "glucose" in lower_text:
        guides += ["식사 시간과 혈당 변화를 함께 기록하세요.", "무리하지 않는 범위에서 규칙적인 걷기 운동을 실천하세요."]
    if "htn" in lower_text or "bp" in lower_text or "혈압" in text:
        guides += ["가능하면 매일 같은 시간에 혈압을 측정하세요.", "짠 음식과 과도한 카페인 섭취를 줄이세요."]
    if "암" in text or "cancer" in lower_text or "chemo" in lower_text:
        guides += ["식욕, 체중 변화, 통증, 피로감을 꾸준히 기록하세요.", "발열이나 심한 통증 등 이상 증상이 있으면 의료진에게 문의하세요."]

    return guides


# -----------------------------
# UI
# -----------------------------
st.sidebar.title("Health Hunters")
menu = st.sidebar.radio(
    "메뉴",
    ["서비스 소개", "차트 해설", "증상 기록", "리포트", "재진 준비 요약"]
)

st.sidebar.info("본 서비스는 진단·처방을 제공하지 않으며, 환자의 이해와 자기관리를 돕는 보조 서비스입니다.")

if menu == "서비스 소개":
    st.title("🩺 Health Hunters")
    st.subheader("장기관리 환자를 위한 AI 기반 진료 차트 해설 및 환자 참여 유도 서비스")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("핵심 기능", "차트 쉬운 설명")
    with col2:
        st.metric("관리 기능", "복약·증상 기록")
    with col3:
        st.metric("진료 준비", "요약 리포트")

    st.markdown("""
    ### 서비스 목적
    진료실에서 받은 차트, 검사결과, 소견서는 전문용어가 많아 환자가 이해하기 어렵습니다.  
    Health Hunters는 의료진의 진단과 처방을 대체하지 않고, 환자가 자신의 기록을 쉽게 이해하고
    진료 사이 기간 동안 복약과 증상을 기록할 수 있도록 돕습니다.

    ### 주요 사용자
    - 암, 심부전, 만성신장질환 등 장기 추적관찰 환자
    - 당뇨, 고혈압 등 지속적 자기관리가 필요한 만성질환자
    - 환자를 함께 돌보는 보호자

    ### 핵심 메시지
    **진단은 의료진이, AI는 환자의 이해와 참여를 돕습니다.**
    """)

elif menu == "차트 해설":
    st.title("📄 AI 진료 차트 쉬운 설명")
    st.caption("데모 버전에서는 문장을 직접 입력하면 규칙 기반으로 쉬운 설명을 제공합니다.")

    sample = "CKD Stage 3, eGFR 감소. BP 조절 필요. F/U 권고."
    chart_text = st.text_area("진료 차트 또는 검사결과 내용을 입력하세요", value=sample, height=180)

    uploaded_file = st.file_uploader("또는 파일 업로드 데모 PDF / 이미지 / TXT", type=["txt", "pdf", "png", "jpg", "jpeg"])
    if uploaded_file is not None:
        if uploaded_file.type == "text/plain":
            chart_text = uploaded_file.read().decode("utf-8")
            st.success("TXT 파일 내용을 불러왔습니다.")
        else:
            st.warning("현재 MVP에서는 PDF/이미지 업로드 UI만 제공하며, 텍스트 추출은 추후 OCR 기능으로 확장 예정입니다.")

    if st.button("쉬운 설명 생성"):
        summary, terms = explain_chart(chart_text)
        guides = make_care_guide(chart_text)

        st.session_state["last_chart_text"] = chart_text
        st.session_state["last_summary"] = summary
        st.session_state["last_guides"] = guides
        st.session_state["last_terms"] = terms

        st.subheader("AI 쉬운 설명")
        st.success(summary)

        st.subheader("의료 용어 풀이")
        if terms:
            term_df = pd.DataFrame(terms, columns=["용어", "쉬운 설명"])
            st.dataframe(term_df, use_container_width=True)
        else:
            st.write("인식된 주요 약어가 없습니다.")

        st.subheader("오늘의 생활관리 가이드")
        for guide in guides:
            st.write(f"✅ {guide}")

elif menu == "증상 기록":
    st.title("📝 오늘의 증상 기록")

    with st.form("symptom_form"):
        log_date = st.date_input("기록 날짜", value=date.today())
        pain_score = st.slider("통증 정도", 0, 10, 3)
        fatigue_score = st.slider("피로 정도", 0, 10, 4)
        medication_taken = st.radio("오늘 약을 복용했나요?", ["예", "아니오", "해당 없음"], horizontal=True)
        sleep_hours = st.number_input("수면 시간", min_value=0.0, max_value=24.0, value=7.0, step=0.5)
        memo = st.text_area("메모", placeholder="예: 어제보다 피로감이 줄었음, 식욕 저하 있음")
        submitted = st.form_submit_button("기록 저장")

    if submitted:
        save_log(log_date, pain_score, fatigue_score, medication_taken, sleep_hours, memo)
        st.success("오늘의 기록이 저장되었습니다.")

elif menu == "리포트":
    st.title("📊 자기관리 리포트")
    df = load_logs()

    if df.empty:
        st.info("아직 저장된 증상 기록이 없습니다. 먼저 '증상 기록' 메뉴에서 데이터를 입력하세요.")
    else:
        total = len(df)
        med_rate = (df["medication_taken"].eq("예").sum() / total) * 100
        avg_pain = df["pain_score"].mean()
        avg_fatigue = df["fatigue_score"].mean()
        avg_sleep = df["sleep_hours"].mean()

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("기록 일수", f"{total}일")
        col2.metric("복약 이행률", f"{med_rate:.1f}%")
        col3.metric("평균 통증", f"{avg_pain:.1f}/10")
        col4.metric("평균 수면", f"{avg_sleep:.1f}시간")

        chart_df = df.set_index("log_date")[["pain_score", "fatigue_score", "sleep_hours"]]
        st.subheader("증상 변화 그래프")
        st.line_chart(chart_df)

        st.subheader("최근 기록")
        st.dataframe(df[["log_date", "pain_score", "fatigue_score", "medication_taken", "sleep_hours", "memo"]].tail(10), use_container_width=True)

elif menu == "재진 준비 요약":
    st.title("🏥 다음 진료 준비 요약")
    df = load_logs()

    last_summary = st.session_state.get("last_summary", "최근 차트 해설 기록이 없습니다. '차트 해설' 메뉴에서 먼저 설명을 생성하세요.")
    last_guides = st.session_state.get("last_guides", [])

    st.subheader("최근 차트 쉬운 설명")
    st.write(last_summary)

    if df.empty:
        st.info("증상 기록이 없어 요약 리포트를 만들 수 없습니다.")
    else:
        recent = df.tail(7)
        med_rate = (recent["medication_taken"].eq("예").sum() / len(recent)) * 100
        avg_pain = recent["pain_score"].mean()
        avg_fatigue = recent["fatigue_score"].mean()
        avg_sleep = recent["sleep_hours"].mean()

        st.subheader("최근 7회 기록 요약")
        st.markdown(f"""
        - 복약 이행률: **{med_rate:.1f}%**
        - 평균 통증 점수: **{avg_pain:.1f}/10**
        - 평균 피로 점수: **{avg_fatigue:.1f}/10**
        - 평균 수면 시간: **{avg_sleep:.1f}시간**
        """)

        memos = recent["memo"].dropna().astype(str)
        memos = [m for m in memos if m.strip()]
        if memos:
            st.subheader("환자가 남긴 최근 메모")
            for memo in memos[-5:]:
                st.write(f"- {memo}")

        st.subheader("의료진에게 물어볼 질문 예시")
        st.write("1. 최근 증상 변화가 치료 과정에서 의미 있는 변화인지 궁금합니다.")
        st.write("2. 복약 중 불편감이 있을 때 어떻게 조절해야 하는지 알고 싶습니다.")
        st.write("3. 식단, 운동, 수면 관리에서 가장 우선해야 할 부분이 무엇인지 궁금합니다.")

st.markdown("---")
st.caption("⚠️ 본 MVP는 해커톤 시연용입니다. 의료 진단, 처방, 응급상황 판단을 제공하지 않습니다. 증상이 심하거나 이상 증상이 있으면 반드시 의료진에게 문의하세요.")
