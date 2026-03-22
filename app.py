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

# --- [PAGE: Analysis] ---
elif page == "📈 Analysis":
    st.title("📈 Rating Analysis")
    df_ana = load_records()
    if not df_ana.empty:
        calc_df = df_ana[df_ana['결과'].isin(['승', '패'])].copy()
        
        # 분석용 수치 컬럼 생성
        calc_df['is_win'] = calc_df['결과'].apply(lambda x: 1 if x == '승' else 0)
        calc_df['is_loss'] = calc_df['결과'].apply(lambda x: 1 if x == '패' else 0)
        calc_df['is_1st'] = calc_df['선후공'].apply(lambda x: 1 if x == '선' else 0)
        calc_df['is_2nd'] = calc_df['선후공'].apply(lambda x: 1 if x == '후' else 0)
        calc_df['win_1st'] = ((calc_df['is_1st'] == 1) & (calc_df['is_win'] == 1)).astype(int)
        calc_df['win_2nd'] = ((calc_df['is_2nd'] == 1) & (calc_df['is_win'] == 1)).astype(int)
        calc_df['has_arch'] = calc_df['아키타입'].apply(lambda x: 1 if str(x).strip() != "" else 0)

        col_left, col_right = st.columns([1, 2.2])
        
        with col_left:
            st.markdown(render_summary_table("Overall Data", calc_df), unsafe_allow_html=True)
            st.write("---")
            st.subheader("내 덱별 승률")
            sel_my = st.selectbox("내 덱 선택", st.session_state.metadata["my_decks"], key="sel_my_ana")
            my_deck_df = calc_df[calc_df['내 덱'] == sel_my]
            st.markdown(render_summary_table(f"Result: {sel_my}", my_deck_df), unsafe_allow_html=True)
            st.write("---")
            st.subheader("상대 덱별 상세")
            c1, c2 = st.columns(2)
            with c1: m_my = st.selectbox("Use.Deck", st.session_state.metadata["my_decks"], key="m_my_box")
            with c2: m_opp = st.selectbox("Opp.Deck", st.session_state.metadata["opp_decks"], key="m_opp_box")
            st.markdown(render_summary_table(f"{m_my} vs {m_opp}", calc_df[(calc_df['내 덱']==m_my)&(calc_df['상대 덱']==m_opp)]), unsafe_allow_html=True)

        with col_right:
            st.subheader("📊 Opponent Deck Statistics")
            target_df = calc_df[calc_df['내 덱'] == sel_my].copy()
            if not target_df.empty:
                agg = target_df.groupby('상대 덱').agg({
                    '결과': 'count', 'is_win': 'sum', 'is_loss': 'sum',
                    'is_1st': 'sum', 'win_1st': 'sum', 'is_2nd': 'sum', 'win_2nd': 'sum', 'has_arch': 'sum'
                }).rename(columns={'결과': 'Total', 'is_win': 'W', 'is_loss': 'L'})
                
                total_m = agg['Total'].sum()
                agg['W%'] = agg['W'] / agg['Total'] * 100
                agg['1st W%'] = agg['win_1st'] / agg['is_1st'] * 100
                agg['2nd W%'] = agg['win_2nd'] / agg['is_2nd'] * 100
                agg['Share'] = agg['Total'] / total_m * 100
                agg['Plus Arch'] = agg['has_arch'] / agg['Total'] * 100
                agg = agg.sort_values(by='Total', ascending=False)

                headers = ['Matchup', 'Total', 'W', 'L', 'W%', '1st W%', '2nd W%', 'Share', 'Plus Arch']
                html = '<table class="styled-table"><tr>' + ''.join(f'<th>{h}</th>' for h in headers) + '</tr>'
                
                # 합계 행
                t_w, t_l, t_1, t_1w, t_2, t_2w, t_a = agg['W'].sum(), agg['L'].sum(), agg['is_1st'].sum(), agg['win_1st'].sum(), agg['is_2nd'].sum(), agg['win_2nd'].sum(), agg['has_arch'].sum()
                html += f'<tr style="background-color:#fff2cc; font-weight:bold;"><td>Total</td><td>{total_m}</td><td class="win-val">{t_w}</td><td class="loss-val">{t_l}</td><td>{(t_w/total_m*100):.2f}%</td><td>{(t_1w/t_1*100 if t_1>0 else 0):.2f}%</td><td>{(t_2w/t_2*100 if t_2>0 else 0):.2f}%</td><td>100.00%</td><td>{(t_a/total_m*100):.2f}%</td></tr>'
                
                for deck, row in agg.iterrows():
                    html += f'<tr><td>{deck}</td><td>{int(row["Total"])}</td><td class="win-val">{int(row["W"])}</td><td class="loss-val">{int(row["L"])}</td><td>{row["W%"]:.2f}%</td>'
                    html += f'<td>{row["1st W%"]:.2f}%</td>' if pd.notnull(row["1st W%"]) else '<td>-</td>'
                    html += f'<td>{row["2nd W%"]:.2f}%</td>' if pd.notnull(row["2nd W%"]) else '<td>-</td>'
                    html += f'<td>{row["Share"]:.2f}%</td><td>{row["Plus Arch"]:.2f}%</td></tr>'
                st.markdown(html + '</table>', unsafe_allow_html=True)
            else: st.info(f"'{sel_my}' 덱의 매치업 데이터가 없습니다.")
    else: st.info("데이터가 없습니다.")

# --- [PAGE: Graph] ---
elif page == "🖼️ Graph":
    st.title("🖼️ Deck Distribution Graph")
    df_graph = load_records()
    if not df_graph.empty:
        calc_df = df_graph[df_graph['결과'].isin(['승', '패'])]
        if not calc_df.empty:
            opp_counts = calc_df['상대 덱'].value_counts().reset_index()
            opp_counts.columns = ['Deck', 'Count']
            fig = px.pie(opp_counts, values='Count', names='Deck', hole=0.4, title="상대 덱 점유율")
            st.plotly_chart(fig, use_container_width=True)
        else: st.info("분석할 데이터가 부족합니다.")

# --- [PAGE: Setting] ---
else:
    st.title("⚙️ Setting (Auto-Save)")
    st.info("수정 후 바깥을 클릭하면 자동 저장됩니다.")
    m = st.session_state.metadata
    
    def update_meta():
        st.session_state.metadata = {
            "my_decks": [x.strip() for x in st.session_state.s_my.split("\n") if x.strip()],
            "opp_decks": [x.strip() for x in st.session_state.s_opp.split("\n") if x.strip()],
            "win_loss_reasons": [x.strip() for x in st.session_state.s_reas.split("\n") if x.strip()],
            "archetypes": [x.strip() for x in st.session_state.s_arch.split("\n") if x.strip()],
            "target_cards": [x.strip() for x in st.session_state.s_card.split("\n") if x.strip()]
        }
        save_metadata(st.session_state.metadata)

    c1, c2 = st.columns(2)
    with c1: st.text_area("내 덱", "\n".join(m["my_decks"]), key="s_my", on_change=update_meta, height=150)
    with c2: st.text_area("상대 덱", "\n".join(m["opp_decks"]), key="s_opp", on_change=update_meta, height=150)
    c3, c4 = st.columns(2)
    with c3: st.text_area("승패 요인", "\n".join(m["win_loss_reasons"]), key="s_reas", on_change=update_meta, height=150)
    with c4: st.text_area("아키타입", "\n".join(m.get("archetypes", ["운영"])), key="s_arch", on_change=update_meta, height=150)
    st.text_area("특정 카드", "\n".join(m["target_cards"]), key="s_card", on_change=update_meta, height=150)
