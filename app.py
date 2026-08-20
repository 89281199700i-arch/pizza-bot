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

ADMIN_USER = "kvakish_"  # ← ТВОЙ НИК

SAVE_FILE = "pizza_data.json"
COOLDOWN_TIME = 5

print("🚀 ЗАПУСК ПИЦЦА-БОТА (АДМИН-КОМАНДЫ С ПОДТВЕРЖДЕНИЕМ)")

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
#  ОТПРАВКА СООБЩЕНИЙ В ЧАТ
# ============================================================
def send_to_chat(ws, msg):
    if ws and ws.connected:
        try:
            ws.send(f"PRIVMSG {TWITCH_CHANNEL} :{msg}\r\n")
            print(f"📤 Отправлено в чат: {msg}")
        except Exception as e:
            print(f"❌ Ошибка отправки: {e}")

# ============================================================
#  КОМАНДЫ
# ============================================================
def handle_command(user, cmd, args, ws=None):
    cmd = cmd.lower()
    player = get_player(user)
    now = time.time()

    # --- ОБЫЧНЫЕ КОМАНДЫ (!) ---
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
    #  АДМИН-КОМАНДЫ (ТОЛЬКО ДЛЯ ТЕБЯ)
    # ============================================================
    if cmd.startswith(':') and cmd.endswith(':'):
        if user.lower() != ADMIN_USER.lower():
            return None  # игнорируем
        
        inner = cmd[1:-1].strip()
        if not inner:
            return "❌ @{user}, напиши: :команда аргументы:"
        
        parts = inner.split()
        subcmd = parts[0].lower()
        subargs = parts[1:] if len(parts) > 1 else []
        
        # Отправляем первое сообщение — "в обработке..."
        processing_msg = f"🔧 Админ-команда \"{inner}\" в обработке..."
        send_to_chat(ws, processing_msg)
        
        result = None
        
        # --- Обработка подкоманд ---
        if subcmd == "всемпицца":
            if not subargs:
                result = "❌ @{user}, напиши: :всемпицца <число>:"
            else:
                try:
                    amount = int(subargs[0])
                    if amount <= 0:
                        result = "❌ @{user}, число должно быть положительным!"
                    else:
                        count = 0
                        for name in list(players.keys()):
                            p = get_player(name)
                            p["pizza"] += amount
                            p["total_pizza"] += amount
                            save_player(name)
                            count += 1
                        result = f"✅ @{user}, всем {count} игрокам добавлено по {amount} пиццы! 🍕"
                except:
                    result = "❌ @{user}, напиши число: :всемпицца 10:"
        
        elif subcmd == "добавитьпицца":
            if len(subargs) < 2:
                result = "❌ @{user}, напиши: :добавитьпицца <ник> <количество>:"
            else:
                target = subargs[0]
                try:
                    amount = int(subargs[1])
                    if amount <= 0:
                        result = "❌ @{user}, число должно быть положительным!"
                    elif target not in players:
                        result = f"❌ @{user}, пользователь '{target}' не найден!"
                    else:
                        p = get_player(target)
                        p["pizza"] += amount
                        p["total_pizza"] += amount
                        save_player(target)
                        result = f"✅ @{user}, у {target} добавлено {amount} пиццы! Теперь: {p['pizza']} 🍕"
                except:
                    result = "❌ @{user}, напиши число!"
        
        elif subcmd == "удалитьпицца":
            if len(subargs) < 2:
                result = "❌ @{user}, напиши: :удалитьпицца <ник> <количество>:"
            else:
                target = subargs[0]
                try:
                    amount = int(subargs[1])
                    if amount <= 0:
                        result = "❌ @{user}, число должно быть положительным!"
                    elif target not in players:
                        result = f"❌ @{user}, пользователь '{target}' не найден!"
                    else:
                        p = get_player(target)
                        if p["pizza"] < amount:
                            result = f"❌ @{user}, у {target} только {p['pizza']} пиццы!"
                        else:
                            p["pizza"] -= amount
                            save_player(target)
                            result = f"✅ @{user}, у {target} удалено {amount} пиццы! Осталось: {p['pizza']} 🍕"
                except:
                    result = "❌ @{user}, напиши число!"
        
        elif subcmd == "сбросить":
            players.clear()
            save_data(players)
            result = f"✅ @{user}, все данные сброшены!"
        
        elif subcmd == "помощь":
            result = """👑 Админ-команды (через :) :
:всемпицца <число> — всем +пицца
:добавитьпицца <ник> <число> — добавить игроку
:удалитьпицца <ник> <число> — удалить у игрока
:сбросить — удалить всех игроков
:помощь — это сообщение"""
        
        else:
            result = f"❌ @{user}, неизвестная команда. Напиши :помощь:"
        
        # Отправляем второе сообщение — результат
        if result:
            send_to_chat(ws, result)
        
        return None  # ничего не возвращаем, так как уже отправили
    
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
                print(f"🔍 Получено: {user} -> {text}")
                if text.startswith('!'):
                    args = text.split()
                    resp = handle_command(user, args[0], args[1:], ws)
                    if resp:
                        send_to_chat(ws, resp)
                elif text.startswith(':') and text.endswith(':'):
                    # Обрабатываем админ-команды без разделения на аргументы
                    handle_command(user, text, [], ws)
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