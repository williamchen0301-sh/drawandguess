# 🎨 Draw & Guess (Multiplayer)

A real-time, multiplayer Pictionary-style game built with Python, Flask, and Socket.IO. Players take turns drawing a secret word while others try to guess it in the chat.

## 🚀 How to Run the Game

### 1. Prerequisites
You need **Python** installed on your computer.

### 2. Installation
Install the required library using pip:
```bash
pip install flask-socketio

3. Start the Server
Run the game file in your terminal:

Bash
python game.py

4. Play!
Open your web browser and navigate to:
http://127.0.0.1:5000

How the Game Works
The game follows a continuous loop of rounds. Here is the flow:

Lobby: Players join by entering a username. The game waits until at least 2 players are connected.

Role Assignment:

The Artist: One player is selected to draw. They receive a Secret Word (e.g., "Apple"). Their job is to draw it on the canvas.

The Guessers: Everyone else sees a blank canvas and a masked word (e.g., _ _ _ _ _). Their job is to guess the word.

Gameplay: The Artist draws. The Guessers type into the chat box.

Winning:

If a Guesser types the correct word, the system detects it.

The Guesser gets +10 points.

The round ends immediately.

Next Round: The role of "Artist" passes to the next player in the list, and a new word is chosen automatically.

Interface & Button Guide
1. The Canvas Controls
Drawing Area: The large white box. You can only draw on this if it is YOUR turn. If it is not your turn, an overlay will block you.

🗑️ Clear Canvas:

Visible to: Only the current Artist.

Function: Wipes the entire drawing board clean instantly. Use this if you make a mistake or want to start your drawing over.

2. The Chat & Guessing Area
Type guess...: Enter your guesses here.

Send Button: Submits your message.

Anti-Cheat Feature: If you are the Artist and you type the secret word, the system will block the message and warn you. You cannot reveal the answer in chat!

3. The Scoreboard
Located on the right side (or bottom on mobile).

Shows a live ranking of all players.

The player with the highest score is automatically sorted to the top.

Green/Yellow Highlight: Indicates your own name so you can find yourself easily.

4. ⚠️ RESET GAME (Kick All)
Location: Top of the screen.

Function: This is an Admin / Debug tool.

What it does:

Wipes the server's memory (deletes all scores and players).

Forces every connected player to refresh their browser.

Kicks everyone to the login screen.

Use case: Use this if the game gets stuck, if a "ghost" player appears, or if you want to restart the match completely.

🛠️ Troubleshooting
"I see 'Waiting for players' but my friend is online?"
This usually means a "Ghost" connection is stuck in the server.

Fix: Press the red ⚠️ RESET GAME button.

"I can't see the Reset Button or Scoreboard."
Your screen might be zoomed in too far.

Fix: Zoom out (Ctrl + -)
