import streamlit as st
import pandas as pd
import datetime
import os
import time
import plotly.express as px

# --- Configuration ---
DATA_FILE = "study_log.csv"
SUBJECTS = [
    "憲法 (Constitution)", 
    "民法 (Civil Law)", 
    "行政法 (Admin Law)", 
    "商法・会社法 (Commercial Law)", 
    "一般知識 (General Knowledge)"
]
GOAL_HOURS = 800

# --- Helper Functions ---
def load_data():
    if not os.path.exists(DATA_FILE):
        return pd.DataFrame(columns=["Timestamp", "Subject", "Duration_Minutes", "Method"])
    try:
        return pd.read_csv(DATA_FILE)
    except Exception as e:
        st.error(f"データファイルの読み込みエラー: {e}")
        return pd.DataFrame(columns=["Timestamp", "Subject", "Duration_Minutes", "Method"])

def save_log(subject, duration_minutes, method="Timer"):
    df = load_data()
    new_entry = pd.DataFrame([{
        "Timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Subject": subject,
        "Duration_Minutes": duration_minutes,
        "Method": method
    }])
    df = pd.concat([df, new_entry], ignore_index=True)
    df.to_csv(DATA_FILE, index=False)
    return df

def get_today_total():
    df = load_data()
    if df.empty:
        return 0, df
    
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    today = datetime.datetime.now().date()
    # Filter for today
    today_df = df[df['Timestamp'].dt.date == today]
    total_minutes = today_df['Duration_Minutes'].sum()
    return total_minutes, df

# --- Page Setup ---
st.set_page_config(page_title="学習タイマー", layout="centered", page_icon="⏱️")

# --- Custom CSS for Mobile Optimization ---
st.markdown("""
<style>
    /* Make buttons larger for touch targets */
    .stButton > button {
        height: 3em; 
        font-size: 1.2rem;
        font-weight: bold;
    }
    /* Increase visibility of metrics */
    [data-testid="stMetricValue"] {
        font-size: 2.5rem;
    }
</style>
""", unsafe_allow_html=True)

# --- Header / Metrics ---
total_min_today, all_data = get_today_total()
total_hours_today = total_min_today / 60

st.title("⏱️ 行政書士試験 学習タイマー")
st.metric(label="今日の学習時間", value=f"{int(total_hours_today)}時間 {int(total_min_today % 60)}分")

st.divider()

# --- Main Actions (Timer & Subject) ---

# Subject Selection
selected_subject = st.radio("科目を選択", SUBJECTS)

# Timer Logic
if 'start_time' not in st.session_state:
    st.session_state.start_time = None

col1, col2 = st.columns(2)

with col1:
    if st.button("▶ 開始", use_container_width=True):
        st.session_state.start_time = time.time()
        st.rerun()

with col2:
    if st.button("⏹ 終了", use_container_width=True):
        if st.session_state.start_time:
            end_time = time.time()
            elapsed_seconds = end_time - st.session_state.start_time
            elapsed_minutes = int(elapsed_seconds / 60)
            
            # Minimum 1 minute to log (prevent accidental clicks)
            if elapsed_minutes < 1:
                st.warning("1分未満のため記録されませんでした。")
            else:
                save_log(selected_subject, elapsed_minutes, method="Timer")
                st.success(f"{selected_subject} を {elapsed_minutes}分 記録しました！")
            
            st.session_state.start_time = None
            time.sleep(1) # Show success message briefly
            st.rerun()
        else:
            st.info("タイマーが開始されていません。")

if st.session_state.start_time:
    elapsed = int(time.time() - st.session_state.start_time)
    min_display = elapsed // 60
    sec_display = elapsed % 60
    st.info(f"⏳ 計測中... {min_display}分 {sec_display}秒")

# --- Manual Entry ---
with st.expander("➕ 手動入力 (タイマー忘れ)"):
    with st.form("manual_entry_form"):
        m_subject = st.selectbox("科目", SUBJECTS, key="manual_subject")
        m_minutes = st.number_input("時間 (分)", min_value=1, max_value=1440, step=15, value=30)
        submitted = st.form_submit_button("記録を追加")
        if submitted:
            save_log(m_subject, m_minutes, method="Manual")
            st.success("手動で追加しました！")
            st.rerun()

st.divider()

# --- Visualizations ---

if not all_data.empty:
    # 1. Progress Bar
    total_lifetime_minutes = all_data['Duration_Minutes'].sum()
    total_lifetime_hours = total_lifetime_minutes / 60
    
    st.subheader("🚀 学習の進捗")
    progress = min(total_lifetime_hours / GOAL_HOURS, 1.0)
    st.progress(progress)
    st.write(f"**{total_lifetime_hours:.1f}時間** / {GOAL_HOURS}時間 目標 ({progress*100:.1f}%)")

    # 2. Subject Breakdown (Pie Chart)
    st.subheader("📚 科目別内訳")
    subject_group = all_data.groupby("Subject")["Duration_Minutes"].sum().reset_index()
    
    fig = px.pie(
        subject_group, 
        values='Duration_Minutes', 
        names='Subject', 
        hole=0.4,
    )
    # Optimize layout for mobile
    fig.update_layout(
        showlegend=False, 
        margin=dict(t=20, b=20, l=20, r=20),
        height=300
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("学習を開始して進捗を確認しましょう！")

