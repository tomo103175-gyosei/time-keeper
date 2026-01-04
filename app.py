import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="行政書士学習トラッカー", layout="centered")
st.title("🛠 エラー診断モード")

# 接続
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    st.write("✅ 接続設定は読み込めました")
except Exception as e:
    st.error(f"❌ 接続設定エラー: {e}")
    st.stop()

# データ読み込み関数（エラーを隠さず表示する版）
def load_data():
    try:
        # まず「シート1」で試す
        df = conn.read(worksheet="シート1", ttl=0)
        return df
    except Exception as e_jp:
        # ダメなら「Sheet1」で試す
        try:
            df = conn.read(worksheet="Sheet1", ttl=0)
            return df
        except Exception as e_en:
            st.error(f"❌ データの読み込みに失敗しました。")
            st.error(f"原因1（シート1）: {e_jp}")
            st.error(f"原因2（Sheet1）: {e_en}")
            return pd.DataFrame(columns=["date", "subject", "minutes", "notes"])

# 保存関数（エラーを隠さず表示する版）
def save_data(date, subject, minutes, notes):
    df = load_data()
    new_data = pd.DataFrame([{
        "date": date,
        "subject": subject,
        "minutes": minutes,
        "notes": notes
    }])
    
    # 既存データと結合
    if not df.empty:
        updated_df = pd.concat([df, new_data], ignore_index=True)
    else:
        updated_df = new_data
        
    # 書き込みトライ
    try:
        # ここでは読み込みに成功したシート名を使う必要があるが、
        # 診断用なので「シート1」で強制トライしてエラーを見る
        conn.update(worksheet="シート1", data=updated_df)
        st.success("✅ 書き込み成功！")
    except Exception as e:
        st.error(f"❌ 書き込みエラー: {e}")
        # 権限エラーの可能性が高い場合のヒント
        if "403" in str(e):
            st.warning("⚠️ ヒント: 権限エラー(403)です。スプレッドシートの「共有」で、サービスアカウント（...iam.gserviceaccount.com）が「編集者」になっているか確認してください。")

# --- UI ---
st.info("テスト入力して「記録する」を押してください。エラー原因が表示されます。")

with st.form("debug_form"):
    subject = st.selectbox("科目", ["憲法", "民法", "行政法"])
    duration = st.number_input("時間", value=10)
    submitted = st.form_submit_button("記録する")
    
    if submitted:
        save_data(datetime.now().strftime("%Y-%m-%d"), subject, duration, "テスト")

# --- 現在のデータ状態 ---
st.subheader("現在のシートの状態")
df_current = load_data()
st.dataframe(df_current)
