"""
Modul Integrasi Telegram Bot - SISKA v2.1
Pengembang: M Nasri AW - email: nasriaw@gmail.com
"""

import requests

def send_telegram_notification(bot_token, chat_id, message):
    """
    Mengirimkan pesan notifikasi real-time ke Telegram Chat ID yang ditentukan.
    """
    if not bot_token or not chat_id:
        return False, "Bot Token atau Chat ID belum dikonfigurasi."
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=5)
        if response.status_code == 200:
            return True, "Notifikasi Telegram berhasil dikirim."
        else:
            return False, f"Gagal mengirim: {response.text}"
    except Exception as e:
        return False, f"Error: {str(e)}"