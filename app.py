import streamlit as st
import pandas as pd
import os
import json
import plotly.express as px

# --- 1. 파일 경로 설정 ---
RECORD_FILE = 'ygo_master_data.csv'
META_FILE = 'metadata_config.json'

st.set_page_config(page_title="YGO Rating Analysis", layout="wide")

# --- 2. CSS 디자인 (엑셀 스타일 상단 2줄 재현) ---
st.markdown("""
    <style>
    [data-testid="stDataFrameResizable"] div[role="grid"] div[role="row"] div { 
        text-align: center !important; 
        font-size: 13px !important; 
    }
    thead { display: none !important; }
    /* 1행: 노란색 제목줄 */
    [data-testid="stDataFrameResizable"] div[role="grid"] div[role="row"]:nth-child(1) {
        background-color: #f9cb9c !important; 
        font-weight: bold !important;
        color: #000 !important;
    }
    /* 2행: 초록색 요약줄 */
    [data-testid="stDataFrameResizable"] div[role="grid"] div[role="row"]:nth-child(2) {
        background-color: #d9ead3 !important; 
        font-weight: bold !important;
    }
    /* 승률/선공률 빨간색 강조 */
    [data-testid="stDataFrameResizable"] div[role="grid"] div[role="row"]:nth-child(2) div:nth-child(3),
    [data-testid="stDataFrameResizable"] div[role="grid"] div[role="row"]:nth-child(2) div:nth-child(4) {
        color: #ff0000 !important;
    }
    textarea, input { spellcheck: false !important; }
    </style>
""", unsafe_allow_html=True)

# --- 3. 데이터 관리 함수 ---
def load_metadata():
    if os.path.exists(META_FILE):
        with open(META_FILE, 'r', encoding='utf-8') as f: return json.load(f)
    return {"my_decks": ["KT", "Ennea"], "opp_decks": ["Mitsu", "Tenpai"], "archetypes": ["운영"], "win_loss_reasons": ["실력"], "target_cards": ["Ash"]}

def save_metadata():
    with open(META_FILE, 'w', encoding='utf-8') as f:
        json.dump(st.session_state.metadata, f, ensure_ascii=False, indent=4)

def load_records():
    cols = ["NO.", "날짜", "선후공", "결과", "세트", "내 덱", "상대 덱", "아키타입", "승패 요인", "특정 카드", "브릭", "실수", "비고"]
    if os.path.exists(RECORD_FILE):
        df = pd.read_csv(RECORD_FILE, dtype=str).fillna("")
        df = df[~df['NO.'].isin(["NO.", "경기"])]
        return df.reset_index(drop=True)
    return pd.DataFrame(columns=cols)

# --- 4. 세션 초기화 ---
if 'metadata' not in st.session_state: st.session_state.metadata = load_metadata()
if 'df' not in st.session_state: st.session_state.df = load_records()

# --- 5. 사이드바 메뉴 및 높이 조절 ---
page = st.sidebar.radio("Menu", ["📊 Record", "📈 Analysis", "🖼️ Graph", "⚙️ Setting"])
st.sidebar.markdown("---")
table_height = st.sidebar.slider("표 높이 조절 (px)", 300, 1200, 700, 50)

