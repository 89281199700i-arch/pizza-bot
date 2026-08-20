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

ADMIN_USER = "kvakish_"  # ← ТВОЙ НИК (БЕЗ @)

SAVE_FILE = "pizza_data.json"
COOLDOWN_TIME = 5

print("🚀 ЗАПУСК ПИЦЦА-БОТА (С АДМИН-КОМАНДАМИ)")

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
            "wins": 0
        }
        save_data(players)
    return players[user]

def save_player(user):
    save_data(players)

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
            return f"⏳ @{user}, подожди {remaining} сек, пицца ещё готовится! 🍕"
        
        pizza = random.randint(1, 3)
        player["pizza"] += pizza
        player["total_pizza"] += pizza
        cooldowns[user] = now
        save_player(user)
        return f"🍕 @{user}, ты получил {pizza} пиццы! Всего: {player['pizza']} 🍕"
    
    elif cmd == "!топпицца":
        if not players:
            return "📊 Пока никто не ел пиццу!"
        top = sorted(players.items(), key=lambda x: x[1]["pizza"], reverse=True)[:5]
        result = ["🏆 ТОП Пицца:"]
        for i, (name, data) in enumerate(top, 1):
            result.append(f"{i}. {name}: {data['pizza']} 🍕")
        return " | ".join(result)
    
    elif cmd == "!пиццастата":
        return f"📊 @{user}, у тебя {player['pizza']} 🍕 | Всего получено: {player['total_pizza']} 🍕"
    
    elif cmd == "!съестьпиццу":
        if player["pizza"] <= 0:
            return "🍕 @{user}, у тебя нет пиццы! Сначала получи её через !пицца"
        player["pizza"] -= 1
        save_player(user)
        return f"🍕 @{user}, ты съел пиццу! Осталось: {player['pizza']} 🍕"
    
    elif cmd == "!помощь":
        return """📖 Команды пицца-бота:
!пицца — получить пиццу (кулдаун 5 сек)
!топпицца — топ по пицце
!пиццастата — твоя статистика
!съестьпиццу — съесть 1 пиццу
!помощь — это сообщение"""
    
    # ============================================================
    #  АДМИН-КОМАНДЫ (только для создателя)
    # ============================================================
    if user.lower() != ADMIN_USER.lower():
        return None
    
    # --- ;всемпицца <число> ---
    if cmd == ";всемпицца":
        if not args:
            return "❌ @{user}, напиши: ;всемпицца <число>"
        try:
            amount = int(args[0])
            if amount <= 0:
                return "❌ @{user}, число должно быть положительным!"
            
            count = 0
            for name in list(players.keys()):
                p = get_player(name)
                p["pizza"] += amount
                p["total_pizza"] += amount
                save_player(name)
                count += 1
            
            return f"✅ @{user}, всем {count} игрокам добавлено по {amount} пиццы! 🍕"
        except:
            return "❌ @{user}, напиши число: ;всемпицца 10"
    
    # --- ;добавитьпицца <ник> <число> ---
    elif cmd == ";добавитьпицца":
        if len(args) < 2:
            return "❌ @{user}, напиши: ;добавитьпицца <ник> <количество>"
        
        target = args[0]
        try:
            amount = int(args[1])
            if amount <= 0:
                return "❌ @{user}, число должно быть положительным!"
        except:
            return "❌ @{user}, напиши число!"
        
        if target not in players:
            return f"❌ @{user}, пользователь '{target}' не найден!"
        
        p = get_player(target)
        p["pizza"] += amount
        p["total_pizza"] += amount
        save_player(target)
        return f"✅ @{user}, у {target} добавлено {amount} пиццы! Теперь: {p['pizza']} 🍕"
    
    # --- ;удалитьпицца <ник> <число> ---
    elif cmd == ";удалитьпицца":
        if len(args) < 2:
            return "❌ @{user}, напиши: ;удалитьпицца <ник> <количество>"
        
        target = args[0]
        try:
            amount = int(args[1])
            if amount <= 0:
                return "❌ @{user}, число должно быть положительным!"
        except:
            return "❌ @{user}, напиши число!"
        
        if target not in players:
            return f"❌ @{user}, пользователь '{target}' не найден!"
        
        p = get_player(target)
        if p["pizza"] < amount:
            return f"❌ @{user}, у {target} только {p['pizza']} пиццы!"
        
        p["pizza"] -= amount
        save_player(target)
        return f"✅ @{user}, у {target} удалено {amount} пиццы! Осталось: {p['pizza']} 🍕"
    
    return None

# ============================================================
#  WEBSOCKET
# ============================================================
def send_to_chat(ws, msg):
    if ws and ws.connected:
        try:
            ws.send(f"PRIVMSG {TWITCH_CHANNEL} :{msg}\r\n")
            print(f"📤 Отправлено в чат: {msg}")
        except Exception as e:
            print(f"❌ Ошибка отправки: {e}")

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
                    resp = handle_command(user, args[0], args[1:])
                    if resp:
                        send_to_chat(ws, resp)
            except Exception as e:
                print(f"⚠️ Ошибка: {e}")

def start_bot():
    print("🔄 Подключение к Twitch...")
    while True:
        try:
            ws = websocket.WebSocket()
            ws.connect("wss://irc-ws.chat.twitch.tv:443")
            ws.send(f"PASS {TWITCH_OAUTH_TOKEN}\r\n")
            ws.send(f"NICK {TWITCH_BOT_NICKNAME}\r\n")
            ws.send(f"JOIN {TWITCH_CHANNEL}\r\n")
            print("✅ Подключено к Twitch чату!")
            send_to_chat(ws, "🍕 Пицца-бот запущен! Пиши !пицца и получай пиццу!")
            
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