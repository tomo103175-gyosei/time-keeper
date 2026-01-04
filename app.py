import streamlit as st
import pandas as pd
import plotly.express as px
import time
from datetime import datetime, timedelta, timezone
from streamlit_gsheets import GSheetsConnection

# --- ページ設定 ---
st.set_page_config(page_title="行政書士学習トラッカー", layout="centered")
st.title("⏱️ 行政書士 合格タイマー")

# --- 日本時間（JST）の定義 ---
JST = timezone(timedelta(hours=9), 'JST')

# --- セッション状態の管理 ---
if "start_time" not in st.session_state:
    st.session_state.start_time = None
if "is_studying" not in st.session_state:
    st.session_state.is_studying = False

# --- Googleスプレッドシート接続 ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error(f"接続エラー: {e}")
    st.stop()

def load_data():
    try:
        try:
            df = conn.read(worksheet="シート1", ttl=0)
            return df, "シート1"
        except:
            df = conn.read(worksheet="Sheet1", ttl=0)
            return df, "Sheet1"
    except:
        return pd.DataFrame(columns=["date", "subject", "minutes", "notes"]), "シート1"

def save_data(date, subject, minutes, notes):
    df, sheet_name = load_data()
    
    new_data = pd.DataFrame([{
        "date": date,
        "subject": subject,
        "minutes": minutes,
        "notes": notes
    }])
    
    if df.empty:
        updated_df = new_data
    else:
        updated_df = pd.concat([df, new_data], ignore_index=True)
        
    try:
        conn.update(worksheet=sheet_name, data=updated_df)
        return True
    except Exception as e:
        st.error(f"保存エラー: {e}")
        return False

# 削除用の関数
def delete_row(index_to_delete):
    df, sheet_name = load_data()
    try:
        # 指定された行（index）を削除
        df = df.drop(index_to_delete)
        conn.update(worksheet=sheet_name, data=df)
        return True
    except Exception as e:
        st.error(f"削除エラー: {e}")
        return False

# --- メイン画面 ---

# 1. 今日の学習時間を表示
df, _ = load_data()
today_str = datetime.now(JST).strftime("%Y-%m-%d")

if not df.empty and "date" in df.columns and "minutes" in df.columns:
    df["date"] = df["date"].astype(str)
    today_df = df[df["date"] == today_str]
    total_today = today_df["minutes"].sum() if not today_df.empty else 0
else:
    total_today = 0

hours = int(total_today // 60)
mins = int(total_today % 60)
st.metric(label=f"📅 今日の学習合計 ({today_str})", value=f"{hours}時間 {mins}分")

st.markdown("---")

# 2. タイマー機能
st.subheader("✍️ 学習を記録する")

subject = st.radio("科目", ["憲法", "民法", "行政法", "商法・会社法", "基礎知識"], horizontal=True)
notes = st.text_input("一言メモ", placeholder="例: 過去問 P.20〜30、条文読み込みなど")

if not st.session_state.is_studying:
    # --- 停止中 ---
    st.info("準備ができたら「開始」を押してください。")
    if st.button("▶ 学習スタート", type="primary", use_container_width=True):
        st.session_state.is_studying = True
        st.session_state.start_time = time.time()
        st.rerun()
else:
    # --- 計測中 ---
    start_dt = datetime.fromtimestamp(st.session_state.start_time, JST)
    start_str = start_dt.strftime("%H:%M")
    
    st.success(f"🏃‍♂️ 学習中... （開始時刻: {start_str}）")
    st.caption("※画面の時間は動きませんが、裏で動いています。学習が終わったら「終了」を押してください。")
    
    if st.button("⏹ 終了して記録する", type="primary", use_container_width=True):
        end_time = time.time()
        duration_sec = end_time - st.session_state.start_time
        duration_min = int(duration_sec // 60)
        if duration_min < 1:
            duration_min = 1
            
        if save_data(today_str, subject, duration_min, notes):
            st.toast(f"お疲れ様でした！ {duration_min}分 記録しました🎉")
            time.sleep(1)
            st.session_state.is_studying = False
            st.session_state.start_time = None
            st.rerun()

# 3. 手動入力
with st.expander("➕ タイマーを使わず手動で追加"):
    with st.form("manual_add"):
        m_subject = st.selectbox("科目", ["憲法", "民法", "行政法", "商法・会社法", "基礎知識"], key="m_sub")
        m_minutes = st.number_input("時間(分)", min_value=1, value=30, step=5)
        m_notes = st.text_input("メモ", key="m_note")
        if st.form_submit_button("追加する"):
            save_data(today_str, m_subject, m_minutes, m_notes)
            st.success("追加しました！")
            st.rerun()

# 4. 履歴と削除（新機能）
st.markdown("---")
with st.expander("🗑️ 履歴の確認・削除（間違えた時はここ！）"):
    if not df.empty:
        st.caption("直近の5件を表示しています。削除ボタンを押すとすぐに消えます。")
        # 最新のものが上に来るように並び替えて表示
        recent_df = df.tail(5).iloc[::-1]
        
        for index, row in recent_df.iterrows():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.text(f"【{row['date']}】{row['subject']} ({row['minutes']}分)\nメモ: {row['notes']}")
            with col2:
                # 削除ボタン（ユニークなキーを設定）
                if st.button("削除", key=f"del_{index}"):
                    delete_row(index)
                    st.toast("削除しました🗑️")
                    time.sleep(1)
                    st.rerun()
    else:
        st.info("まだ記録がありません。")

# 5. グラフ
if not df.empty and "minutes" in df.columns:
    st.subheader("📊 進捗データ")
    tab1, tab2 = st.tabs(["科目割合", "目標達成"])
    
    with tab1:
        fig = px.pie(df, values='minutes', names='subject', title='科目別比率')
        st.plotly_chart(fig, use_container_width=True)
    with tab2:
        total_all = df["minutes"].sum()
        goal = 800 * 60
        prog = min(total_all / goal, 1.0)
        st.progress(prog)
        st.caption(f"全体累計: {int(total_all//60)}時間 / 目標800時間")

st.markdown("<br><br>", unsafe_allow_html=True)
if st.button("🔄 調子が悪い時はここを押してリセット"):
    st.session_state.clear()
    st.rerun()
