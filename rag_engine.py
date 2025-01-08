import streamlit as st
from views.login_page import LoginPage
from views.main_page import MainPage
from views.register_page import RegisterPage

# 設定 Streamlit 頁面配置
st.set_page_config(page_title="南亞塑膠GenAI")

def main():
    """主函數，用於控制應用的流程"""
    if not st.session_state.get('authentication_status'):
        choice = st.sidebar.selectbox("選擇頁面", ["登入", "註冊"])

        if choice == "登入":
            # 創建登入頁面物件
            login_page = LoginPage()
            # 執行登入頁面邏輯，並檢查是否通過驗證
            if login_page.run():
                # 創建主頁面物件並顯示主頁面
                main_page = MainPage()
                main_page.show()
        elif choice == "註冊":
            # 創建註冊頁面物件並顯示註冊頁面
            register_page = RegisterPage()
            register_page.show()
    else:
        main_page = MainPage()
        main_page.show()


if __name__ == "__main__":
    # 執行主函數
    main()
