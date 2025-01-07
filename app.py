import streamlit as st
from views.login_page import LoginPage
from views.main_page import MainPage

# 确保 set_page_config 是第一个调用的 Streamlit 命令
st.set_page_config(page_title="南亞塑膠GenAI")

def main():
    # 主函數
    #login_page = LoginPage()
    #if login_page.run():
    main_page = MainPage()
    main_page.show_main_page()

if __name__ == "__main__":
    main()
