import streamlit as st
import pandas as pd
import plotly.express as px
import time
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- ページ設定 ---
st.set_page_config(page_title="行政書士学習トラッカー", layout="centered")
st.title("⏱️ 行政書士 合格タイマー")

# --- セッション状態の初期化（タイマー用） ---
if "start_time" not in st.session_state:
    st.session_state.start_time = None
if "is_studying" not in st.session_state:
    st.session_state.is_studying = False

# --- Googleスプレッドシート接続（自動判別機能付き） ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error(f"接続設定エラー: {e}")
    st.stop()

def load_data():
    # シート名が「シート1」か「Sheet1」か自動で探す
    try:
        df = conn.read(worksheet="シート1", ttl=0)
        return df, "シート1"
    except:
        try:
            df = conn.read(worksheet="Sheet1", ttl=0)
            return df, "Sheet1"
        except:
            return pd.DataFrame(columns=["date", "subject", "minutes", "notes"]), "シート1"

def save_data(date, subject, minutes, notes):
    df, sheet_name = load_data()
    
    # 既存データの列名チェック（エラー防止）
    if df.empty:
        df = pd.DataFrame(columns=["date", "subject", "minutes", "notes"])
        
    new_data = pd.DataFrame([{
        "date": date,
        "subject": subject,
        "minutes": minutes,
        "notes": notes
    }])
    
    # データ結合
    # 空のデータフレームとの結合でwarningが出ないよう配慮
    if df.empty:
        updated_df = new_data
    else:
        updated_df = pd.concat([df, new_data], ignore_index=True)
        
    # スプレッドシートを更新
    try:
        conn.update(worksheet=sheet_name, data=updated_df)
        return True, None
    except Exception as e:
        return False, str(e)

# --- UI: 今日の学習時間表示 ---
df, _ = load_data()
today_str = datetime.now().strftime("%Y-%m-%d")

if not df.empty and "date" in df.columns and "minutes" in df.columns:
    # 日付を文字列型にしてフィルタ
    df["date"] = df["date"].astype(str)
    today_df = df[df["date"] == today_str]
    total_today = today_df["minutes"].sum() if not today_df.empty else 0
else:
    total_today = 0

hours = int(total_today // 60)
mins = int(total_today % 60)
st.metric(label="今日の学習時間（累計）", value=f"{hours}時間 {mins}分")

st.markdown("---")

# --- UI: タイマー機能 ---
st.subheader("学習タイマー")

# 科目選択
subject = st.radio("科目", ["憲法", "民法", "行政法", "商法・会社法", "基礎知識"], horizontal=True)
notes = st.text_input("一言メモ", placeholder="例: 過去問 P.50-60")

# タイマーボタン制御
if not st.session_state.is_studying:
    # --- 停止中：スタートボタンを表示 ---
    if st.button("▶ 学習スタート", use_container_width=True, type="primary"):
        st.session_state.is_studying = True
        st.session_state.start_time = time.time()
        st.rerun()
else:
    # --- 計測中：ストップボタンと経過時間を表示 ---
    elapsed_time = time.time() - st.session_state.start_time
    elapsed_mins = int(elapsed_time // 60)
    
    st.info(f"📝 学習中... （経過: 約 {elapsed_mins} 分）")
    st.caption("※画面を閉じてもバックグラウンドで計測されますが、リロードするとリセットされる場合があります。")
    
    if st.button("⏹ ストップ & 記録", use_container_width=True):
        # 最終的な時間を計算
        end_time = time.time()
        final_duration_sec = end_time - st.session_state.start_time
        final_duration_min = int(final_duration_sec // 60)
        
        # 1分未満は切り上げまたは1分として記録
        if final_duration_min < 1:
            final_duration_min = 1
            
        # 保存処理
        success, error_msg = save_data(today_str, subject, final_duration_min, notes)
        
        if success:
            st.success(f"お疲れ様でした！ {final_duration_min}分 を記録しました。")
            # 状態リセット
            st.session_state.is_studying = False
            st.session_state.start_time = None
            time.sleep(2) # メッセージを読めるように少し待つ
            st.rerun()
        else:
            st.error(f"保存に失敗しました: {error_msg}")
            # エラー時は状態を維持して再試行できるようにする

# --- グラフ表示 ---
if not df.empty and "minutes" in df.columns:
    st.markdown("---")
    st.subheader("📊 学習データ")
    
    tab1, tab2 = st.tabs(["科目別割合", "目標達成度"])
    
    with tab1:
        fig_pie = px.pie(df, values='minutes', names='subject', title='科目別学習比率')
        st.plotly_chart(fig_pie, use_container_width=True)
        
    with tab2:
        total_all = df["minutes"].sum()
        goal = 800 * 60
        progress = min(total_all / goal, 1.0)
        st.progress(progress)
        st.caption(f"総学習時間: {int(total_all//60)}時間 / 目標800時間（あと {int((goal - total_all)//60)} 時間）")
