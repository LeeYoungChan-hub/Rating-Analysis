import streamlit as st
import pandas as pd
import os
import json
import plotly.express as px

# --- 1. 설정 및 파일 경로 ---
RECORD_FILE = 'ygo_master_data.csv'
META_FILE = 'metadata_config.json'

st.set_page_config(page_title="YGO Rating Analysis", layout="wide")

# --- 2. [디자인] CSS: 엑셀 스타일 및 레이아웃 ---
st.markdown("""
    <style>
    /* 전체 텍스트 중앙 정렬 */
    [data-testid="stDataFrameResizable"] div[role="grid"] div[role="row"] div { 
        text-align: center !important; 
        font-size: 13px !important; 
    }
    
    /* Record 페이지 전용: 헤더 숨기기 및 색상 지정 */
    thead { display: none !important; }

    /* 1행(노란색): 제목줄 */
    [data-testid="stDataFrameResizable"] div[role="grid"] div[role="row"]:nth-child(1) {
        background-color: #f9cb9c !important; 
        font-weight: bold !important;
        color: #000 !important;
    }

    /* 2행(초록색): 요약줄 */
    [data-testid="stDataFrameResizable"] div[role="grid"] div[role="row"]:nth-child(2) {
        background-color: #d9ead3 !important; 
        font-weight: bold !important;
    }

    /* 승률/선공률 빨간색 강조 */
    [data-testid="stDataFrameResizable"] div[role="grid"] div[role="row"]:nth-child(2) div:nth-child(3),
    [data-testid="stDataFrameResizable"] div[role="grid"] div[role="row"]:nth-child(2) div:nth-child(4) {
        color: #ff0000 !important;
    }
    
    /* 입력창 빨간줄 제거 */
    textarea, input { spellcheck: false !important; }
    </style>
""", unsafe_allow_html=True)

# --- 3. 데이터 관리 함수 ---
def load_metadata():
    if os.path.exists(META_FILE):
        with open(META_FILE, 'r', encoding='utf-8') as f: return json.load(f)
    return {
        "my_decks": ["KT", "Ennea"], 
        "opp_decks": ["Mitsu", "Tenpai", "Branded"], 
        "archetypes": ["운영", "전개"], 
        "win_loss_reasons": ["자신 실력", "특정 카드", "선후공", "상대 패"], 
        "target_cards": ["Nibiru", "Ash", "Fuwalos"]
    }

def save_metadata(meta):
    with open(META_FILE, 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=4)

def load_records():
    cols = ["NO.", "날짜", "선후공", "결과", "세트", "내 덱", "상대 덱", "아키타입", "승패 요인", "특정 카드", "브릭", "실수", "비고"]
    if os.path.exists(RECORD_FILE):
        df = pd.read_csv(RECORD_FILE, dtype=str).fillna("")
        df = df[~df['NO.'].isin(["NO.", "경기"])] # 요약행 제외하고 로드
        return df.reset_index(drop=True)
    return pd.DataFrame(columns=cols)

def save_records(df):
    # 상단 2줄 제외하고 저장
    if len(df) > 2:
        real_data = df.iloc[2:].copy()
        real_data.to_csv(RECORD_FILE, index=False, encoding='utf-8-sig')
        st.session_state.df = real_data.reset_index(drop=True)

# --- 4. 초기화 ---
if 'metadata' not in st.session_state: st.session_state.metadata = load_metadata()
if 'df' not in st.session_state: st.session_state.df = load_records()

# --- 5. 사이드바 메뉴 ---
page = st.sidebar.radio("Menu", ["📊 Record", "📈 Analysis", "🖼️ Graph", "⚙️ Setting"])

