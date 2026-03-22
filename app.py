import streamlit as st
import pandas as pd
import os
import json
import plotly.express as px

# --- 1. 설정: 파일명 변경으로 깨끗하게 시작 ---
RECORD_FILE = 'ygo_data_v2.csv'  # 새로운 파일명
META_FILE = 'metadata_config.json'

st.set_page_config(page_title="YGO Rating Analysis", layout="wide")

# --- 2. 디자인: CSS (깔끔한 표 정렬) ---
st.markdown("""
    <style>
    /* 표 안의 텍스트 중앙 정렬 */
    [data-testid="stDataFrameResizable"] div[role="grid"] div[role="row"] div { 
        text-align: center !important; 
        font-size: 13px !important; 
    }
    /* 표 헤더 색상 */
    thead tr th {
        background-color: #f0f2f6 !important;
        font-weight: bold !important;
    }
    /* 입력창 맞춤법 검사(빨간줄) 제거 */
    textarea, input { spellcheck: false !important; }
    
    /* 분석 페이지 테이블 스타일 */
    .styled-table { width: 100%; font-size: 12px; border-collapse: collapse; margin-bottom: 20px; border: 1px solid #dee2e6; }
    .styled-table th, .styled-table td { text-align: center !important; border: 1px solid #dee2e6 !important; padding: 6px !important; }
    .styled-table th { background-color: #f9cb9c !important; color: #31333F !important; }
    .win-val { color: #0000ff !important; font-weight: bold; }
    .loss-val { color: #ff0000 !important; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- 3. 핵심 함수: 데이터 관리 ---
def load_metadata():
    if os.path.exists(META_FILE):
        with open(META_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "my_decks": ["KT", "Ennea"], 
        "opp_decks": ["Mitsu", "Branded", "Tenpai", "Snake-Eye"],
        "archetypes": ["운영", "전개", "함떡"], 
        "win_loss_reasons": ["실력", "패사고", "매칭운", "상성"], 
        "target_cards": ["Nibiru", "Ash", "Maxx-C"]
    }

def save_metadata(meta):
    with open(META_FILE, 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=4)

def load_records():
    cols = ["NO.", "날짜", "선후공", "결과", "세트", "점수", "내 덱", "상대 덱", "아키타입", "승패 요인", "특정 카드", "브릭", "실수", "비고"]
    if os.path.exists(RECORD_FILE):
        df = pd.read_csv(RECORD_FILE, dtype=str).fillna("")
        # 체크박스 데이터 복원
        for col in ["브릭", "실수"]:
            if col in df.columns:
                df[col] = df[col].apply(lambda x: str(x).lower() in ['true', '1'])
        return df
    return pd.DataFrame(columns=cols)

def save_records(df):
    df.to_csv(RECORD_FILE, index=False, encoding='utf-8-sig')
    st.session_state.df = df.reset_index(drop=True)

def render_summary_table(title, target_df):
    calc = target_df[target_df['결과'].isin(['승', '패'])]
    total = len(calc)
    if total == 0: return f"<div>{title}: 데이터 없음</div>"
    
    w, l = len(calc[calc['결과']=='승']), len(calc[calc['결과']=='패'])
    f_df, s_df = calc[calc['선후공']=='선'], calc[calc['선후공']=='후']
    f_t, s_t = len(f_df), len(s_df)
    f_w, s_w = len(f_df[f_df['결과']=='승']), len(s_df[s_df['결과']=='승'])

    return f"""
        <table class="styled-table">
            <tr><th colspan="5">{title}</th></tr>
            <tr><th>Overall</th><th>Games</th><th>Win Rate</th><th>W</th><th>L</th></tr>
            <tr><td>Result</td><td>{total}</td><td>{(w/total*100):.2f}%</td><td class="win-val">{w}</td><td class="loss-val">{l}</td></tr>
            <tr><th>Coin</th><th>1st</th><th>2nd</th><th>1st Rate</th><th>2nd Rate</th></tr>
            <tr><td>Result</td><td>{f_t}</td><td>{s_t}</td><td>{(f_t/total*100):.1f}%</td><td>{(s_t/total*100):.1f}%</td></tr>
        </table>
    """

# --- 4. 세션 상태 초기화 ---
if 'metadata' not in st.session_state: st.session_state.metadata = load_metadata()
if 'df' not in st.session_state: st.session_state.df = load_records()

# --- 5. 사이드바 메뉴 ---
page = st.sidebar.radio("Menu", ["📊 Record", "📈 Analysis", "🖼️ Graph", "⚙️ Setting"])

# --- PAGE: Record ---
if page == "📊 Record":
    st.title("📊 Match Record")
    
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("➕ Add New Match"):
            new_no = str(len(st.session_state.df) + 1)
            new_row = pd.DataFrame([{
                "NO.": new_no, "날짜": "", "선후공": "", "결과": "", "세트": "", "점수": "", 
                "내 덱": "", "상대 덱": "", "아키타입": "", "승패 요인": "", "특정 카드": "", 
                "브릭": False, "실수": False, "비고": ""
            }])
            st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True)
            save_records(st.session_state.df)
            st.rerun()

    # 데이터 에디터 (가장 순수한 형태)
    edited = st.data_editor(
        st.session_state.df, 
        use_container_width=True, 
        num_rows="dynamic", 
        hide_index=True, 
        key="main_editor",
        height=700,
        column_config={
            "NO.": st.column_config.TextColumn("NO.", width=50),
            "날짜": st.column_config.TextColumn("날짜", width=90),
            "선후공": st.column_config.SelectboxColumn("선후공", options=["", "선", "후"], width=70),
            "결과": st.column_config.SelectboxColumn("결과", options=["", "승", "패"], width=70),
            "세트": st.column_config.SelectboxColumn("세트", options=["", "OO", "OXO", "XOO", "XX", "XOX", "OXX"], width=90),
            "내 덱": st.column_config.SelectboxColumn("내 덱", options=[""] + st.session_state.metadata["my_decks"], width=120),
            "상대 덱": st.column_config.SelectboxColumn("상대 덱", options=[""] + st.session_state.metadata["opp_decks"], width=130),
            "아키타입": st.column_config.SelectboxColumn("아키타입", options=[""] + st.session_state.metadata["archetypes"], width=110),
            "승패 요인": st.column_config.SelectboxColumn("승패 요인", options=[""] + st.session_state.metadata["win_loss_reasons"], width=110),
            "브릭": st.column_config.CheckboxColumn("브릭", width=60), 
            "실수": st.column_config.CheckboxColumn("실수", width=60),
            "비고": st.column_config.TextColumn("비고", width=350)
        }
    )

    if not edited.equals(st.session_state.df):
        save_records(edited)
        st.rerun()

# --- PAGE: Analysis ---
elif page == "📈 Analysis":
    st.title("📈 Rating Analysis")
    df_ana = load_records()
    if not df_ana.empty:
        calc_df = df_ana[df_ana['결과'].isin(['승', '패'])].copy()
        st.markdown(render_summary_table("Overall Statistics", calc_df), unsafe_allow_html=True)
        
        st.subheader("Matchup Detail")
        sel_my = st.selectbox("Select My Deck", st.session_state.metadata["my_decks"])
        my_df = calc_df[calc_df['내 덱'] == sel_my]
        st.markdown(render_summary_table(f"Results for {sel_my}", my_df), unsafe_allow_html=True)
    else:
        st.info("No data available. Please add records first.")

# --- PAGE: Graph ---
elif page == "🖼️ Graph":
    st.title("🖼️ Deck Distribution")
    df_graph = load_records()
    if not df_graph.empty:
        calc_df = df_graph[df_graph['상대 덱'] != ""]
        if not calc_df.empty:
            counts = calc_df['상대 덱'].value_counts().reset_index()
            counts.columns = ['Deck', 'Count']
            fig = px.pie(counts, values='Count', names='Deck', hole=0.4, title="Opponent Deck Share")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data to display.")

# --- PAGE: Setting ---
elif page == "⚙️ Setting":
    st.title("⚙️ Metadata Setting")
    st.info("Enter items separated by new lines. Changes save automatically on focus out.")
    
    def update_meta():
        st.session_state.metadata = {
            "my_decks": [x.strip() for x in st.session_state.s_my.split("\n") if x.strip()],
            "opp_decks": [x.strip() for x in st.session_state.s_opp.split("\n") if x.strip()],
            "win_loss_reasons": [x.strip() for x in st.session_state.s_reas.split("\n") if x.strip()],
            "archetypes": [x.strip() for x in st.session_state.s_arch.split("\n") if x.strip()],
            "target_cards": [x.strip() for x in st.session_state.s_card.split("\n") if x.strip()]
        }
        save_metadata(st.session_state.metadata)

    m = st.session_state.metadata
    c1, c2 = st.columns(2)
    with c1: st.text_area("My Decks", "\n".join(m["my_decks"]), key="s_my", on_change=update_meta, height=150)
    with c2: st.text_area("Opponent Decks", "\n".join(m["opp_decks"]), key="s_opp", on_change=update_meta, height=150)
    
    c3, c4 = st.columns(2)
    with c3: st.text_area("W/L Reasons", "\n".join(m["win_loss_reasons"]), key="s_reas", on_change=update_meta, height=150)
    with c4: st.text_area("Archetypes", "\n".join(m["archetypes"]), key="s_arch", on_change=update_meta, height=150)
