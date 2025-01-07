import streamlit as st
from views.login_page import LoginPage
from views.main_page import MainPage

# 設定頁面配置
st.set_page_config(page_title="南亞塑膠GenAI")
st.session_state.setdefault('logged_in', False)

# 提取查詢參數
query_params = st.experimental_get_query_params()
page = query_params.get("page", ["login"])[0]

def main():
    # 根據頁面參數渲染對應的頁面
    if page == "login":
        handle_login()
    elif page == "main":
        handle_main_page()
    else:
        # 如果參數值不匹配，默認跳轉到登錄頁面
        st.experimental_set_query_params(page="login")
        handle_login()

def handle_login():
    login_page = LoginPage()
    if login_page.run():
        # 只有在登入成功時才重定向到主頁面
        st.session_state.logged_in = True
        st.experimental_set_query_params(page="main")
        st.rerun()

def handle_main_page():
    # 確保只有在登錄後才能訪問主頁面
    if st.session_state.logged_in:
        main_page = MainPage()
        main_page.show_main_page()
    else:
        # 未登錄時重定向回登入頁面
        st.experimental_set_query_params(page="login")
        st.rerun()

if __name__ == "__main__":
    main()
