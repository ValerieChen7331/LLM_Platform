import streamlit as st
from controllers.ui_controller import UIController

def boot():
    ui_controller = UIController()
    ui_controller.configure_page()
    ui_controller.initialize_session_state()
    ui_controller.select_llm_type()
    ui_controller.input_fields()

    st.button("提交文件", on_click=ui_controller.process_uploaded_documents)

    ui_controller.display_messages()

    if query := st.chat_input():
        ui_controller.handle_query(query)

    ui_controller.display_chat_history()

if __name__ == '__main__':
    boot()
