import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="公司午餐評分系統", page_icon="🍱")

# --- 連接 Google Sheets ---
# 在 Streamlit Cloud 的 Settings -> Secrets 放入網址 (稍後教學)
conn = st.connection("gsheets", type=GSheetsConnection)

# 讀取現有資料
try:
    df = conn.read()
except:
    df = pd.DataFrame(columns=['date', 'meal_name', 'user_name', 'score', 'comment', 'timestamp'])

st.title("🍱 公司午餐評分系統")

# --- 側邊欄導覽 ---
menu = st.sidebar.selectbox("功能選單", ["今日評分", "歷史紀錄", "管理員登入"])
today_str = datetime.now().strftime('%Y-%m-%d')

# --- 1. 今日評分模式 ---
if menu == "今日評分":
    # 找出今天的餐點名稱
    today_meal = df[df['date'] == today_str]['meal_name'].unique()
    meal_name = today_meal[0] if len(today_meal) > 0 else "管理員尚未設定今日餐點"
    
    st.header(f"📅 今日餐點：{meal_name}")
    
    if meal_name != "管理員尚未設定今日餐點":
        with st.form("rating_form"):
            u_name = st.text_input("你的暱稱")
            u_score = st.number_input("評分 (0-5)", 0.0, 5.0, 4.0, 0.1)
            u_comment = st.text_area("寫點評語")
            submit = st.form_submit_button("送出評分")
            
if submit and u_name:
    # 確保資料格式一致
    new_data = pd.DataFrame([{
        "date": str(today_str),
        "meal_name": str(meal_name),
        "user_name": str(u_name),
        "score": float(u_score),
        "comment": str(u_comment),
        "timestamp": datetime.now().strftime("%H:%M:%S")
    }])
    
    # 讀取最新資料後再合併，避免覆蓋
    current_df = conn.read()
    updated_df = pd.concat([current_df, new_data], ignore_index=True)
    
    # 執行更新
    conn.update(data=updated_df)
    st.success("評分成功！")
    st.rerun()

# --- 2. 歷史紀錄模式 ---
elif menu == "歷史紀錄":
    st.header("📜 歷史評分紀錄")
    all_dates = df['date'].unique()
    sel_date = st.selectbox("選擇日期", sorted(all_dates, reverse=True))
    
    day_data = df[df['date'] == sel_date]
    if not day_data.empty:
        meal = day_data['meal_name'].iloc[0]
        avg = day_data[day_data['user_name'].notna()]['score'].mean()
        st.subheader(f"🍴 餐點：{meal}")
        st.metric("平均得分", f"{avg:.1f} ⭐")
        st.dataframe(day_data[day_data['user_name'].notna()][['user_name', 'score', 'comment', 'timestamp']])

# --- 3. 管理員模式 ---
elif menu == "管理員登入":
    pwd = st.text_input("輸入管理密碼", type="password")
    if pwd == "admin123":
        st.header("⚙️ 設定今日餐點")
        new_meal = st.text_input("今天的午餐是什麼？")
        if st.button("發布餐點"):
            new_entry = pd.DataFrame([{"date": today_str, "meal_name": new_meal}])
            updated_df = pd.concat([df, new_entry], ignore_index=True)
            conn.update(data=updated_df)
            st.success("餐點已更新！")

