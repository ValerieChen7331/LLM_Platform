import streamlit as st
from controllers.ui_controller import UIController
from views.main_page_sidebar import Sidebar
from views.main_page_content import MainContent
from services.llm_services import LLMService

class MainPage:
    def __init__(self):
        """初始化主頁面物件"""
        self.controller = UIController()
        self.chat_session_data = self.controller.initialize_session_state()
        self.chat_session_data["username"] = st.session_state.get("username")
        self.sidebar = Sidebar(self.chat_session_data)
        self.main_content = MainContent(self.chat_session_data)
        self.llm_service = LLMService(self.chat_session_data)

    def show(self):
        """顯示主頁面"""
        self.sidebar.display()       # 顯示側邊欄
        self.main_content.display()  # 顯示主內容

        # 處理聊天輸入
        if query := st.chat_input():   # 如果使用者在聊天框中輸入了內容
            st.chat_message("human").write(query)
            response, self.chat_session_data = self.llm_service.query(query)
            st.chat_message("ai").write(response)

def main():
    """主函數"""
    MainPage().show()

if __name__ == "__main__":
    main()
