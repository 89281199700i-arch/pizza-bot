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

print("🚀 ПИЦЦА-БОТ С МАГАЗИНОМ БУСТОВ")

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
        return f"❌ Буст '{boost_key}' не найден!"
    
    if player["pizza"] < boost["price"]:
        return f"❌ @{user}, недостаточно пиццы! Нужно {boost['price']} 🍕"
    
    # Проверяем, активен ли уже буст
    if player["boosts"][boost_key]["active"]:
        return f"⚠️ @{user}, буст уже активен! Осталось использований: {player['boosts'][boost_key]['uses_left']}"
    
    # Активируем буст
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

    # --- ОБЫЧНЫЕ КОМАНДЫ ---
    if cmd == "!пицца":
        if user in cooldowns and now - cooldowns[user] < COOLDOWN_TIME:
            remaining = int(COOLDOWN_TIME - (now - cooldowns[user]))
            return f"⏳ @{user}, подожди {remaining} сек"
        
        # Базовая порция
        pizza = random.randint(1, 3)
        
        # Проверяем буст удвоения
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
    
    elif cmd == "!топпицца":
        if not players:
            return "📊 Пока никто не ел пиццу!"
        top = sorted(players.items(), key=lambda x: x[1]["pizza"], reverse=True)[:5]
        return " | ".join([f"{i+1}. {n}: {d['pizza']} 🍕" for i, (n, d) in enumerate(top)])
    
    elif cmd == "!пиццастата":
        return f"📊 @{user}, у тебя {player['pizza']} 🍕 | Всего: {player['total_pizza']}"
    
    elif cmd == "!съестьпиццу":
        if player["pizza"] <= 0:
            return "🍕 @{user}, у тебя нет пиццы!"
        player["pizza"] -= 1
        save_player(user)
        return f"🍕 @{user}, ты съел пиццу! Осталось: {player['pizza']}"
    
    # --- МАГАЗИН БУСТОВ ---
    elif cmd == "!магазин" or cmd == "!бусты":
        boost_list = []
        for key, boost in BOOSTS.items():
            boost_list.append(f"{key}: {boost['name']} — {boost['price']} 🍕 ({boost['description']})")
        return f"🛒 Магазин бустов: {' | '.join(boost_list)}"
    
    elif cmd == "!купитьбуст":
        if not args:
            return "❌ @{user}, напиши: !купитьбуст <название> (доступно: double)"
        boost_key = args[0].lower()
        return activate_boost(user, boost_key)
    
    elif cmd == "!мойбуст":
        return f"🎯 @{user}, твои бусты: {get_boost_status(user)}"
    
    elif cmd == "!помощь":
        return """📖 Команды:
!пицца — получить пиццу
!топпицца — топ игроков
!пиццастата — твоя статистика
!съестьпиццу — съесть 1 пиццу
!магазин — список бустов
!купитьбуст <название> — купить буст (double)
!мойбуст — статус твоих бустов
!помощь — это сообщение"""

    # ============================================================
    #  АДМИН-КОМАНДЫ
    # ============================================================
    if cmd.startswith(':') and cmd.endswith(':'):
        if user.lower() != ADMIN_USER.lower():
            return None
        
        inner = cmd[1:-1].strip()
        if not inner:
            return "❌ @{user}, напиши: :команда аргументы:"
        
        parts = inner.split()
        subcmd = parts[0].lower()
        subargs = parts[1:] if len(parts) > 1 else []
        
        if subcmd == "всемпицца":
            if not subargs:
                return "❌ Напиши: :всемпицца <число>:"
            try:
                amount = int(subargs[0])
                if amount <= 0:
                    return "❌ Число должно быть положительным!"
                count = 0
                for name in list(players.keys()):
                    p = get_player(name)
                    p["pizza"] += amount
                    p["total_pizza"] += amount
                    save_player(name)
                    count += 1
                return f"✅ Всем {count} игрокам +{amount} пиццы! 🍕"
            except:
                return "❌ Напиши число: :всемпицца 10:"
        
        elif subcmd == "добавитьпицца":
            if len(subargs) < 2:
                return "❌ Напиши: :добавитьпицца <ник> <число>:"
            target = subargs[0]
            try:
                amount = int(subargs[1])
                if amount <= 0:
                    return "❌ Число должно быть положительным!"
                if target not in players:
                    return f"❌ Игрок '{target}' не найден!"
                p = get_player(target)
                p["pizza"] += amount
                p["total_pizza"] += amount
                save_player(target)
                return f"✅ {target} +{amount} пиццы! Теперь: {p['pizza']} 🍕"
            except:
                return "❌ Напиши число!"
        
        elif subcmd == "удалитьпицца":
            if len(subargs) < 2:
                return "❌ Напиши: :удалитьпицца <ник> <число>:"
            target = subargs[0]
            try:
                amount = int(subargs[1])
                if amount <= 0:
                    return "❌ Число должно быть положительным!"
                if target not in players:
                    return f"❌ Игрок '{target}' не найден!"
                p = get_player(target)
                if p["pizza"] < amount:
                    return f"❌ У {target} только {p['pizza']} пиццы!"
                p["pizza"] -= amount
                save_player(target)
                return f"✅ {target} -{amount} пиццы! Осталось: {p['pizza']} 🍕"
            except:
                return "❌ Напиши число!"
        
        elif subcmd == "сбросить":
            players.clear()
            save_data(players)
            return "✅ Все данные сброшены!"
        
        elif subcmd == "помощь":
            return """👑 Админ-команды:
:всемпицца <число> — всем +пицца
:добавитьпицца <ник> <число> — игроку
:удалитьпицца <ник> <число> — у игрока
:сбросить — удалить всех
:помощь — это сообщение"""
        
        else:
            return f"❌ Неизвестная команда. Напиши :помощь:"
    
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
                elif text.startswith(':') and text.endswith(':'):
                    resp = handle_command(user, text, [], ws)
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
            send_to_chat(ws, "🍕 Пицца-бот с бустами запущен! Пиши !магазин")
            
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