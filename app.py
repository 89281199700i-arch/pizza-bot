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
DICT_FILE = "dictionary.json"
QUIZ_FILE = "quiz_data.json"
COOLDOWN_TIME = 5
EVENT_TIMEOUT = 60

print("🚀 ПИЦЦА-БОТ С ВИКТОРИНОЙ И ПЕРЕВОДЧИКОМ")

# ============================================================
#  СОЗДАНИЕ СЛОВАРЯ (30 000 слов)
# ============================================================
def generate_dictionary():
    base_words = [
        "привет", "пока", "как", "дела", "спасибо", "пицца", "ананас", "бот", "код",
        "игра", "победа", "поражение", "день", "ночь", "солнце", "луна", "звезда",
        "небо", "вода", "огонь", "земля", "ветер", "дождь", "снег", "лед", "гора",
        "река", "море", "океан", "лес", "поле", "город", "деревня", "дом", "квартира",
        "комната", "кухня", "ванна", "туалет", "коридор", "лестница", "лифт", "крыша",
        "стена", "пол", "потолок", "окно", "дверь", "стол", "стул", "кровать", "диван",
        "шкаф", "зеркало", "лампа", "свет", "тень", "цвет", "форма", "размер", "вес",
        "длина", "ширина", "высота", "глубина", "скорость", "время", "дата", "год",
        "месяц", "неделя", "час", "минута", "секунда", "мгновение", "вечность",
        "космос", "галактика", "планета", "спутник", "астероид", "комета", "метеорит",
        "черная_дыра", "туманность", "квазар", "пульсар", "нейтронная_звезда",
        "компьютер", "монитор", "клавиатура", "мышь", "процессор", "память", "диск",
        "файл", "папка", "программа", "скрипт", "сервер", "клиент", "сеть",
        "интернет", "сайт", "страница", "ссылка", "поиск", "браузер", "чат", "бот"
    ]
    
    prefixes = ["супер", "мега", "ультра", "гипер", "архи", "мульти", "поли", "анти", "контр"]
    suffixes = ["ный", "овой", "ельный", "истый", "астый", "чий", "ский", "овый", "евый"]
    
    dictionary = {}
    words_added = 0
    
    for word in base_words:
        translation = word
        ru_to_en = {
            'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'ye', 'ё': 'yo',
            'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
            'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
            'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch',
            'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
            ' ': '_'
        }
        for ru, en in ru_to_en.items():
            translation = translation.replace(ru, en)
        dictionary[word] = translation
        words_added += 1
    
    while words_added < 30000:
        base = random.choice(base_words)
        prefix = random.choice(prefixes) if random.random() > 0.5 else ""
        suffix = random.choice(suffixes) if random.random() > 0.5 else ""
        new_word = prefix + base + suffix
        
        if new_word not in dictionary and len(new_word) > 0:
            translation = new_word
            ru_to_en = {
                'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'ye', 'ё': 'yo',
                'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
                'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
                'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch',
                'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
                ' ': '_'
            }
            for ru, en in ru_to_en.items():
                translation = translation.replace(ru, en)
            dictionary[new_word] = translation
            words_added += 1
    
    return dictionary

