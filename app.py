import streamlit as st
import pandas as pd
import os
import json
import plotly.express as px

# --- 1. 파일 경로 설정 ---
RECORD_FILE = 'ygo_master_data.csv'
META_FILE = 'metadata_config.json'

st.set_page_config(page_title="YGO Rating Analysis", layout="wide")

# --- 2. CSS 디자인 (초록색 요약줄을 맨 위로) ---
st.markdown("""
    <style>
    [data-testid="stDataFrameResizable"] div[role="grid"] div[role="row"] div { 
        text-align: center !important; 
        font-size: 13px !important; 
    }
    thead { display: none !important; }
    
    /* 1행: 초록색 요약줄 (기존의 row2가 위로 올라옴) */
    [data-testid="stDataFrameResizable"] div[role="grid"] div[role="row"]:nth-child(1) {
        background-color: #d9ead3 !important; 
        font-weight: bold !important;
        color: #000 !important;
    }
    
    /* 승률/선공률 빨간색 강조 (1행의 3, 4번째 칸) */
    [data-testid="stDataFrameResizable"] div[role="grid"] div[role="row"]:nth-child(1) div:nth-child(3),
    [data-testid="stDataFrameResizable"] div[role="grid"] div[role="row"]:nth-child(1) div:nth-child(4) {
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
        # 요약행 식별자("경기") 제외하고 로드
        df = df[df['NO.'] != "경기"]
        return df.reset_index(drop=True)
    return pd.DataFrame(columns=cols)

# --- 4. 세션 초기화 ---
if 'metadata' not in st.session_state: st.session_state.metadata = load_metadata()
if 'df' not in st.session_state: st.session_state.df = load_records()

# --- 5. 사이드바 메뉴 및 높이 조절 ---
page = st.sidebar.radio("Menu", ["📊 Record", "📈 Analysis", "🖼️ Graph", "⚙️ Setting"])
st.sidebar.markdown("---")
table_height = st.sidebar.slider("표 높이 조절 (px)", 300, 20000, 700, 50)

# --- [PAGE: Record] ---
if page == "📊 Record":
    st.title("📊 Match Record")
    data_df = st.session_state.df
    
    # 통계 계산
    calc_df = data_df[data_df['결과'].isin(['승', '패'])]
    total_v = len(calc_df)
    f_rate = f"{(len(calc_df[calc_df['선후공'] == '선']) / total_v * 100):.2f}%" if total_v > 0 else "0.00%"
    w_rate = f"{(len(calc_df[calc_df['결과'] == '승']) / total_v * 100):.2f}%" if total_v > 0 else "0.00%"
    b_sum = str(data_df['브릭'].astype(str).str.contains('▣').sum())
    m_sum = str(data_df['실수'].astype(str).str.contains('▣').sum())

    # 1행: 초록색 요약줄만 생성
    row_summary = ["경기", "Date", f_rate, w_rate, "Set", "Use.Deck", "Opp.Deck", "Plus Arch.", "W/L Factor", "Certain Card", b_sum, m_sum, "Summary"]
    
    # 요약줄 + 실제 데이터 결합
    display_df = pd.concat([pd.DataFrame([row_summary], columns=data_df.columns), data_df]).reset_index(drop=True)

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

    # 자동 저장 로직 (1행 제외하고 저장)
    if not edited_df.equals(display_df):
        if len(edited_df) >= 1:
            real_data = edited_df.iloc[1:].copy() # 1행(요약줄) 제외
            real_data.to_csv(RECORD_FILE, index=False, encoding='utf-8-sig')
            st.session_state.df = real_data.reset_index(drop=True)
            st.rerun()

elif page == "📈 Analysis":
    st.title("📈 Rating Analysis")
    df_ana = load_records()
    if not df_ana.empty:
        st.markdown('<div class="analysis-wrapper">', unsafe_allow_html=True)
        st.markdown(render_styled_table("Overall Data", df_ana), unsafe_allow_html=True)
        
        st.subheader("덱별 승률")
        sel_my = st.selectbox("내 덱 선택", st.session_state.metadata["my_decks"], label_visibility="collapsed")
        st.markdown(render_styled_table(sel_my, df_ana[df_ana['내 덱'] == sel_my]), unsafe_allow_html=True)
        
        st.subheader("상대 덱별 승률")
        c1, c2 = st.columns(2)
        with c1: m_my = st.selectbox("Use.Deck", st.session_state.metadata["my_decks"], label_visibility="collapsed", key="m_my")
        with c2: m_opp = st.selectbox("Opp.Deck", st.session_state.metadata["opp_decks"], label_visibility="collapsed", key="m_opp")
        st.markdown(render_styled_table("결과", df_ana[(df_ana['내 덱']==m_my) & (df_ana['상대 덱']==m_opp)]), unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

else:
    st.title("⚙️ Setting")
    meta = st.session_state.metadata
    c1, c2 = st.columns(2)
    with c1: new_my = st.text_area("내 덱 (쉼표 구분)", ", ".join(meta.get("my_decks", [])))
    with c2: new_opp = st.text_area("상대 덱 (쉼표 구분)", ", ".join(meta.get("opp_decks", [])))
    c3, c4 = st.columns(2)
    with c3: new_reasons = st.text_area("승패 요인 (쉼표 구분)", ", ".join(meta.get("win_loss_reasons", [])))
    with c4: new_arche = st.text_area("아키타입 (쉼표 구분)", ", ".join(meta.get("archetypes", [])))
    c5, _ = st.columns(2)
    with c5: new_cards = st.text_area("특정 카드 (쉼표 구분)", ", ".join(meta.get("target_cards", [])))
    
    if st.button("✅ 설정 저장"):
        st.session_state.metadata = {
            "my_decks": [x.strip() for x in new_my.split(",") if x.strip()],
            "opp_decks": [x.strip() for x in new_opp.split(",") if x.strip()],
            "win_loss_reasons": [x.strip() for x in new_reasons.split(",") if x.strip()],
            "archetypes": [x.strip() for x in new_arche.split(",") if x.strip()],
            "target_cards": [x.strip() for x in new_cards.split(",") if x.strip()]
        }
        with open(META_FILE, 'w', encoding='utf-8') as f:
            json.dump(st.session_state.metadata, f, ensure_ascii=False, indent=4)
        st.success("설정 저장 완료!")
        st.rerun()

