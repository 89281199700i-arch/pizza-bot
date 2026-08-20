import time
import websocket
import json
import random
import os
from flask import Flask, request, render_template_string, redirect, url_for, session
import threading

# ============================================================
#  НАСТРОЙКИ
# ============================================================
TWITCH_BOT_NICKNAME = "deepseekbot"
TWITCH_OAUTH_TOKEN = "oauth:0qe7od9qwu4vtzv0t5cl38h9tezroc"
TWITCH_CHANNEL = "#QumosX"

ADMIN_USER = "kvakish_"
ADMIN_CODE = "9760ef6e-8418-45c9-89d4-118745b9f413"      # ← ТВОЙ ПЕРВЫЙ КОД
SECRET_CODE = "чекушка"     # ← ТВОЙ ВТОРОЙ КОД

SAVE_FILE = "pizza_data.json"
COOLDOWN_TIME = 5

print("🚀 ЗАПУСК ПИЦЦА-БОТА С АДМИН-ПАНЕЛЬЮ")

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
        players[user] = {"pizza": 0, "total_pizza": 0, "wins": 0}
        save_data(players)
    return players[user]

def save_player(user):
    save_data(players)

# ============================================================
#  FLASK (АДМИН-ПАНЕЛЬ)
# ============================================================
app = Flask(__name__)
app.secret_key = "pizza_secret_key_12345"

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>🍕 Админ-панель пицца-бота</title>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial; background: #1a1a2e; color: #fff; padding: 20px; }
        .container { max-width: 800px; margin: 0 auto; }
        .card { background: #16213e; padding: 20px; border-radius: 10px; margin: 10px 0; }
        input, button { padding: 8px 12px; border-radius: 6px; border: none; margin: 4px; }
        button { background: #9146FF; color: #fff; cursor: pointer; }
        button:hover { background: #7a3bcc; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 8px; text-align: left; border-bottom: 1px solid #30363d; }
        th { color: #9146FF; }
        .danger { background: #da3633; }
        .danger:hover { background: #b12b29; }
        .success { background: #2ea043; }
        .success:hover { background: #238636; }
        .hidden { display: none; }
        .code-input { background: #0d1117; color: #fff; border: 1px solid #30363d; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🍕 Админ-панель</h1>
        
        <!-- Вход по кодам -->
        <div id="login" class="card">
            <h2>🔐 Вход</h2>
            <p>Введи оба кода для доступа</p>
            <input class="code-input" id="code1" placeholder="Admin Code" type="password">
            <input class="code-input" id="code2" placeholder="Secret Code" type="password">
            <button onclick="login()">🔓 Войти</button>
            <p id="loginError" style="color:#da3633;"></p>
        </div>

        <!-- Панель управления -->
        <div id="panel" class="hidden">
            <div class="card">
                <h2>📊 Статистика</h2>
                <table>
                    <tr><th>Игрок</th><th>🍕 Пицца</th><th>📦 Всего</th></tr>
                    {% for user, data in players.items() %}
                    <tr><td>{{ user }}</td><td>{{ data.pizza }}</td><td>{{ data.total_pizza }}</td></tr>
                    {% endfor %}
                </table>
            </div>

            <div class="card">
                <h2>🎮 Управление</h2>
                <div>
                    <input id="targetUser" placeholder="Игрок" class="code-input">
                    <input id="amount" placeholder="Количество" type="number" class="code-input">
                    <button onclick="addPizza()" class="success">➕ Добавить</button>
                    <button onclick="removePizza()" class="danger">➖ Удалить</button>
                </div>
                <div style="margin-top:10px;">
                    <button onclick="addAllPizza()" class="success">👥 Всем +1</button>
                    <button onclick="resetAll()" class="danger">🗑️ Сбросить всех</button>
                </div>
                <p id="adminResult"></p>
            </div>

            <div class="card">
                <h2>📋 Данные (JSON)</h2>
                <pre style="background:#0d1117;padding:10px;border-radius:6px;max-height:200px;overflow:auto;">{{ players_json }}</pre>
            </div>
        </div>
    </div>

    <script>
        function login() {
            const c1 = document.getElementById('code1').value;
            const c2 = document.getElementById('code2').value;
            fetch('/login', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({code1: c1, code2: c2})
            })
            .then(r => r.json())
            .then(data => {
                if (data.ok) {
                    document.getElementById('login').classList.add('hidden');
                    document.getElementById('panel').classList.remove('hidden');
                } else {
                    document.getElementById('loginError').textContent = '❌ Неверные коды!';
                }
            });
        }

        function addPizza() {
            const user = document.getElementById('targetUser').value;
            const amount = document.getElementById('amount').value;
            if (!user || !amount) return;
            fetch('/add', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({user, amount: parseInt(amount)})
            })
            .then(r => r.json())
            .then(data => {
                document.getElementById('adminResult').textContent = data.message;
                if (data.ok) setTimeout(() => location.reload(), 1000);
            });
        }

        function removePizza() {
            const user = document.getElementById('targetUser').value;
            const amount = document.getElementById('amount').value;
            if (!user || !amount) return;
            fetch('/remove', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({user, amount: parseInt(amount)})
            })
            .then(r => r.json())
            .then(data => {
                document.getElementById('adminResult').textContent = data.message;
                if (data.ok) setTimeout(() => location.reload(), 1000);
            });
        }

        function addAllPizza() {
            const amount = document.getElementById('amount').value || 1;
            fetch('/addall', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({amount: parseInt(amount)})
            })
            .then(r => r.json())
            .then(data => {
                document.getElementById('adminResult').textContent = data.message;
                if (data.ok) setTimeout(() => location.reload(), 1000);
            });
        }

        function resetAll() {
            if (!confirm('Удалить всех игроков?')) return;
            fetch('/reset', {method: 'POST'})
            .then(r => r.json())
            .then(data => {
                document.getElementById('adminResult').textContent = data.message;
                if (data.ok) setTimeout(() => location.reload(), 1000);
            });
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML, players=players, players_json=json.dumps(players, indent=2))

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    if data.get('code1') == ADMIN_CODE and data.get('code2') == SECRET_CODE:
        return {'ok': True}
    return {'ok': False}

@app.route('/add', methods=['POST'])
def add_pizza():
    data = request.json
    user = data.get('user')
    amount = data.get('amount', 1)
    if user in players:
        players[user]['pizza'] += amount
        players[user]['total_pizza'] += amount
        save_data(players)
        return {'ok': True, 'message': f'✅ Добавлено {amount} пиццы для {user}'}
    return {'ok': False, 'message': '❌ Игрок не найден'}

@app.route('/remove', methods=['POST'])
def remove_pizza():
    data = request.json
    user = data.get('user')
    amount = data.get('amount', 1)
    if user in players:
        if players[user]['pizza'] >= amount:
            players[user]['pizza'] -= amount
            save_data(players)
            return {'ok': True, 'message': f'✅ Удалено {amount} пиццы у {user}'}
        return {'ok': False, 'message': f'❌ У {user} только {players[user]["pizza"]} пиццы'}
    return {'ok': False, 'message': '❌ Игрок не найден'}

@app.route('/addall', methods=['POST'])
def add_all():
    data = request.json
    amount = data.get('amount', 1)
    for user in players:
        players[user]['pizza'] += amount
        players[user]['total_pizza'] += amount
    save_data(players)
    return {'ok': True, 'message': f'✅ Всем добавлено по {amount} пиццы'}

@app.route('/reset', methods=['POST'])
def reset_all():
    players.clear()
    save_data(players)
    return {'ok': True, 'message': '✅ Все данные сброшены'}

def start_web():
    app.run(host='0.0.0.0', port=5000)

# ============================================================
#  БОТ
# ============================================================
def handle_command(user, cmd, args):
    cmd = cmd.lower()
    player = get_player(user)
    now = time.time()

    if cmd == "!пицца":
        if user in cooldowns and now - cooldowns[user] < COOLDOWN_TIME:
            remaining = int(COOLDOWN_TIME - (now - cooldowns[user]))
            return f"⏳ @{user}, подожди {remaining} сек!"
        pizza = random.randint(1, 3)
        player["pizza"] += pizza
        player["total_pizza"] += pizza
        cooldowns[user] = now
        save_player(user)
        return f"🍕 @{user}, +{pizza} пиццы! Всего: {player['pizza']}"
    
    elif cmd == "!топпицца":
        if not players:
            return "📊 Пока никто не ел пиццу!"
        top = sorted(players.items(), key=lambda x: x[1]["pizza"], reverse=True)[:5]
        return " | ".join([f"{i+1}. {n}: {d['pizza']} 🍕" for i, (n, d) in enumerate(top)])
    
    elif cmd == "!помощь":
        return "📖 !пицца, !топпицца, !помощь"
    
    return None

def send_to_chat(ws, msg):
    if ws and ws.connected:
        ws.send(f"PRIVMSG {TWITCH_CHANNEL} :{msg}\r\n")
        print(f"📤 {msg}")

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
                print(f"⚠️ {e}")

def start_bot():
    print("🔄 Подключение к Twitch...")
    while True:
        try:
            ws = websocket.WebSocket()
            ws.connect("wss://irc-ws.chat.twitch.tv:443")
            ws.send(f"PASS {TWITCH_OAUTH_TOKEN}\r\n")
            ws.send(f"NICK {TWITCH_BOT_NICKNAME}\r\n")
            ws.send(f"JOIN {TWITCH_CHANNEL}\r\n")
            print("✅ Подключено!")
            send_to_chat(ws, "🍕 Пицца-бот запущен! Пиши !пицца")
            
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
    # Запускаем веб-сервер в фоновом потоке
    web_thread = threading.Thread(target=start_web, daemon=True)
    web_thread.start()
    print("🌐 Админ-панель: http://localhost:5000")
    start_bot()