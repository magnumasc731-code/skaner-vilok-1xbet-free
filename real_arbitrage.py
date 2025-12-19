import requests
import time
import json

# --- ⚙️ НАСТРОЙКИ ---
API_KEY = 'b00e08c845bd33c3e5c259c087c14659'
TELEGRAM_TOKEN = 'ВАШ_ТОКЕН_БОТА'
CHANNEL_ID = 'ВАШ_ID_КАНАЛА'

TOTAL_BANKROLL = 10000 
REF_1X = "https://refpa749456.pro/L?tag=s_2417237m_355c_&site=2417237&ad=355&r=live"

def get_odds():
    url = 'https://api.the-odds-api.com/v4/sports/upcoming/odds/'
    params = {'api_key': API_KEY, 'regions': 'eu', 'markets': 'h2h', 'oddsFormat': 'decimal'}
    try:
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            print(f"OK. Осталось лимитов: {r.headers.get('x-requests-remaining')}")
            return r.json()
    except: pass
    return None

def send_tg_alert(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    # Только одна кнопка для 1xBet
    keyboard = {"inline_keyboard": [[{"text": "📱 Сделать ставку в 1xBet", "url": REF_1X}]]}
    
    payload = {
        "chat_id": CHANNEL_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
        "reply_markup": json.dumps(keyboard)
    }
    requests.post(url, json=payload)

def round_stake(amount):
    return int(round(amount / 50.0) * 50.0)

def process_events():
    events = get_odds()
    if not events: return
    
    for event in events:
        best_odds = {}
        has_1x = False
        for bookie in event['bookmakers']:
            if not bookie['markets']: continue
            if bookie['key'] == 'onexbet': has_1x = True
            for outcome in bookie['markets'][0]['outcomes']:
                name = outcome['name']
                price = outcome['price']
                if name not in best_odds or price > best_odds[name]['price']:
                    best_odds[name] = {'price': price, 'bookie': bookie['title']}

        if not has_1x: continue
        inv_sum = sum(1/item['price'] for item in best_odds.values())
        
        if inv_sum < 1.0:
            profit = round((1/inv_sum - 1)*100, 2)
            if profit > 0.5:
                stakes = []
                for name, data in best_odds.items():
                    raw_stake = (TOTAL_BANKROLL / inv_sum) / data['price']
                    stakes.append(f"🔹 {name}: <b>{data['price']}</b> ({data['bookie']}) ➡️ <b>{round_stake(raw_stake)}₽</b>")

                msg = (
                    f"🔥 <b>НАЙДЕНА ВИЛКА: {profit}%</b>\n"
                    f"🏆 {event['sport_title']}\n"
                    f"⚔️ {event['home_team']} vs {event['away_team']}\n"
                    f"💰 Банк: <b>{TOTAL_BANKROLL}₽</b>\n\n"
                    f"{chr(10).join(stakes)}"
                )
                send_tg_alert(msg)
                time.sleep(2)

if __name__ == "__main__":
    while True:
        try:
            process_events()
        except: pass
        time.sleep(3600)
