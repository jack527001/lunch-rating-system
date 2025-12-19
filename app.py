import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- 1. 資料庫設定 (使用 SQLite) ---
def init_db():
    conn = sqlite3.connect('lunch_rating.db')
    c = conn.cursor()
    # 建立菜單表
    c.execute('''CREATE TABLE IF NOT EXISTS menu
                 (date TEXT PRIMARY KEY, meal_name TEXT)''')
    # 建立評分表
    c.execute('''CREATE TABLE IF NOT EXISTS ratings
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  date TEXT, 
                  user_name TEXT, 
                  score REAL, 
                  comment TEXT,
                  timestamp TEXT)''')
    conn.commit()
    conn.close()

# 初始化資料庫
init_db()

# --- 2. 輔助函式 ---
def get_today_str():
    return datetime.now().strftime('%Y-%m-%d')

def get_today_meal():
    conn = sqlite3.connect('lunch_rating.db')
    c = conn.cursor()
    c.execute("SELECT meal_name FROM menu WHERE date=?", (get_today_str(),))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def update_meal(name):
    conn = sqlite3.connect('lunch_rating.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO menu (date, meal_name) VALUES (?, ?)", 
              (get_today_str(), name))
    conn.commit()
    conn.close()

def add_rating(name, score, comment):
    conn = sqlite3.connect('lunch_rating.db')
    c = conn.cursor()
    c.execute("INSERT INTO ratings (date, user_name, score, comment, timestamp) VALUES (?, ?, ?, ?, ?)",
              (get_today_str(), name, score, comment, datetime.now().strftime('%H:%M:%S')))
    conn.commit()
    conn.close()

def get_today_ratings():
    conn = sqlite3.connect('lunch_rating.db')
    df = pd.read_sql_query("SELECT user_name, score, comment, timestamp FROM ratings WHERE date=?", 
                           conn, params=(get_today_str(),))
    conn.close()
    return df

# --- 3. 網頁介面設計 ---

st.set_page_config(page_title="公司午餐評分系統", page_icon="🍱")

st.title("🍱 公司每日午餐評分系統")

# 側邊欄：管理員區塊
with st.sidebar:
    st.header("⚙️ 管理員專區")
    admin_password = st.text_input("輸入管理員密碼", type="password")
    
    if admin_password == "admin123":  # 這裡可以改成你想要的密碼
        st.success("已登入")
        new_meal = st.text_input("輸入今日餐點名稱", placeholder="例如：香酥雞腿飯配滷蛋")
        if st.button("更新今日菜單"):
            if new_meal:
                update_meal(new_meal)
                st.success(f"已更新今日餐點為：{new_meal}")
                st.rerun()
            else:
                st.warning("請輸入餐點名稱")
    elif admin_password:
        st.error("密碼錯誤")

# 主畫面邏輯
today_meal = get_today_meal()

if not today_meal:
    st.info("👋 嗨！管理員還沒設定今天的午餐名稱喔。請等待更新。")
else:
    st.markdown(f"### 📅 今日餐點：**{today_meal}**")
    st.markdown("---")

    # --- 左邊：評分區 ---
    col1, col2 = st.columns([1, 1.5])

    with col1:
        st.subheader("✍️ 我要評分")
        with st.form("rating_form"):
            user_name = st.text_input("你的暱稱", placeholder="例如：設計部小陳")
            
            # 使用數字輸入框，允許小數點，設定範圍 0-5
            score = st.number_input("評分 (滿分 5 分)", min_value=0.0, max_value=5.0, value=4.0, step=0.1, format="%.1f")
            
            comment = st.text_area("寫點評語", placeholder="肉有點柴，但是配菜很好吃...")
            
            submitted = st.form_submit_button("送出評論")
            
            if submitted:
                if not user_name:
                    st.error("請輸入你的暱稱！")
                else:
                    add_rating(user_name, score, comment)
                    st.success("感謝你的回饋！")
                    st.rerun()

    # --- 右邊：統計與留言區 ---
    with col2:
        st.subheader("📊 大家怎麼說")
        
        df = get_today_ratings()
        
        if not df.empty:
            # 計算平均分
            avg_score = df['score'].mean()
            count = len(df)
            
            # 顯示大大的平均分數指標
            st.metric(label="今日平均分數", value=f"{avg_score:.1f} ⭐", delta=f"{count} 人已評分")
            
            st.write("---")
            st.write("#### 最新留言")
            
            # 顯示留言列表
            for index, row in df.iterrows():
                with st.chat_message("user"):
                    st.write(f"**{row['user_name']}** 給了 **{row['score']}** 分")
                    st.caption(f"時間: {row['timestamp']}")
                    if row['comment']:
                        st.info(row['comment'])
        else:
            st.write("目前還沒有人評分，搶第一個吧！")