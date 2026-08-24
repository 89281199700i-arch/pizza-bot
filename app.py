import time
import websocket
import json
import random
import os
import threading

# ============================================================
#  НАСТРОЙКИ
# ============================================================
TWITCH_BOT_NICKNAME = "deepseekbot"
TWITCH_OAUTH_TOKEN = "oauth:0qe7od9qwu4vtzv0t5cl38h9tezroc"
TWITCH_CHANNEL = "#QumosX"

ADMIN_USER = "kvakish_"

SAVE_FILE = "pizza_data.json"
COOLDOWN_TIME = 5
EVENT_TIMEOUT = 60  # 1 минута

print("🚀 ПИЦЦА-БОТ С ИВЕНТАМИ (ИСПРАВЛЕННЫЙ)")

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

# ============================================================
#  ИВЕНТ
# ============================================================
event_active = False
event_answer = []
event_timer = None
event_ingredients = [
    "Томатный соус", "Моцарелла", "Тесто", "Орегано", 
    "Пепперони", "Лук", "Перец", "Грибы", 
    "Оливки", "Халапеньо", "Чеснок", "Ветчина", 
    "Ананас", "Анчоусы", "Фасоль"
]
event_ws = None

def get_player(user):
    if user not in players:
        players[user] = {
            "pizza": 0,
            "total_pizza": 0,
            "wins": 0,
            "hidden": False,
            "event_wins": 0,
            "boosts": {
                "double": {"active": False, "uses_left": 0, "max_uses": 4}
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
#  БУСТЫ
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
#  ИВЕНТ "ПРОФЕССИОНАЛ ПО ПИЦЦЕ"
# ============================================================
def stop_event():
    global event_active, event_timer
    if event_active:
        event_active = False
        event_timer = None
        send_to_chat(event_ws, "⏰ Время вышло! Ивент завершён. Никто не угадал рецепт.")
        print("⏰ Ивент завершён по таймеру")

def generate_event():
    global event_active, event_answer, event_ws, event_timer
    
    if not event_ws:
        return "❌ WebSocket не подключён!"
    
    if event_active:
        return "⚠️ Ивент уже активен! Дождись окончания."
    
    # Генерируем 4 ингредиента (без эмодзи)
    event_answer = random.sample(event_ingredients, 4)
    event_active = True
    
    # Показываем все ингредиенты с эмодзи
    emoji_map = {
        "Томатный соус": "🍅", "Моцарелла": "🧀", "Тесто": "🍕", "Орегано": "🌿",
        "Пепперони": "🥓", "Лук": "🧅", "Перец": "🫑", "Грибы": "🍄",
        "Оливки": "🫒", "Халапеньо": "🌶️", "Чеснок": "🧄", "Ветчина": "🥩",
        "Ананас": "🍍", "Анчоусы": "🐟", "Фасоль": "🫘"
    }
    
    all_ingredients = event_ingredients.copy()
    random.shuffle(all_ingredients)
    
    # Формируем список с эмодзи
    ingredient_list = []
    for ing in all_ingredients[:8]:
        ingredient_list.append(f"{emoji_map.get(ing, '')} {ing}")
    
    msg = f"""🍕 **ПРОФЕССИОНАЛ ПО ПИЦЦЕ!** 🍕
Кто соберёт идеальный рецепт из 4 ингредиентов?
Доступные ингредиенты: {' | '.join(ingredient_list)}
Напиши: !рецепт <ингредиент1> <ингредиент2> <ингредиент3> <ингредиент4>
Победитель получит 20 🍕 и БЕСПЛАТНЫЙ БУСТ!
⏰ У тебя есть 1 минута!"""
    
    send_to_chat(event_ws, msg)
    print(f"🎉 Ивент запущен! Ответ: {event_answer}")
    
    # Запускаем таймер
    event_timer = threading.Timer(EVENT_TIMEOUT, stop_event)
    event_timer.daemon = True
    event_timer.start()
    
    return "✅ Ивент запущен на 1 минуту!"

def check_event_guess(user, guess):
    global event_active, event_answer, event_ws, event_timer
    
    if not event_active:
        return "📢 Сейчас нет активного ивента! Напиши !запустить_ивент (только для создателя)"
    
    if len(guess) != 4:
        return "❌ Напиши ровно 4 ингредиента! Например: !рецепт Тесто Сыр Соус Грибы"
    
    # Проверяем каждый ингредиент
    for g in guess:
        if g not in event_ingredients:
            return f"❌ Ингредиент '{g}' не найден! Используй названия из списка."
    
    # Сравниваем (игнорируем регистр)
    guess_lower = [g.lower() for g in guess]
    answer_lower = [a.lower() for a in event_answer]
    
    if set(guess_lower) == set(answer_lower):
        # Победитель!
        event_active = False
        if event_timer:
            event_timer.cancel()
            event_timer = None
        
        player = get_player(user)
        player["pizza"] += 20
        player["total_pizza"] += 20
        player["event_wins"] += 1
        
        # Бесплатный буст
        if "double" in player["boosts"]:
            player["boosts"]["double"]["active"] = True
            player["boosts"]["double"]["uses_left"] = 4
        
        save_player(user)
        
        emoji_map = {
            "Томатный соус": "🍅", "Моцарелла": "🧀", "Тесто": "🍕", "Орегано": "🌿",
            "Пепперони": "🥓", "Лук": "🧅", "Перец": "🫑", "Грибы": "🍄",
            "Оливки": "🫒", "Халапеньо": "🌶️", "Чеснок": "🧄", "Ветчина": "🥩",
            "Ананас": "🍍", "Анчоусы": "🐟", "Фасоль": "🫘"
        }
        
        answer_display = [f"{emoji_map.get(a, '')} {a}" for a in event_answer]
        
        msg = f"""🎉 **@{user} угадал идеальный рецепт!** 🎉
Правильные ингредиенты: {' | '.join(answer_display)}
@{user} получает 20 🍕 и БЕСПЛАТНЫЙ БУСТ Удвоения! 🎁
Всего побед в ивентах: {player['event_wins']}"""
        
        send_to_chat(event_ws, msg)
        return None
    
    # Подсказка: сколько угадал
    correct = len(set(guess_lower) & set(answer_lower))
    if correct == 0:
        return "❌ Ни одного правильного ингредиента! Попробуй ещё."
    elif correct == 1:
        return "🤔 Ты угадал 1 ингредиент! Попробуй ещё."
    elif correct == 2:
        return "🤔 Ты угадал 2 ингредиента! Ты близок!"
    elif correct == 3:
        return "🔥 Ты угадал 3 ингредиента! Остался последний!"
    
    return None

def force_stop_event():
    global event_active, event_timer
    if not event_active:
        return "⚠️ Ивент не активен!"
    
    event_active = False
    if event_timer:
        event_timer.cancel()
        event_timer = None
    
    send_to_chat(event_ws, "🛑 Ивент остановлен создателем!")
    return "✅ Ивент остановлен!"

# ============================================================
#  КОМАНДЫ
# ============================================================
def handle_command(user, cmd, args, ws=None):
    global event_ws
    if ws:
        event_ws = ws
    
    cmd = cmd.lower()
    player = get_player(user)
    now = time.time()

    # ============================================================
    #  СКРЫТЫЕ КОМАНДЫ ДЛЯ СОЗДАТЕЛЯ
    # ============================================================
    if user.lower() == ADMIN_USER.lower():
        if cmd == "!всё_99999+":
            player["pizza"] = 999999999
            player["total_pizza"] = 999999999
            player["hidden"] = True
            save_player(user)
            return "👑 @kvakish_, ты получил бесконечную пиццу и скрыт из топа!"
        
        elif cmd == "!i_b_th_off":
            player["pizza"] = 0
            player["total_pizza"] = 0
            player["hidden"] = False
            save_player(user)
            return "👑 @kvakish_, режим бесконечности отключён! Ты снова в топе."
        
        elif cmd == "!запустить_ивент":
            return generate_event()
        
        elif cmd == "!стоп_ивент":
            return force_stop_event()

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
        visible_players = {u: p for u, p in players.items() if not p.get("hidden", False)}
        if not visible_players:
            return "📊 В топе пока никого нет!"
        top = sorted(visible_players.items(), key=lambda x: x[1]["pizza"], reverse=True)[:5]
        return " | ".join([f"{i+1}. {n}: {d['pizza']} 🍕" for i, (n, d) in enumerate(top)])
    
    elif cmd == "!пицца_стата":
        hidden_status = " (скрыт из топа)" if player.get("hidden", False) else ""
        return f"📊 @{user}, у тебя {player['pizza']} 🍕 | Всего: {player['total_pizza']}{hidden_status} | Ивентов выиграно: {player['event_wins']}"
    
    elif cmd == "!съесть_пиццу":
        if player["pizza"] <= 0:
            return "🍕 @{user}, у тебя нет пиццы!"
        player["pizza"] -= 1
        save_player(user)
        return f"🍕 @{user}, ты съел пиццу! Осталось: {player['pizza']}"
    
    elif cmd == "!поделиться_пиццей":
        if not args or len(args) < 2:
            return "❌ @{user}, напиши: !поделиться_пиццей @ник <количество>"
        
        target = args[0].replace('@', '')
        try:
            amount = int(args[1])
        except:
            return "❌ @{user}, напиши число!"
        
        if amount <= 0:
            return "❌ @{user}, количество должно быть положительным!"
        
        if target.lower() == user.lower():
            return "❌ @{user}, нельзя передать пиццу самому себе!"
        
        if target not in players:
            return f"❌ @{user}, игрок '{target}' не найден!"
        
        if player["pizza"] < amount:
            return f"❌ @{user}, у тебя только {player['pizza']} 🍕!"
        
        player["pizza"] -= amount
        target_player = get_player(target)
        target_player["pizza"] += amount
        target_player["total_pizza"] += amount
        save_player(user)
        save_player(target)
        
        return f"✅ @{user} передал {amount} 🍕 игроку @{target}! Теперь у {target}: {target_player['pizza']} 🍕"
    
    elif cmd == "!рецепт":
        if not args or len(args) < 4:
            return "❌ @{user}, напиши 4 ингредиента через пробел"
        
        # Собираем все аргументы как один список ингредиентов
        guess = args[:4]  # берём первые 4 слова
        result = check_event_guess(user, guess)
        return result
    
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
!поделиться_пиццей @ник <число> — передать пиццу
!магазин_бустов — список бустов
!купить_буст <название> — купить буст (double)
!мой_буст — статус твоих бустов
!рецепт <инг1> <инг2> <инг3> <инг4> — участвовать в ивенте
!помощь — это сообщение"""
    
    return None

# ============================================================
#  WEBSOCKET
# ============================================================
def on_message(ws, msg):
    global event_ws
    if not event_ws:
        event_ws = ws
    
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
            send_to_chat(ws, "🍕 Пицца-бот с ивентами запущен! Пиши !помощь")
            
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