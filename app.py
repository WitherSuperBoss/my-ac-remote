import flask
from flask import render_template_string
import os

app = flask.Flask(__name__)

# Красивая HTML-заглушка
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Умный Климат - Техработы</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            text-align: center; 
            background-color: #1a1a1a; 
            color: white; 
            margin: 0; 
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            height: 100vh;
        }
        .container {
            background: #2c2c2c;
            padding: 40px 20px;
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
            width: 85%;
            max-width: 400px;
            border: 2px dashed #ff9800;
        }
        .icon {
            font-size: 64px;
            margin-bottom: 20px;
            animation: pulse 2s infinite;
        }
        .title {
            font-size: 24px;
            font-weight: bold;
            color: #f44336;
            margin-bottom: 15px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .subtitle {
            font-size: 16px;
            color: #aaa;
            line-height: 1.5;
        }
        .status-badge {
            margin-top: 25px;
            display: inline-block;
            background: #444;
            color: #ff9800;
            padding: 8px 15px;
            border-radius: 12px;
            font-size: 14px;
            font-weight: bold;
        }
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.1); }
            100% { transform: scale(1); }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="icon">🛠️</div>
        <div class="title">Пульт временно<br>не работает</div>
        <div class="subtitle">
            Ожидаем продления API от серверов Tuya.<br>
            <b>Скоро починю!</b>
        </div>
        <div class="status-badge">⏳ Статус: на модерации</div>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

# На всякий случай оставляем заглушки для API, чтобы если телефон попытается отправить команду по старой памяти, сервер не упал
@app.route('/api/status')
def status():
    return flask.jsonify({"status": "maintenance", "online": False})

@app.route('/api/timer')
@app.route('/api/command')
@app.route('/api/clear_queue')
@app.route('/api/debug')
def dummy_api():
    return flask.jsonify({"status": "maintenance"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
