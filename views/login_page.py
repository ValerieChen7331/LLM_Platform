import streamlit as st
import yaml
from yaml import SafeLoader
import streamlit_authenticator as stauth

class LoginPage:
    def __init__(self, config_file='login_config.yaml'):
        self.config = self.load_config(config_file)
        self.authenticator = self.create_authenticator()

    def load_config(self, file_path):
        """加載配置文件並返回配置字典。"""
        try:
            with open(file_path, 'r') as file:
                return yaml.load(file, Loader=SafeLoader)
        except FileNotFoundError:
            st.error("配置文件未找到，請確認文件路徑。")
            st.stop()
        except yaml.YAMLError as e:
            st.error(f"加載配置文件時發生錯誤: {e}")
            st.stop()

    def create_authenticator(self):
        """創建 Streamlit 認證對象。"""
        try:
            return stauth.Authenticate(
                self.config['credentials'],
                self.config['cookie']['name'],
                self.config['cookie']['key'],
                self.config['cookie']['expiry_days'],
                self.config.get('pre-authorized', [])
            )
        except KeyError as e:
            st.error(f"配置文件中缺少必需的鍵: {e}")
            st.stop()

    def run(self):
        """運行登錄邏輯。"""
        self.authenticator.login(fields={'Form name': 'Login', 'Username': 'Username', 'Password': 'Password'})
        authentication_status = st.session_state.get("authentication_status")

        if authentication_status:
            st.session_state['logged_in'] = True
            return True
        elif authentication_status is False:
            st.error('用戶名或密碼不正確')
        else:
            st.warning('請輸入用戶名和密碼')

        st.session_state['logged_in'] = False
        return False
