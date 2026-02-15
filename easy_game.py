import os
from flask import Flask, render_template_string, request
from flask_socketio import SocketIO, emit
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", "dev_key_for_testing")
socketio = SocketIO(app, cors_allowed_origins="*")

# --- GAME CONFIG ---
WORDS = ["apple", "sun", "house", "tree", "smile", "rocket", "cat", "dog", "fish", "star", "pizza", "ball", "bird", "car"]

# --- GAME STATE ---
players = {}       
turn_order = []    
current_drawer = None  
current_word = ""

# --- THE FRONTEND ---
html_code = """
<!DOCTYPE html>
<html>
<head>
    <title>Draw & Guess - Safe Mode</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <style>
        /* 1. Global Reset: Allow scrolling! */
        body { 
            font-family: 'Segoe UI', sans-serif; 
            background: #eef2f3; 
            margin: 0; 
            padding: 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        
        /* 2. Header with the Reset Button */
        #header {
            width: 100%;
            max-width: 1100px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            background: #fff;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }

        h1 { margin: 0; font-size: 24px; color: #2c3e50; }

        .btn-reset {
            background: #c0392b;
            color: white;
            border: none;
            padding: 10px 20px;
            font-weight: bold;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
        }
        .btn-reset:hover { background: #e74c3c; }

        /* 3. Main Game Container (Wraps on small screens) */
        #game-container { 
            display: flex; 
            flex-wrap: wrap; /* CRITICAL: Allows items to stack if screen is small */
            gap: 20px; 
            width: 100%; 
            max-width: 1100px; 
            justify-content: center;
        }
        
        /* 4. Left Panel (Canvas) */
        #left-panel { flex: 1; min-width: 300px; max-width: 800px; }
        
        #canvas-wrapper { 
            position: relative; 
            border-radius: 8px; 
            overflow: hidden; 
            box-shadow: 0 4px 10px rgba(0,0,0,0.1); 
            border: 4px solid #34495e; 
            background: white; 
        }
        canvas { display: block; width: 100%; height: auto; cursor: crosshair; }
        
        #overlay { 
            position: absolute; top: 0; left: 0; width: 100%; height: 100%; 
            background: rgba(255,255,255,0.95); display: flex; 
            flex-direction: column; align-items: center; justify-content: center;
            font-size: 24px; font-weight: bold; color: #2c3e50;
            pointer-events: none; z-index: 10; text-align: center; padding: 20px;
        }

        #controls { margin-top: 10px; text-align: right; }
        .btn-clear { background: #f39c12; color: white; border: none; padding: 8px 15px; border-radius: 5px; cursor: pointer; font-weight: bold; }

        /* 5. Right Panel (Scoreboard + Chat) */
        #right-panel { 
            flex: 0 0 300px; /* Fixed width of 300px */
            display: flex; 
            flex-direction: column; 
            gap: 15px; 
        }
        
        #scoreboard { 
            background: #2c3e50; 
            color: white; 
            border-radius: 8px; 
            padding: 15px; 
            min-height: 150px; /* Ensure it has height */
            max-height: 200px;
            overflow-y: auto;
            border: 2px solid #1a252f;
        }
        
        .player-row { display: flex; justify-content: space-between; padding: 5px 0; border-bottom: 1px solid rgba(255,255,255,0.1); }
        .myself { color: #f1c40f; font-weight: bold; }

        #game-info { background: white; padding: 15px; border-radius: 8px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
        #word-display { font-size: 24px; font-weight: 900; color: #2c3e50; margin-top: 5px; }

        #chat-box { 
            background: white; 
            border-radius: 8px; 
            height: 300px; 
            display: flex; 
            flex-direction: column; 
            box-shadow: 0 2px 5px rgba(0,0,0,0.05); 
        }
        #messages { flex-grow: 1; overflow-y: auto; list-style: none; padding: 10px; margin: 0; background: #f8f9fa; }
        #messages li { padding: 4px 0; border-bottom: 1px solid #eee; font-size: 14px; }
        #input-area { display: flex; padding: 10px; border-top: 1px solid #eee; }
        #input-area input { flex-grow: 1; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
        #input-area button { margin-left: 5px; background: #3498db; color: white; border: none; padding: 0 15px; border-radius: 4px; cursor: pointer; }

        .win { color: #27ae60; font-weight: bold; background: #d5f5e3; padding: 5px; border-radius: 4px; text-align: center; }
        .drawer-msg { color: #d35400; font-weight: bold; }
    </style>
</head>
<body>

    <div id="header">
        <h1>🎨 Draw & Guess</h1>
        <button class="btn-reset" onclick="resetGame()">⚠️ RESET GAME (KICK ALL)</button>
    </div>

    <div id="game-container">
        
        <div id="left-panel">
            <div id="canvas-wrapper">
                <canvas id="canvas" width="800" height="600"></canvas>
                <div id="overlay">
                    <div id="overlay-text">Waiting for players...</div>
                    <div style="font-size: 16px; margin-top: 10px; font-weight: normal;" id="overlay-sub">Need at least 2 people</div>
                </div>
            </div>
            <div id="controls">
                <button class="btn-clear" onclick="clearCanvas()">🗑 Clear Canvas</button>
            </div>
        </div>

        <div id="right-panel">
            <div id="scoreboard">
                <h3 style="margin: 0 0 10px 0; border-bottom: 1px solid #999; padding-bottom:5px;">🏆 Leaderboard</h3>
                <div id="score-list"></div>
            </div>

            <div id="game-info">
                <div id="role-display">Waiting...</div>
                <div id="word-display">???</div>
            </div>

            <div id="chat-box">
                <ul id="messages"></ul>
                <div id="input-area">
                    <input type="text" id="msgInput" placeholder="Guess here..." autocomplete="off">
                    <button onclick="sendMessage()">Send</button>
                </div>
            </div>
        </div>
    </div>

    <script>
        var socket = io();
        var username = "";
        
        while(!username) {
            username = prompt("Enter your name (Required):");
        }

        var canvas = document.getElementById('canvas');
        var ctx = canvas.getContext('2d');
        var overlay = document.getElementById('overlay');
        var overlayText = document.getElementById('overlay-text');
        var overlaySub = document.getElementById('overlay-sub');
        var isMyTurn = false;
        var isDrawing = false;

        socket.on('connect', function() {
            socket.emit('join_game', {username: username});
        });

        socket.on('force_reload', function() {
            window.location.reload();
        });

        function resetGame() {
            if(confirm("Kick everyone and restart?")) {
                socket.emit('reset_game');
            }
        }

        socket.on('update_scores', function(data) {
            var list = document.getElementById('score-list');
            list.innerHTML = "";
            data.players.sort((a, b) => b.score - a.score);
            data.players.forEach(p => {
                var row = document.createElement('div');
                row.className = 'player-row';
                var nameDisplay = (p.name === username) ? `<span class="myself">${p.name} (You)</span>` : p.name;
                row.innerHTML = `<span>${nameDisplay}</span> <span>${p.score}</span>`;
                list.appendChild(row);
            });
        });

        socket.on('game_waiting', function(data) {
            overlay.style.display = 'flex';
            overlay.style.pointerEvents = 'auto'; 
            overlayText.innerText = "Waiting for players...";
            overlaySub.innerText = "Need at least 2 people.";
            document.getElementById('word-display').innerText = "???";
            isMyTurn = false;
        });

        socket.on('new_round', function(data) {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            if (data.drawer === socket.id) {
                isMyTurn = true;
                overlay.style.display = 'none';
                overlay.style.pointerEvents = 'none';
                document.getElementById('role-display').innerText = "IT'S YOUR TURN!";
                document.getElementById('role-display').style.color = "#27ae60";
                document.getElementById('word-display').innerText = data.word;
                addMessage("It's your turn! Draw: " + data.word, "drawer-msg");
            } else {
                isMyTurn = false;
                overlay.style.display = 'flex';
                overlay.style.pointerEvents = 'auto'; 
                overlay.style.background = 'rgba(0,0,0,0.05)';
                overlayText.innerText = "";
                overlaySub.innerText = "";
                document.getElementById('role-display').innerText = data.drawer_name + " IS DRAWING";
                document.getElementById('role-display').style.color = "#c0392b";
                document.getElementById('word-display').innerText = data.word.replace(/[a-zA-Z]/g, "_ ");
            }
        });

        socket.on('game_won', function(data) { addMessage(data.msg, 'win'); });
        socket.on('draw_event', function(data) { drawCircle(data.x, data.y, data.color); });
        socket.on('clear_board', function() { ctx.clearRect(0, 0, canvas.width, canvas.height); });
        socket.on('chat_message', function(data) { addMessage(data.user + ": " + data.msg); });
        socket.on('system_message', function(data) { addMessage(data.msg, 'system'); });

        function drawCircle(x, y, color) {
            ctx.fillStyle = color;
            ctx.beginPath();
            ctx.arc(x, y, 5, 0, Math.PI * 2);
            ctx.fill();
        }

        function getMousePos(evt) {
            var rect = canvas.getBoundingClientRect();
            return {
                x: (evt.clientX - rect.left) * (canvas.width / rect.width),
                y: (evt.clientY - rect.top) * (canvas.height / rect.height)
            };
        }

        canvas.addEventListener('mousedown', () => { if(isMyTurn) isDrawing = true; });
        canvas.addEventListener('mouseup', () => isDrawing = false);
        canvas.addEventListener('mousemove', (e) => {
            if (!isDrawing || !isMyTurn) return;
            var pos = getMousePos(e);
            drawCircle(pos.x, pos.y, 'black');
            socket.emit('draw_event', {x: pos.x, y: pos.y, color: 'black'});
        });

        function clearCanvas() {
            if (!isMyTurn) return;
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            socket.emit('clear_board');
        }

        function sendMessage() {
            var input = document.getElementById("msgInput");
            if (input.value) {
                socket.emit('chat_message', {msg: input.value});
                input.value = "";
            }
        }
        document.getElementById("msgInput").addEventListener("keypress", (e) => { if (e.key === "Enter") sendMessage(); });
        function addMessage(text, className) {
            var ul = document.getElementById('messages');
            var li = document.createElement('li');
            li.textContent = text;
            if(className) li.className = className;
            ul.appendChild(li);
            ul.scrollTop = ul.scrollHeight;
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(html_code)

# --- SERVER LOGIC ---

def broadcast_scores():
    score_list = []
    for sid, p_data in players.items():
        score_list.append({'name': p_data['name'], 'score': p_data['score']})
    emit('update_scores', {'players': score_list}, broadcast=True)

def start_new_round():
    global current_drawer, current_word, turn_order
    
    turn_order = [sid for sid in turn_order if sid in players]

    if len(players) < 2:
        current_drawer = None
        emit('game_waiting', {}, broadcast=True)
        return

    if current_drawer not in turn_order:
        current_drawer = turn_order[0]
    else:
        turn_order.pop(0)
        turn_order.append(current_drawer)
        current_drawer = turn_order[0]

    current_word = random.choice(WORDS)
    drawer_name = players[current_drawer]['name']
    
    emit('new_round', {
        'drawer': current_drawer, 
        'drawer_name': drawer_name,
        'word': current_word
    }, broadcast=True)


@socketio.on('join_game')
def handle_join(data):
    global current_drawer
    sid = request.sid
    username = data.get('username', 'Anonymous')
    
    players[sid] = {"name": username, "score": 0}
    if sid not in turn_order:
        turn_order.append(sid)
    
    emit('system_message', {'msg': f"{username} joined!"}, broadcast=True)
    broadcast_scores()
    
    if len(players) >= 2 and current_drawer is None:
        start_new_round()
    elif current_drawer and current_drawer in players:
        emit('new_round', {
            'drawer': current_drawer,
            'drawer_name': players[current_drawer]['name'],
            'word': current_word
        }, to=sid)
    else:
        emit('game_waiting', {}, to=sid)


@socketio.on('disconnect')
def handle_disconnect():
    global current_drawer
    sid = request.sid
    
    if sid in players:
        del players[sid]
        if sid in turn_order:
            turn_order.remove(sid)
        broadcast_scores()
        
        if len(players) < 2:
            current_drawer = None
            emit('game_waiting', {}, broadcast=True)
        elif sid == current_drawer:
            current_drawer = None
            start_new_round()

@socketio.on('reset_game')
def handle_reset():
    global players, turn_order, current_drawer, current_word
    print("!!! RESET TRIGGERED !!!")
    players = {}
    turn_order = []
    current_drawer = None
    current_word = ""
    emit('force_reload', broadcast=True)

@socketio.on('draw_event')
def handle_draw(data):
    if request.sid == current_drawer:
        emit('draw_event', data, broadcast=True, include_self=False)

@socketio.on('clear_board')
def handle_clear():
    if request.sid == current_drawer:
        emit('clear_board', broadcast=True, include_self=False)

@socketio.on('chat_message')
def handle_chat(data):
    sid = request.sid
    if sid not in players: return
    
    msg = data['msg'].strip()
    name = players[sid]['name']

    if sid == current_drawer and msg.lower() == current_word.lower():
        emit('system_message', {'msg': "You cannot guess your own word!"}, to=sid)
        return

    if msg.lower() == current_word.lower():
        if sid == current_drawer: return 
        players[sid]['score'] += 10
        emit('game_won', {'msg': f"🏆 {name} guessed {current_word.upper()}!"}, broadcast=True)
        broadcast_scores()
        start_new_round()
    else:
        emit('chat_message', {'user': name, 'msg': msg}, broadcast=True)

if __name__ == '__main__':

    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
