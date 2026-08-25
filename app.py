import time
import websocket
import json
import random
import os
import threading

# ============================================================
#  НАСТРОЙКИ
#т ============================================================
TWITCH_BOT_NICKNAME = "deepseekbot"
TWITCH_OAUTH_TOKEN = "oauth:0qe7od9qwu4vtzv0t5cl38h9tezroc"
TWITCH_CHANNEL = "#QumosX"

ADMIN_USER = "kvakish_"

SAVE_FILE = "pizza_data.json"
COOLDOWN_TIME = 5
EVENT_TIMEOUT = 60

print("🚀 ПИЦЦА-БОТ С АВТООТВЕТАМИ")

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
#  БАНЫ
# ============================================================
banned_users = set()
commands_locked = False

# ============================================================
#  ДУЭЛИ
# ============================================================
duels = {}

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
            "duel_wins": 0,
            "duel_losses": 0,
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
#  ИВЕНТ
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
    
    event_answer = random.sample(event_ingredients, 4)
    event_active = True
    
    emoji_map = {
        "Томатный соус": "🍅", "Моцарелла": "🧀", "Тесто": "🍕", "Орегано": "🌿",
        "Пепперони": "🥓", "Лук": "🧅", "Перец": "🫑", "Грибы": "🍄",
        "Оливки": "🫒", "Халапеньо": "🌶️", "Чеснок": "🧄", "Ветчина": "🥩",
        "Ананас": "🍍", "Анчоусы": "🐟", "Фасоль": "🫘"
    }
    
    all_ingredients = event_ingredients.copy()
    random.shuffle(all_ingredients)
    
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
    
    for g in guess:
        if g not in event_ingredients:
            return f"❌ Ингредиент '{g}' не найден! Используй названия из списка."
    
    guess_lower = [g.lower() for g in guess]
    answer_lower = [a.lower() for a in event_answer]
    
    if set(guess_lower) == set(answer_lower):
        event_active = False
        if event_timer:
            event_timer.cancel()
            event_timer = None
        
        player = get_player(user)
        player["pizza"] += 20
        player["total_pizza"] += 20
        player["event_wins"] += 1
        
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
#  ДУЭЛЬ
# ============================================================
def start_duel(challenger, target, ws):
    if challenger == target:
        return "❌ @{challenger}, нельзя вызвать на дуэль самого себя!"
    
    if target not in players:
        return f"❌ @{challenger}, игрок '{target}' не найден!"
    
    if get_player(challenger)["pizza"] < 1:
        return f"❌ @{challenger}, у тебя нет пиццы для дуэли!"
    
    if challenger in duels:
        return f"❌ @{challenger}, у тебя уже есть активный вызов на дуэль!"
    
    duels[challenger] = {"target": target, "status": "waiting"}
    
    msg = f"⚔️ @{challenger} вызывает @{target} на ДУЭЛЬ! 🍕\nУ кого выпадет больше пиццы за 1 минуту — тот забирает всё!\n@{target}, напиши !принять_дуэль или !отказаться_дуэль"
    send_to_chat(ws, msg)
    
    def duel_timeout():
        if challenger in duels and duels[challenger]["status"] == "waiting":
            del duels[challenger]
            send_to_chat(ws, f"⏰ @{challenger}, время на принятие дуэли вышло!")
    
    timer = threading.Timer(30, duel_timeout)
    timer.daemon = True
    timer.start()
    
    return None

def accept_duel(user, ws):
    challenger = None
    for c, data in duels.items():
        if data["target"] == user and data["status"] == "waiting":
            challenger = c
            break
    
    if not challenger:
        return f"❌ @{user}, у тебя нет активных вызовов на дуэль!"
    
    duels[challenger]["status"] = "active"
    duels[challenger]["start_time"] = time.time()
    duels[challenger]["attempts"] = {challenger: 0, user: 0}
    duels[challenger]["pizza_got"] = {challenger: 0, user: 0}
    
    msg = f"⚔️ ДУЭЛЬ НАЧАЛАСЬ! @{challenger} VS @{user}!\nУ каждого по 5 попыток !пицца. У кого больше — тот забирает всё! 🍕"
    send_to_chat(ws, msg)
    return None

