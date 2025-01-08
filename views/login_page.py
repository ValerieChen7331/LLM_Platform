import yaml
import streamlit as st
import streamlit_authenticator as stauth
from yaml.loader import SafeLoader

class LoginPage:
    def __init__(self, config_file='login_config.yaml'):
        """初始化，載入設定檔案並創建認證器"""
        self.config = self.load_config(config_file)
        self.authenticator = self.create_authenticator()

    def load_config(self, config_file):
        """載入 YAML 設定檔案"""
        with open(config_file, 'r') as file:
            return yaml.load(file, Loader=SafeLoader)

    def create_authenticator(self):
        """創建認證器物件"""
        return stauth.Authenticate(
            self.config['credentials'],
            self.config['cookie']['name'],
            self.config['cookie']['key'],
            self.config['cookie']['expiry_days'],
            self.config['pre-authorized']
        )

    def run(self):
        """執行登入頁面邏輯"""
        self.authenticator.login(fields={
            'Form name': '登入',
            'Username': '帳號',
            'Password': '密碼',
            'Login': '登入'
        })

        if st.session_state.get('authentication_status'):
            return True

        elif st.session_state.get('authentication_status') is False:
            # 驗證失敗，顯示錯誤訊息
            st.error('用戶名或密碼錯誤')
            return False
        elif st.session_state.get('authentication_status') is None:
            # 尚未輸入用戶名或密碼，顯示警告訊息
            st.warning('請輸入用戶名和密碼')
            return False

if __name__ == '__main__':
    # 創建並運行登入頁面
    page = LoginPage()
    page.run()
