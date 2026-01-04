import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# ページ設定
st.set_page_config(page_title="行政書士学習トラッカー", layout="centered")

# --- Googleスプレッドシート接続 ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    # キャッシュを使わず常に最新を取得（ttl=0）
    try:
        # 【修正点1】ここを "シート1" に変更（日本語環境のデフォルト名に合わせる）
        df = conn.read(worksheet="シート1", ttl=0)
        # 空の場合や型変換のエラー防止
        if df.empty:
            return pd.DataFrame(columns=["date", "subject", "minutes", "notes"])
        return df
    except Exception:
        return pd.DataFrame(columns=["date", "subject", "minutes", "notes"])

def save_data(date, subject, minutes, notes):
    df = load_data()
    new_data = pd.DataFrame([{
        "date": date,
        "subject": subject,
        "minutes": minutes,
        "notes": notes
    }])
    updated_df = pd.concat([df, new_data], ignore_index=True)
    # スプレッドシートを更新
    # 【修正点2】ここも "シート1" に変更
    conn.update(worksheet="シート1", data=updated_df)

# --- UI ---
st.title("📱 行政書士 合格トラッカー")

# 今日の学習時間を計算して表示
df = load_data()
today_str = datetime.now().strftime("%Y-%m-%d")

# データフレームの確認と集計
if not df.empty and "date" in df.columns and "minutes" in df.columns:
    # date列を文字列型に変換して比較（エラー防止）
    df["date"] = df["date"].astype(str)
    today_df = df[df["date"] == today_str]
    total_minutes = today_df["minutes"].sum() if not today_df.empty else 0
else:
    total_minutes = 0

hours = int(total_minutes // 60)
mins = int(total_minutes % 60)
st.metric(label="今日の学習時間", value=f"{hours}時間 {mins}分")

# --- 入力フォーム ---
st.subheader("学習を記録")
with st.form("log_form", clear_on_submit=True):
    subject = st.radio("科目", ["憲法", "民法", "行政法", "商法・会社法", "基礎知識"], horizontal=True)
    duration = st.number_input("勉強時間（分）", min_value=1, value=30, step=5)
    notes = st.text_input("一言メモ（任意）", placeholder="行政手続法の条文など")
    
    submitted = st.form_submit_button("記録する")
    if submitted:
        save_data(today_str, subject, duration, notes)
        st.success("記録しました！")
        st.rerun() # 画面更新

# --- グラフ ---
if not df.empty and "minutes" in df.columns:
    st.markdown("---")
    st.subheader("📊 進捗データ")
    
    # 科目別円グラフ
    fig = px.pie(df, values='minutes', names='subject', title='科目別比率')
    st.plotly_chart(fig, use_container_width=True)

    # 目標（800時間＝48000分）
    total_all = df["minutes"].sum()
    goal = 800 * 60
    progress = min(total_all / goal, 1.0)
    st.progress(progress)
    st.caption(f"総学習時間: {int(total_all//60)}時間 / 目標800時間（達成率 {progress*100:.1f}%）")