def decline_duel(user, ws):
    challenger = None
    for c, data in duels.items():
        if data["target"] == user and data["status"] == "waiting":
            challenger = c
            break
    
    if not challenger:
        return f"❌ @{user}, у тебя нет активных вызовов на дуэль!"
    
    del duels[challenger]
    send_to_chat(ws, f"❌ @{user} отказался от дуэли с @{challenger}!")
    return None

def duel_pizza(user, ws):
    active_duel = None
    for c, data in duels.items():
        if data["status"] == "active":
            if c == user or data["target"] == user:
                active_duel = (c, data)
                break
    
    if not active_duel:
        return None
    
    challenger, data = active_duel
    target = data["target"]
    
    if data["attempts"][user] >= 5:
        return f"⏳ @{user}, у тебя закончились попытки в дуэли!"
    
    pizza = random.randint(1, 6)
    data["pizza_got"][user] += pizza
    data["attempts"][user] += 1
    
    msg = f"🍕 @{user} получает {pizza} пиццы в дуэли! (Попытка {data['attempts'][user]}/5)"
    send_to_chat(ws, msg)
    
    if data["attempts"][challenger] >= 5 and data["attempts"][target] >= 5:
        c_pizza = data["pizza_got"][challenger]
        t_pizza = data["pizza_got"][target]
        
        if c_pizza > t_pizza:
            winner = challenger
            loser = target
            win_amount = c_pizza + t_pizza
        elif t_pizza > c_pizza:
            winner = target
            loser = challenger
            win_amount = c_pizza + t_pizza
        else:
            send_to_chat(ws, f"🤝 ДУЭЛЬ ЗАВЕРШЕНА! Ничья! Оба игрока получают по 5 🍕")
            winner_player = get_player(challenger)
            winner_player["pizza"] += 5
            winner_player["total_pizza"] += 5
            save_player(challenger)
            
            loser_player = get_player(target)
            loser_player["pizza"] += 5
            loser_player["total_pizza"] += 5
            save_player(target)
            
            del duels[challenger]
            return None
        
        winner_player = get_player(winner)
        winner_player["pizza"] += win_amount
        winner_player["total_pizza"] += win_amount
        winner_player["duel_wins"] += 1
        save_player(winner)
        
        loser_player = get_player(loser)
        loser_player["pizza"] = 0
        loser_player["duel_losses"] += 1
        save_player(loser)
        
        msg = f"""⚔️ **ДУЭЛЬ ЗАВЕРШЕНА!** ⚔️
🏆 @{winner} ПОБЕДИЛ! @{loser} проиграл!
@{winner} забирает {win_amount} 🍕!
Теперь у {winner}: {winner_player['pizza']} 🍕
У {loser}: 0 🍕"""
        
        send_to_chat(ws, msg)
        del duels[challenger]
    
    return None

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
    #  ПРОВЕРКА БАНА И БЛОКИРОВКИ (С АВТООТВЕТАМИ!)
    # ============================================================
    # Пропускаем проверку для создателя
    if user != ADMIN_USER:
        # Проверка на бан
        if user in banned_users:
            return "🚫 Вы заблокированы для этого бота! Обратитесь к создателю."
        
        # Проверка на глобальную блокировку
        if commands_locked:
            return "⛔ Бот временно недоступен! Команды заблокированы создателем."

    # ============================================================
    #  СКРЫТЫЕ КОМАНДЫ ДЛЯ СОЗДАТЕЛЯ
    # ============================================================
    if user.lower() == ADMIN_USER.lower():
        # ---- БАНЫ ----
        if cmd == "!бан":
            if not args:
                return "❌ @{user}, напиши: !бан @ник"
            target = args[0].replace('@', '')
            banned_users.add(target)
            save_data({"banned": list(banned_users), "locked": commands_locked})
            return f"🚫 @{user} забанил @{target}! Теперь он не может использовать команды."
        
        elif cmd == "!разбан":
            if not args:
                return "❌ @{user}, напиши: !разбан @ник"
            target = args[0].replace('@', '')
            if target in banned_users:
                banned_users.remove(target)
                save_data({"banned": list(banned_users), "locked": commands_locked})
                return f"✅ @{user} разбанил @{target}!"
            else:
                return f"❌ @{user}, игрок '{target}' не забанен."
        
        elif cmd == "!банлист":
            if not banned_users:
                return "📊 Список забаненных пуст."
            return f"🚫 Забаненные: {', '.join(banned_users)}"
        
        # ---- БЛОКИРОВКА КОМАНД ----
        elif cmd == "!заблокировать_команды":
            global commands_locked
            commands_locked = True
            save_data({"banned": list(banned_users), "locked": commands_locked})
            return "⛔ ВСЕ КОМАНДЫ ЗАБЛОКИРОВАНЫ! Только создатель может их использовать."
        
        elif cmd == "!разблокировать_команды":
            global commands_locked
            commands_locked = False
            save_data({"banned": list(banned_users), "locked": commands_locked})
            return "✅ Команды разблокированы для всех!"
        
        # ---- ОСТАЛЬНЫЕ АДМИН-КОМАНДЫ ----
        elif cmd == "!всё_99999+":
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
        
        elif cmd == "!обнулить_всех":
            for name in list(players.keys()):
                players[name]["pizza"] = 0
                players[name]["total_pizza"] = 0
            save_data(players)
            return "👑 @kvakish_, у ВСЕХ игроков пицца обнулена до 0! 🍕"

    # ============================================================
    #  ДУЭЛИ
    # ============================================================
    if cmd == "!дуэль":
        if not args:
            return "❌ @{user}, напиши: !дуэль @ник"
        target = args[0].replace('@', '')
        return start_duel(user, target, ws)
    
    elif cmd == "!принять_дуэль":
        return accept_duel(user, ws)
    
    elif cmd == "!отказаться_дуэль":
        return decline_duel(user, ws)

    # ============================================================
    #  ОБЫЧНЫЕ КОМАНДЫ
    # ============================================================
    if cmd == "!пицца":
        for c, data in duels.items():
            if data["status"] == "active":
                if c == user or data["target"] == user:
                    result = duel_pizza(user, ws)
                    if result:
                        return result
                    return None
        
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
        return f"📊 @{user}, у тебя {player['pizza']} 🍕 | Всего: {player['total_pizza']}{hidden_status} | Ивентов выиграно: {player['event_wins']} | Дуэлей: побед {player['duel_wins']} / поражений {player['duel_losses']}"
    
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
    
    elif cmd == "!шанс":
        if not args:
            return f"❌ @{user}, напиши: !шанс <текст вопроса>"
        
        question = ' '.join(args)
        chance = random.randint(0, 100)
        
        return f"🎲 @{user}, думаю, вероятность того, что {question} — {chance}%!"
    
    elif cmd == "!рецепт":
        if not args or len(args) < 4:
            return "❌ @{user}, напиши 4 ингредиента через пробел"
        guess = args[:4]
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
🍕 !пицца — получить пиццу
🏆 !топ_пицца — топ игроков
📊 !пицца_стата — твоя статистика
🍽️ !съесть_пиццу — съесть 1 пиццу
🤝 !поделиться_пиццей @ник <число> — передать пиццу
🛒 !магазин_бустов — список бустов
💰 !купить_буст <название> — купить буст
🎯 !мой_буст — статус твоих бустов
⚔️ !дуэль @ник — вызвать на дуэль
✅ !принять_дуэль — принять дуэль
❌ !отказаться_дуэль — отказаться от дуэли
🎲 !шанс <текст> — случайный процент
🍕 !рецепт <инг1> <инг2> <инг3> <инг4> — участвовать в ивенте
❓ !помощь — это сообщение

👑 Команды создателя:
!бан @ник — забанить игрока
!разбан @ник — разбанить игрока
!банлист — список забаненных
!заблокировать_команды — заблокировать все команды
!разблокировать_команды — разблокировать все команды
!запустить_ивент
!стоп_ивент
!обнулить_всех
!всё_99999+
!i_b_th_off"""
    
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
            send_to_chat(ws, "🍕 Пицца-бот с автоответами запущен! Пиши !помощь")
            
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
    # Загружаем состояние банов
    try:
        data = load_data()
        if "banned" in data:
            global banned_users
            banned_users = set(data["banned"])
        if "locked" in data:
            global commands_locked
            commands_locked = data["locked"]
    except:
        pass
    
    start_bot()