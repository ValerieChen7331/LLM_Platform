import streamlit as st
import yaml
import streamlit_authenticator as stauth
from yaml.loader import SafeLoader

class RegisterPage:
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

    def show(self):
        """顯示註冊頁面"""
        st.title("註冊新用戶")
        
        try:
            email_of_registered_user, username_of_registered_user, name_of_registered_user = self.authenticator.register_user(pre_authorization=True)
            if email_of_registered_user:
                st.success('User registered successfully')
                with open('login_config.yaml', 'w') as file:
                    yaml.dump(self.config, file, default_flow_style=False)
            elif email_of_registered_user==False:
                st.error('User registered unsuccessfully')
        except Exception as e:
            st.error(e)


