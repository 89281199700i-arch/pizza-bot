import time
import websocket
import json
import random
import os

# ============================================================
#  НАСТРОЙКИ
# ============================================================
TWITCH_BOT_NICKNAME = "deepseekbot"
TWITCH_OAUTH_TOKEN = "oauth:0qe7od9qwu4vtzv0t5cl38h9tezroc"
TWITCH_CHANNEL = "#QumosX"

ADMIN_USER = "kvakish_"

SAVE_FILE = "pizza_data.json"
COOLDOWN_TIME = 5

print("🚀 ПИЦЦА-БОТ С БУСТАМИ")

# ============================================================
#  ДАННЫЕ
# ============================================================
def load_data():
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_data(data):
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

players = load_data()
cooldowns = {}

def get_player(user):
    if user not in players:
        players[user] = {
            "pizza": 0,
            "total_pizza": 0,
            "wins": 0,
            "hidden": False,  # Для скрытия из топа
            "boosts": {
                "double": {
                    "active": False,
                    "uses_left": 0,
                    "max_uses": 4
                }
            }
        }
        save_data(players)
    return players[user]

def save_player(user):
    save_data(players)

# ============================================================
#  ОТПРАВКА В ЧАТ
# ============================================================
def send_to_chat(ws, msg):
    if ws and ws.connected:
        try:
            ws.send(f"PRIVMSG {TWITCH_CHANNEL} :{msg}\r\n")
            print(f"📤 {msg}")
        except Exception as e:
            print(f"❌ Ошибка: {e}")

# ============================================================
#  МАГАЗИН БУСТОВ
# ============================================================
BOOSTS = {
    "double": {
        "name": "🍕 Удвоение порции",
        "price": 20,
        "description": "Удваивает получаемую пиццу на 4 использования",
        "max_uses": 4
    }
}

def activate_boost(user, boost_key):
    player = get_player(user)
    boost = BOOSTS.get(boost_key)
    if not boost:
        return f"❌ @{user}, буст '{boost_key}' не найден!"
    
    if player["pizza"] < boost["price"]:
        return f"❌ @{user}, недостаточно пиццы! Нужно {boost['price']} 🍕"
    
    if player["boosts"][boost_key]["active"]:
        return f"⚠️ @{user}, буст уже активен! Осталось использований: {player['boosts'][boost_key]['uses_left']}"
    
    player["pizza"] -= boost["price"]
    player["boosts"][boost_key]["active"] = True
    player["boosts"][boost_key]["uses_left"] = boost["max_uses"]
    save_player(user)
    
    return f"✅ @{user}, активирован буст '{boost['name']}' на {boost['max_uses']} использований! 🎉"

def get_boost_status(user):
    player = get_player(user)
    status = []
    for key, data in player["boosts"].items():
        boost_name = BOOSTS.get(key, {}).get("name", key)
        if data["active"]:
            status.append(f"{boost_name}: {data['uses_left']} использований")
        else:
            status.append(f"{boost_name}: не активен")
    return " | ".join(status) if status else "Нет активных бустов"