# --- [PAGE: Record] ---
if page == "📊 Record":
    st.title("📊 Match Record")
    
    data_df = st.session_state.df
    total_valid = len(data_df[data_df['결과'].isin(['승', '패'])])
    f_rate = f"{(len(data_df[data_df['선후공'] == '선']) / total_valid * 100):.2f}%" if total_valid > 0 else "0.00%"
    w_rate = f"{(len(data_df[data_df['결과'] == '승']) / total_valid * 100):.2f}%" if total_valid > 0 else "0.00%"
    b_sum = str(data_df['브릭'].astype(str).str.contains('▣').sum())
    m_sum = str(data_df['실수'].astype(str).str.contains('▣').sum())

    # 시각적 2줄 구성
    row1 = ["NO.", "날짜", "선후공", "결과", "세트 전적", "내 덱", "상대 덱", "아키타입", "승패 요인", "특정 카드", "브릭", "실수", "비고"]
    row2 = ["경기", "Date", f_rate, w_rate, "Result", "Use.deck", "Opp. deck", "Plus Arch.", "W/L Factor", "Certain Card", b_sum, m_sum, "Summary"]
    display_df = pd.concat([pd.DataFrame([row1, row2], columns=data_df.columns), data_df]).reset_index(drop=True)

    edited = st.data_editor(
        display_df, use_container_width=True, num_rows="dynamic", hide_index=True, key="main_editor", height=600,
        column_config={
            "선후공": st.column_config.SelectboxColumn(options=["", "선", "후"]),
            "결과": st.column_config.SelectboxColumn(options=["", "승", "패"]),
            "세트": st.column_config.SelectboxColumn(options=["", "OO", "OXO", "XOO", "XX", "XOX", "OXX"]),
            "내 덱": st.column_config.SelectboxColumn(options=[""] + st.session_state.metadata["my_decks"]),
            "상대 덱": st.column_config.SelectboxColumn(options=[""] + st.session_state.metadata["opp_decks"]),
            "브릭": st.column_config.TextColumn(help="▣ 입력 시 카운트"),
            "실수": st.column_config.TextColumn(help="▣ 입력 시 카운트"),
        }
    )

    if st.button("💾 SAVE DATA"):
        save_records(edited)
        st.rerun()

# --- [PAGE: Analysis] ---
elif page == "📈 Analysis":
    st.title("📈 Rating Analysis")
    df = st.session_state.df
    if not df.empty:
        calc_df = df[df['결과'].isin(['승', '패'])]
        total = len(calc_df)
        wins = len(calc_df[calc_df['결과'] == '승'])
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Games", f"{total} G")
        c2.metric("Win Rate", f"{(wins/total*100):.1f}%" if total > 0 else "0%")
        c3.metric("Bricks/Mistakes", f"{b_sum} / {m_sum}")
        
        st.subheader("Matchup Detail")
        st.dataframe(calc_df[['날짜', '내 덱', '상대 덱', '결과', '승패 요인']], use_container_width=True, hide_index=True)
    else:
        st.info("데이터가 없습니다. Record 페이지에서 먼저 기록해주세요.")

# --- [PAGE: Graph] ---
elif page == "🖼️ Graph":
    st.title("🖼️ Deck Distribution")
    df = st.session_state.df
    if not df.empty:
        # 상대 덱 분포 그래프
        counts = df['상대 덱'].value_counts().reset_index()
        counts.columns = ['Deck', 'Count']
        fig = px.pie(counts, values='Count', names='Deck', title="Opponent Deck Usage", hole=0.3)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("그래프를 표시할 데이터가 부족합니다.")

# --- [PAGE: Setting] ---
elif page == "⚙️ Setting":
    st.title("⚙️ Metadata Setting")
    st.write("각 항목을 줄바꿈(Enter)으로 구분하여 입력하세요.")
    
    m = st.session_state.metadata
    col1, col2 = st.columns(2)
    
    with col1:
        new_my = st.text_area("내 덱 리스트", "\n".join(m["my_decks"]), height=150)
        new_opp = st.text_area("상대 덱 리스트", "\n".join(m["opp_decks"]), height=150)
    with col2:
        new_reas = st.text_area("승패 요인", "\n".join(m["win_loss_reasons"]), height=150)
        new_cards = st.text_area("특정 카드(타겟)", "\n".join(m["target_cards"]), height=150)

    if st.button("✅ 설정 저장"):
        st.session_state.metadata = {
            "my_decks": [x.strip() for x in new_my.split("\n") if x.strip()],
            "opp_decks": [x.strip() for x in new_opp.split("\n") if x.strip()],
            "win_loss_reasons": [x.strip() for x in new_reas.split("\n") if x.strip()],
            "target_cards": [x.strip() for x in new_cards.split("\n") if x.strip()],
            "archetypes": m["archetypes"]
        }
        save_metadata(st.session_state.metadata)
        st.success("설정이 저장되었습니다!")
        st.rerun()