def load_dictionary():
    if os.path.exists(DICT_FILE):
        try:
            with open(DICT_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                print(f"✅ Загружен словарь: {len(data)} слов")
                return data
        except:
            pass
    
    print("🔄 Генерация словаря на 30 000 слов... Это может занять 20-30 секунд...")
    dictionary = generate_dictionary()
    
    with open(DICT_FILE, "w", encoding="utf-8") as f:
        json.dump(dictionary, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Создан словарь: {len(dictionary)} слов")
    return dictionary

dictionary = load_dictionary()

# ============================================================
#  ЗАГРУЗКА ВОПРОСОВ ДЛЯ ВИКТОРИНЫ
# ============================================================
def load_quiz_questions():
    if os.path.exists(QUIZ_FILE):
        try:
            with open(QUIZ_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    
    demo_questions = {
        "Программирование": [
            {"question": "Что такое Python?", "answer": "Язык программирования"},
            {"question": "Что такое HTML?", "answer": "Язык разметки"},
            {"question": "Что такое CSS?", "answer": "Каскадные таблицы стилей"},
            {"question": "Что такое JavaScript?", "answer": "Язык программирования"},
            {"question": "Что такое SQL?", "answer": "Язык запросов"},
        ],
        "География": [
            {"question": "Столица Франции?", "answer": "Париж"},
            {"question": "Столица Германии?", "answer": "Берлин"},
            {"question": "Столица Италии?", "answer": "Рим"},
            {"question": "Столица Испании?", "answer": "Мадрид"},
            {"question": "Столица Китая?", "answer": "Пекин"},
        ],
        "История": [
            {"question": "Год начала Второй мировой войны?", "answer": "1939"},
            {"question": "Кто открыл Америку?", "answer": "Колумб"},
            {"question": "Год первого полёта человека в космос?", "answer": "1961"},
            {"question": "Кто написал 'Войну и мир'?", "answer": "Толстой"},
            {"question": "Год крещения Руси?", "answer": "988"},
        ],
        "Наука": [
            {"question": "Формула воды?", "answer": "H2O"},
            {"question": "Ближайшая звезда к Земле?", "answer": "Солнце"},
            {"question": "Сколько планет в Солнечной системе?", "answer": "8"},
            {"question": "Что изучает биология?", "answer": "Жизнь"},
            {"question": "Что изучает физика?", "answer": "Природу"},
        ],
        "Игры": [
            {"question": "Создатель Minecraft?", "answer": "Нотч"},
            {"question": "Главный герой Mario?", "answer": "Марио"},
            {"question": "Что такое RPG?", "answer": "Ролевая игра"},
            {"question": "Создатель GTA?", "answer": "Rockstar"},
            {"question": "Год выхода Fortnite?", "answer": "2017"},
        ],
        "Кино": [
            {"question": "Режиссёр 'Титаника'?", "answer": "Кэмерон"},
            {"question": "Кто играл Джокера?", "answer": "Хит Леджер"},
            {"question": "Год выхода 'Матрицы'?", "answer": "1999"},
            {"question": "Режиссёр 'Звёздных войн'?", "answer": "Лукас"},
            {"question": "Кто играл Терминатора?", "answer": "Шварценеггер"},
        ],
        "Музыка": [
            {"question": "Создатель 'Bohemian Rhapsody'?", "answer": "Queen"},
            {"question": "Кто такой Mozart?", "answer": "Композитор"},
            {"question": "Инструмент с 6 струнами?", "answer": "Гитара"},
            {"question": "Жанр: 'Hey Jude'", "answer": "Рок"},
            {"question": "Кто исполнил 'Thriller'?", "answer": "Майкл Джексон"},
        ],
        "Спорт": [
            {"question": "Количество игроков в футболе?", "answer": "11"},
            {"question": "Количество игроков в баскетболе?", "answer": "5"},
            {"question": "Год первой Олимпиады?", "answer": "1896"},
            {"question": "Самый быстрый бегун?", "answer": "Болт"},
            {"question": "Где проходила Олимпиада 2020?", "answer": "Токио"},
        ],
        "Литература": [
            {"question": "Автор 'Гарри Поттера'?", "answer": "Роулинг"},
            {"question": "Автор 'Властелина колец'?", "answer": "Толкин"},
            {"question": "Автор 'Преступления и наказания'?", "answer": "Достоевский"},
            {"question": "Автор 'Евгения Онегина'?", "answer": "Пушкин"},
            {"question": "Автор 'Героя нашего времени'?", "answer": "Лермонтов"},
        ],
        "Еда": [
            {"question": "Главный ингредиент пиццы?", "answer": "Тесто"},
            {"question": "Фрукт, который не любят на пицце?", "answer": "Ананас"},
            {"question": "Самый популярный сыр?", "answer": "Моцарелла"},
            {"question": "Из чего делают спагетти?", "answer": "Мука"},
            {"question": "Страна-родина пиццы?", "answer": "Италия"},
        ],
    }
    
    with open(QUIZ_FILE, "w", encoding="utf-8") as f:
        json.dump(demo_questions, f, indent=2, ensure_ascii=False)
    
    return demo_questions

quiz_questions_data = load_quiz_questions()

# ============================================================
#  ВИКТОРИНА
# ============================================================
QUIZ_CATEGORIES = 10
QUESTIONS_PER_CATEGORY = 5

quiz_active = False
quiz_categories = []
quiz_votes = {}
quiz_questions = []
quiz_current_question = 0
quiz_score = {}
quiz_timer = None
quiz_ws = None
quiz_phase = "idle"

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
#  ФУНКЦИИ ДЛЯ ВИКТОРИНЫ (ИСПРАВЛЕННЫЕ)
# ============================================================
def start_quiz_voting(ws):
    global quiz_active, quiz_categories, quiz_votes, quiz_phase, quiz_ws, quiz_timer
    
    if quiz_active:
        return "⚠️ Викторина уже активна! Дождись окончания."
    
    all_categories = list(quiz_questions_data.keys())
    if len(all_categories) < 2:
        return "❌ Недостаточно категорий для викторины! Добавь вопросы."
    
    quiz_categories = random.sample(all_categories, min(QUIZ_CATEGORIES, len(all_categories)))
    quiz_votes = {cat: 0 for cat in quiz_categories}
    quiz_phase = "voting"
    quiz_active = True
    quiz_ws = ws
    
    categories_msg = " | ".join([f"{i+1}. {cat}" for i, cat in enumerate(quiz_categories)])
    
    msg = f"""🎯 **ВИКТОРИНА СКОРО НАЧНЁТСЯ!** 🎯
Победитель получит +20 🍕!

📚 Категории на выбор:
{categories_msg}

🗳️ Голосуй: !голос <номер> (1-{len(quiz_categories)})
⏰ У тебя есть 30 секунд!"""
    
    send_to_chat(ws, msg)
    
    quiz_timer = threading.Timer(30, finish_voting)
    quiz_timer.daemon = True
    quiz_timer.start()
    
    return None

def finish_voting():
    global quiz_categories, quiz_votes, quiz_phase, quiz_active, quiz_timer, quiz_ws
    global quiz_questions, quiz_current_question, quiz_score
    
    if quiz_phase != "voting":
        return
    
    max_votes = max(quiz_votes.values())
    winning_categories = [cat for cat, votes in quiz_votes.items() if votes == max_votes]
    
    if max_votes == 0 or len(winning_categories) > 1:
        chosen_category = random.choice(quiz_categories)
        send_to_chat(quiz_ws, f"🤔 Ничья в голосовании! Выбрана случайная категория: **{chosen_category}**")
    else:
        chosen_category = winning_categories[0]
        send_to_chat(quiz_ws, f"✅ Победила категория: **{chosen_category}!** 🎉")
    
    all_questions = quiz_questions_data.get(chosen_category, [])
    
    if len(all_questions) < QUESTIONS_PER_CATEGORY:
        for cat in quiz_categories:
            if cat != chosen_category:
                all_questions.extend(quiz_questions_data.get(cat, []))
            if len(all_questions) >= QUESTIONS_PER_CATEGORY:
                break
    
    quiz_questions = random.sample(all_questions, min(QUESTIONS_PER_CATEGORY, len(all_questions)))
    quiz_current_question = 0
    quiz_score = {}
    quiz_phase = "questions"
    
    send_to_chat(quiz_ws, f"🎯 **ВИКТОРИНА НАЧИНАЕТСЯ!** 📚\nКатегория: {chosen_category}\nВсего вопросов: {len(quiz_questions)}\n\nПервый вопрос:")
    
    if quiz_timer:
        quiz_timer.cancel()
        quiz_timer = None
    
    ask_next_question()

def ask_next_question():
    global quiz_current_question, quiz_questions, quiz_phase, quiz_ws, quiz_timer
    
    if quiz_current_question >= len(quiz_questions):
        finish_quiz()
        return
    
    question_data = quiz_questions[quiz_current_question]
    question_num = quiz_current_question + 1
    total = len(quiz_questions)
    
    msg = f"📝 **Вопрос {question_num}/{total}:**\n{question_data['question']}\n\n✍️ Пиши ответ в чат! У тебя 15 секунд."
    send_to_chat(quiz_ws, msg)
    
    quiz_timer = threading.Timer(15, next_question_timeout)
    quiz_timer.daemon = True
    quiz_timer.start()

def next_question_timeout():
    global quiz_current_question, quiz_ws, quiz_timer
    
    quiz_current_question += 1
    send_to_chat(quiz_ws, "⏰ Время вышло! Следующий вопрос...")
    
    if quiz_timer:
        quiz_timer.cancel()
        quiz_timer = None
    
    ask_next_question()

def check_quiz_answer(user, answer):
    global quiz_current_question, quiz_questions, quiz_phase, quiz_score, quiz_timer, quiz_ws
    
    if quiz_phase != "questions":
        return None
    
    if quiz_current_question >= len(quiz_questions):
        return None
    
    question_data = quiz_questions[quiz_current_question]
    correct_answer = question_data['answer'].lower()
    user_answer = answer.lower()
    
    if user_answer == correct_answer or user_answer in correct_answer.split():
        if user not in quiz_score:
            quiz_score[user] = 0
        quiz_score[user] += 1
        
        send_to_chat(quiz_ws, f"✅ @{user} ответил правильно! +1 балл! 🎉")
        
        if quiz_timer:
            quiz_timer.cancel()
            quiz_timer = None
        
        quiz_current_question += 1
        ask_next_question()
        return None
    else:
        return f"❌ @{user}, неправильно! Попробуй ещё..."

def finish_quiz():
    global quiz_active, quiz_phase, quiz_ws, quiz_score, quiz_timer
    
    quiz_phase = "ended"
    quiz_active = False
    
    if quiz_timer:
        quiz_timer.cancel()
        quiz_timer = None
    
    if not quiz_score:
        send_to_chat(quiz_ws, "😔 Никто не ответил ни на один вопрос! Викторина завершена.")
        return
    
    winner = max(quiz_score, key=quiz_score.get)
    max_score = quiz_score[winner]
    
    winners = [user for user, score in quiz_score.items() if score == max_score]
    
    if len(winners) > 1:
        winner = random.choice(winners)
        send_to_chat(quiz_ws, f"🤝 Ничья! Победитель выбран случайно: @{winner}!")
    
    player = get_player(winner)
    player["pizza"] += 20
    player["total_pizza"] += 20
    save_player(winner)
    
    scoreboard = " | ".join([f"@{u}: {s}" for u, s in sorted(quiz_score.items(), key=lambda x: x[1], reverse=True)])
    send_to_chat(quiz_ws, f"""🏆 **ВИКТОРИНА ЗАВЕРШЕНА!** 🏆
Победитель: @{winner} с {max_score} баллами!
@{winner} получает 20 🍕! 🎉

📊 Результаты:
{scoreboard}""")

def stop_quiz(ws):
    global quiz_active, quiz_phase, quiz_timer, quiz_ws
    
    if not quiz_active:
        return "⚠️ Викторина не активна!"
    
    quiz_active = False
    quiz_phase = "ended"
    
    if quiz_timer:
        quiz_timer.cancel()
        quiz_timer = None
    
    send_to_chat(ws, "🛑 Викторина остановлена создателем!")
    return "✅ Викторина остановлена!"

# ============================================================
#  ПЕРЕВОДЧИК (ОФЛАЙН)
# ============================================================
def translate_offline(text):
    words = text.lower().split()
    translated = []
    
    for word in words:
        clean_word = word.strip('.,!?;:()[]{}')
        if clean_word in dictionary:
            translated.append(dictionary[clean_word])
        else:
            found = False
            for key in dictionary:
                if key in clean_word:
                    translated.append(dictionary[key])
                    found = True
                    break
            if not found:
                translated.append(word)
    
    return ' '.join(translated)

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
        
        elif cmd == "!обнулить_всех":
            for name in list(players.keys()):
                players[name]["pizza"] = 0
                players[name]["total_pizza"] = 0
            save_data(players)
            return "👑 @kvakish_, у ВСЕХ игроков пицца обнулена до 0! 🍕"
        
        elif cmd == "!s_r_on":
            result = start_quiz_voting(ws)
            if result:
                return result
            return None
        
        elif cmd == "!s_r_off":
            return stop_quiz(ws)

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
    
    elif cmd == "!ананас":
        target = args[0].replace('@', '') if args else user
        
        if args and target not in players:
            return f"❌ @{user}, игрок '{target}' не найден! Пиши: !ананас @ник"
        
        reactions = [
            f"🍍 @{user} положил АНАНАС на пиццу @{target}! Это преступление против кулинарии! 😱",
            f"🍍 @{target}, твоя пицца теперь с АНАНАСОМ! @{user}, ты чудовище! 👹",
            f"🍍 @{user} добавил ананас на пиццу @{target}! Итальянцы в шоке! 🇮🇹💀",
            f"🍍 @{target}, твоя пицца испорчена ананасом! @{user}, зачем ты это сделал? 😭",
            f"🍍 @{user} совершил ВОЙНУ с пиццей @{target}! Ананас на пицце — это грех! ⚠️",
            f"🍍 @{target} теперь ест пиццу с ананасом... @{user}, ты разрушил ему день! 💀",
            f"🍍 @{user} запихнул ананас в пиццу @{target}! Вкусовые рецепторы в панике! 🤯",
            f"🍍 @{user} нанёс урон пицце @{target} ананасом! -100 к репутации! 📉",
        ]
        
        return random.choice(reactions)
    
    elif cmd == "!fasttrans":
        if not args:
            return f"❌ @{user}, напиши: !fasttrans <текст для перевода>"
        
        text = ' '.join(args)
        translated = translate_offline(text)
        
        return f"🗣️ @{user}, перевод: \"{translated}\""
    
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
🍍 !ананас @ник — испортить пиццу ананасом
🗣️ !fasttrans <текст> — перевод на пиццерийский (офлайн, 30к слов)
🎯 !s_r_on — запустить викторину (только создатель)
⛔ !s_r_off — остановить викторину (только создатель)
🗳️ !голос <номер> — проголосовать за категорию в викторине
📝 <ответ> — ответить на вопрос викторины
❓ !помощь — это сообщение

👑 Команды создателя:
!запустить_ивент
!стоп_ивент
!обнулить_всех
!всё_99999+
!i_b_th_off
!s_r_on
!s_r_off"""
    
    return None

# ============================================================
#  WEBSOCKET
# ============================================================
def on_message(ws, msg):
    global event_ws, quiz_phase, quiz_categories, quiz_votes
    
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
                
                # Проверяем команду голосования
                if text.startswith('!голос'):
                    args = text.split()
                    if len(args) > 1:
                        try:
                            vote_num = int(args[1]) - 1
                            if quiz_phase == "voting" and 0 <= vote_num < len(quiz_categories):
                                chosen_cat = quiz_categories[vote_num]
                                quiz_votes[chosen_cat] = quiz_votes.get(chosen_cat, 0) + 1
                                send_to_chat(ws, f"🗳️ @{user}, твой голос за категорию '{chosen_cat}' учтён!")
                            else:
                                send_to_chat(ws, f"❌ @{user}, голосование не активно или неверный номер!")
                        except:
                            send_to_chat(ws, f"❌ @{user}, напиши: !голос <номер>")
                    continue
                
                # Обычные команды
                if text.startswith('!'):
                    args = text.split()
                    cmd = args[0]
                    resp = handle_command(user, cmd, args[1:], ws)
                    if resp:
                        send_to_chat(ws, resp)
                else:
                    # Если сообщение без команды — проверяем ответ на викторину
                    if quiz_active and quiz_phase == "questions":
                        if user.lower() != TWITCH_BOT_NICKNAME.lower():
                            result = check_quiz_answer(user, text)
                            if result:
                                send_to_chat(ws, result)
                                
            except Exception as e:
                print(f"⚠️ Ошибка: {e}")

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
            send_to_chat(ws, "🍕 Пицца-бот с викториной и переводчиком запущен! Пиши !помощь")
            
            while True:
                try:
                    msg = ws.recv()
                    if msg:
                        on_message(ws, msg)
                except websocket.WebSocketConnectionClosedException:
                    print("❌ Разрыв, переподключение...")
                    break
                except Exception as e:
                    print(f"⚠️ Ошибка: {e}")
                    break
        except Exception as e:
            print(f"❌ Ошибка: {e}")
        time.sleep(5)

if __name__ == "__main__":
    start_bot()