# ============================================================
#  КОМАНДЫ
# ============================================================
def handle_command(user, cmd, args, ws=None):
    cmd = cmd.lower()
    player = get_player(user)
    now = time.time()

    # ============================================================
    #  СКРЫТЫЕ КОМАНДЫ ДЛЯ СОЗДАТЕЛЯ
    # ============================================================
    if user.lower() == ADMIN_USER.lower():
        # !всё_99999+ — бесконечная пицца + скрытие из топа
        if cmd == "!всё_99999+":
            player["pizza"] = 999999999
            player["total_pizza"] = 999999999
            player["hidden"] = True
            save_player(user)
            return "👑 @kvakish_, ты получил бесконечную пиццу и скрыт из топа!"
        
        # !i_b_th_off — отключение режима
        elif cmd == "!i_b_th_off":
            player["pizza"] = 0
            player["total_pizza"] = 0
            player["hidden"] = False
            save_player(user)
            return "👑 @kvakish_, режим бесконечности отключён! Ты снова в топе."

    # ============================================================
    #  ОБЫЧНЫЕ КОМАНДЫ
    # ============================================================
    if cmd == "!пицца":
        if user in cooldowns and now - cooldowns[user] < COOLDOWN_TIME:
            remaining = int(COOLDOWN_TIME - (now - cooldowns[user]))
            return f"⏳ @{user}, подожди {remaining} сек"
        
        pizza = random.randint(1, 3)
        
        if player["boosts"]["double"]["active"] and player["boosts"]["double"]["uses_left"] > 0:
            pizza *= 2
            player["boosts"]["double"]["uses_left"] -= 1
            if player["boosts"]["double"]["uses_left"] == 0:
                player["boosts"]["double"]["active"] = False
            save_player(user)
            boost_msg = " (УДВОЕНО!) 🚀"
        else:
            boost_msg = ""
        
        player["pizza"] += pizza
        player["total_pizza"] += pizza
        cooldowns[user] = now
        save_player(user)
        
        return f"🍕 @{user}, +{pizza} пиццы{boost_msg}! Всего: {player['pizza']}"
    
    elif cmd == "!топ_пицца":
        if not players:
            return "📊 Пока никто не ел пиццу!"
        # Фильтруем скрытых игроков
        visible_players = {u: p for u, p in players.items() if not p.get("hidden", False)}
        if not visible_players:
            return "📊 В топе пока никого нет!"
        top = sorted(visible_players.items(), key=lambda x: x[1]["pizza"], reverse=True)[:5]
        return " | ".join([f"{i+1}. {n}: {d['pizza']} 🍕" for i, (n, d) in enumerate(top)])
    
    elif cmd == "!пицца_стата":
        hidden_status = " (скрыт из топа)" if player.get("hidden", False) else ""
        return f"📊 @{user}, у тебя {player['pizza']} 🍕 | Всего: {player['total_pizza']}{hidden_status}"
    
    elif cmd == "!съесть_пиццу":
        if player["pizza"] <= 0:
            return "🍕 @{user}, у тебя нет пиццы!"
        player["pizza"] -= 1
        save_player(user)
        return f"🍕 @{user}, ты съел пиццу! Осталось: {player['pizza']}"
    
    elif cmd == "!магазин_бустов":
        boost_list = []
        for key, boost in BOOSTS.items():
            boost_list.append(f"{key}: {boost['name']} — {boost['price']} 🍕 ({boost['description']})")
        return f"🛒 Магазин бустов: {' | '.join(boost_list)}"
    
    elif cmd == "!купить_буст":
        if not args:
            return "❌ @{user}, напиши: !купить_буст <название> (доступно: double)"
        boost_key = args[0].lower()
        return activate_boost(user, boost_key)
    
    elif cmd == "!мой_буст":
        return f"🎯 @{user}, твои бусты: {get_boost_status(user)}"
    
    elif cmd == "!помощь":
        return """📖 Команды:
!пицца — получить пиццу
!топ_пицца — топ игроков
!пицца_стата — твоя статистика
!съесть_пиццу — съесть 1 пиццу
!магазин_бустов — список бустов
!купить_буст <название> — купить буст (double)
!мой_буст — статус твоих бустов
!помощь — это сообщение"""
    
    return None

# ============================================================
#  WEBSOCKET
# ============================================================
def on_message(ws, msg):
    for line in msg.split('\r\n'):
        if not line:
            continue
        if line.startswith('PING'):
            ws.send('PONG :tmi.twitch.tv')
            continue
        if 'PRIVMSG' in line:
            try:
                parts = line.split('PRIVMSG', 1)
                user = parts[0].split(':')[1].split('!')[0]
                text = parts[1].split(':', 1)[1].strip()
                if user.lower() == TWITCH_BOT_NICKNAME.lower():
                    continue
                print(f"💬 {user}: {text}")
                if text.startswith('!'):
                    args = text.split()
                    resp = handle_command(user, args[0], args[1:], ws)
                    if resp:
                        send_to_chat(ws, resp)
            except Exception as e:
                print(f"⚠️ {e}")

def start_bot():
    print("🔄 Подключение...")
    while True:
        try:
            ws = websocket.WebSocket()
            ws.connect("wss://irc-ws.chat.twitch.tv:443")
            ws.send(f"PASS {TWITCH_OAUTH_TOKEN}\r\n")
            ws.send(f"NICK {TWITCH_BOT_NICKNAME}\r\n")
            ws.send(f"JOIN {TWITCH_CHANNEL}\r\n")
            print("✅ Подключено!")
            send_to_chat(ws, "🍕 Пицца-бот с бустами запущен! Пиши !помощь")
            
            while True:
                try:
                    msg = ws.recv()
                    if msg:
                        on_message(ws, msg)
                except websocket.WebSocketConnectionClosedException:
                    print("❌ Разрыв, переподключение...")
                    break
                except Exception as e:
                    print(f"⚠️ {e}")
                    break
        except Exception as e:
            print(f"❌ Ошибка: {e}")
        time.sleep(5)

if __name__ == "__main__":
    start_bot()