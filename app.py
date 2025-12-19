import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="公司午餐評分系統", page_icon="🍱")

# --- 1. 連接 Google Sheets ---
# 確保你在 Secrets 已經設定好 connections.gsheets 的資訊
conn = st.connection("gsheets", type=GSheetsConnection)

# 讀取現有資料的函式 (增加錯誤處理)
def get_data():
    try:
        # 加入 ttl=0 代表不使用暫存，每次都從 Google 抓新的
        return conn.read(ttl=0) 
    except Exception as e:
        return pd.DataFrame(columns=['date', 'meal_name', 'user_name', 'score', 'comment', 'timestamp'])

df = get_data()

st.title("🍱 公司午餐評分系統")

# --- 2. 側邊欄導覽 ---
menu = st.sidebar.selectbox("功能選單", ["今日評分", "歷史紀錄", "管理員登入"])
today_str = datetime.now().strftime('%Y-%m-%d')

# --- 3. 今日評分模式 ---
if menu == "今日評分":
    # 核心修正 1：確保 df 的日期欄位全部變成純文字字串，並過濾掉空值
    df['date'] = pd.to_datetime(df['date'], errors='coerce').dt.strftime('%Y-%m-%d')
    current_today = datetime.now().strftime('%Y-%m-%d')
    
    # 核心修正 2：不分管理員或評分行，只要日期對了就抓第一個餐點名稱
    today_data = df[df['date'] == current_today].dropna(subset=['meal_name'])
    
    if not today_data.empty:
        # 抓取今天最新設定的餐點名稱
        meal_name = today_data['meal_name'].iloc[0]
        st.header(f"📅 今日餐點：{meal_name}")
        
        # 顯示目前的平均分（排除掉餐點設定行）
        today_ratings = today_data[today_data['user_name'].notna()]
        if not today_ratings.empty:
            avg_score = today_ratings['score'].mean()
            st.metric("目前平均得分", f"{avg_score:.1f} ⭐")

        # 評分表單
        with st.form("rating_form", clear_on_submit=True):
            u_name = st.text_input("你的暱稱 (必填)")
            u_score = st.slider("評分 (0-5)", 0.0, 5.0, 4.0, 0.5)
            u_comment = st.text_area("寫點評語 (選填)")
            submit_btn = st.form_submit_button("送出評分")
            
            if submit_btn:
                if not u_name:
                    st.error("請輸入暱稱再送出！")
                else:
                    new_rating = pd.DataFrame([{
                        "date": current_today,
                        "meal_name": meal_name,
                        "user_name": u_name,
                        "score": u_score,
                        "comment": u_comment,
                        "timestamp": datetime.now().strftime("%H:%M:%S")
                    }])
                    # 重新讀取並上傳
                    latest_df = get_data()
                    updated_df = pd.concat([latest_df, new_rating], ignore_index=True)
                    conn.update(data=updated_df)
                    st.success("評分成功！")
                    st.rerun()
    else:
        # Debug 資訊：如果還是失敗，這行會顯示系統抓到的日期，方便比對
        st.info(f"👋 嗨！管理員還沒設定今天的午餐名稱喔。")
        st.write(f"系統偵測今日日期為: `{current_today}`")
        st.write("目前試算表內有的日期:", df['date'].unique().tolist())

# --- 4. 歷史紀錄模式 ---
elif menu == "歷史紀錄":
    st.header("📜 歷史評分紀錄")
    # 只抓取有餐點名稱的日期
    history_dates = df[df['meal_name'].notna()]['date'].unique()
    
    if len(history_dates) > 0:
        sel_date = st.selectbox("選擇日期", sorted(history_dates, reverse=True))
        day_data = df[df['date'] == sel_date]
        
        meal = day_data['meal_name'].iloc[0]
        st.subheader(f"🍴 餐點：{meal}")
        
        # 只顯示有評論的資料
        comments_df = day_data[day_data['user_name'].notna()]
        if not comments_df.empty:
            st.metric("當日平均分", f"{comments_df['score'].mean():.1f} ⭐")
            st.table(comments_df[['user_name', 'score', 'comment', 'timestamp']])
        else:
            st.write("當天沒有評論紀錄。")
    else:
        st.write("目前尚無任何紀錄。")

# --- 5. 管理員模式 ---
elif menu == "管理員登入":
    pwd = st.text_input("輸入管理密碼", type="password")
    if pwd == "admin123":
        st.header("⚙️ 管理員後台")
        target_date = st.date_input("設定日期", datetime.now())
        target_date_str = target_date.strftime('%Y-%m-%d')
        new_meal = st.text_input("該日餐點名稱")
        
        if st.button("確認發布"):
            if new_meal:
                meal_entry = pd.DataFrame([{"date": target_date_str, "meal_name": new_meal}])
                latest_df = get_data()
                # 移除該日舊的餐點名稱(如果有)，避免重複
                latest_df = latest_df[~((latest_df['date'] == target_date_str) & (latest_df['user_name'].isna()))]
                updated_df = pd.concat([latest_df, meal_entry], ignore_index=True)
                conn.update(data=updated_df)
                st.success(f"已成功設定 {target_date_str} 的餐點！")
                st.rerun()
            else:
                st.error("請輸入餐點名稱")


