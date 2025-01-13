import streamlit as st
from controllers.ui_controller import UIController
from models.database_userRecords import UserRecordsDB
from views.main_page_sidebar import Sidebar
from views.main_page_content import MainContent

class MainPage:
    def __init__(self):
        """初始化主頁面物件"""
        self.controller = UIController()
        self.userRecords_db = UserRecordsDB()
        self.sidebar = Sidebar(self.controller)
        self.main_content = MainContent(self.controller, self.userRecords_db)
        self.controller.initialize_session_state()  # 初始化 session state

    def show(self):
        """顯示主頁面"""
        print('main page')
        self.sidebar.display()       # 顯示側邊欄
        self.main_content.display()  # 顯示主內容

        if query := st.chat_input():                # 如果使用者在聊天框中輸入了內容
            self.controller.handle_query(query)     # 處理使用者的查詢


def main():
    """主函數"""
    main_page = MainPage()
    main_page.show()

if __name__ == "__main__":
    main()