# --- [PAGE: Record] ---
if page == "📊 Record":
    st.title("📊 Match Record")
    data_df = st.session_state.df
    calc_df = data_df[data_df['결과'].isin(['승', '패'])]
    total_v = len(calc_df)
    f_rate = f"{(len(calc_df[calc_df['선후공'] == '선']) / total_v * 100):.2f}%" if total_v > 0 else "0.00%"
    w_rate = f"{(len(calc_df[calc_df['결과'] == '승']) / total_v * 100):.2f}%" if total_v > 0 else "0.00%"
    b_sum = str(data_df['브릭'].astype(str).str.contains('▣').sum())
    m_sum = str(data_df['실수'].astype(str).str.contains('▣').sum())

    row1 = ["NO.", "날짜", "선후공", "결과", "세트", "내 덱", "상대 덱", "아키타입", "승패 요인", "특정 카드", "브릭", "실수", "비고"]
    row2 = ["경기", "Date", f_rate, w_rate, "Set", "Use.Deck", "Opp.Deck", "Plus Arch.", "W/L Factor", "Certain Card", b_sum, m_sum, "Summary"]
    display_df = pd.concat([pd.DataFrame([row1, row2], columns=data_df.columns), data_df]).reset_index(drop=True)

    edited_df = st.data_editor(
        display_df, use_container_width=True, num_rows="dynamic", hide_index=True, key="main_editor", height=table_height,
        column_config={
            "NO.": st.column_config.TextColumn(width=50),
            "날짜": st.column_config.TextColumn(width=80),
            "선후공": st.column_config.TextColumn("선후공", width=80),
            "결과": st.column_config.TextColumn("결과", width=80),
            "세트": st.column_config.TextColumn("세트", width=90),
            "내 덱": st.column_config.TextColumn("내 덱", width=110),
            "상대 덱": st.column_config.TextColumn("상대 덱", width=120),
        }
    )

    if not edited_df.equals(display_df):
        if len(edited_df) >= 2:
            real_data = edited_df.iloc[2:].copy()
            real_data.to_csv(RECORD_FILE, index=False, encoding='utf-8-sig')
            st.session_state.df = real_data.reset_index(drop=True)
            st.rerun()

# --- [PAGE: Analysis] ---
elif page == "📈 Analysis":
    st.title("📈 Rating Analysis")
    df = st.session_state.df
    if not df.empty:
        calc_df = df[df['결과'].isin(['승', '패'])]
        total = len(calc_df)
        wins = len(calc_df[calc_df['결과'] == '승'])
        c1, c2 = st.columns(2)
        c1.metric("Total Games", f"{total} G")
        c2.metric("Win Rate", f"{(wins/total*100):.1f}%" if total > 0 else "0%")
        st.dataframe(calc_df[['날짜', '내 덱', '상대 덱', '결과']], use_container_width=True, hide_index=True)

# --- [PAGE: Graph] ---
elif page == "🖼️ Graph":
    st.title("🖼️ Deck Distribution")
    df = st.session_state.df
    if not df.empty:
        counts = df['상대 덱'].value_counts().reset_index()
        counts.columns = ['Deck', 'Count']
        fig = px.pie(counts, values='Count', names='Deck', title="Opponent Deck Usage", hole=0.3)
        st.plotly_chart(fig, use_container_width=True)

# --- [PAGE: Setting] ---
elif page == "⚙️ Setting":
    st.title("⚙️ Metadata Setting (Auto-save)")
    m = st.session_state.metadata
    def sync_settings():
        st.session_state.metadata = {
            "my_decks": [x.strip() for x in st.session_state.new_my.split("\n") if x.strip()],
            "opp_decks": [x.strip() for x in st.session_state.new_opp.split("\n") if x.strip()],
            "win_loss_reasons": [x.strip() for x in st.session_state.new_reas.split("\n") if x.strip()],
            "target_cards": [x.strip() for x in st.session_state.new_cards.split("\n") if x.strip()],
            "archetypes": m["archetypes"]
        }
        save_metadata()
    col1, col2 = st.columns(2)
    with col1:
        st.text_area("내 덱 리스트", "\n".join(m["my_decks"]), key="new_my", on_change=sync_settings, height=200)
        st.text_area("상대 덱 리스트", "\n".join(m["opp_decks"]), key="new_opp", on_change=sync_settings, height=200)
    with col2:
        st.text_area("승패 요인", "\n".join(m["win_loss_reasons"]), key="new_reas", on_change=sync_settings, height=200)
        st.text_area("특정 카드(타겟)", "\n".join(m["target_cards"]), key="new_cards", on_change=sync_settings, height=200)
