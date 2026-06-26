import flask
from flask import request, jsonify, render_template_string
import tinytuya
import os

# === ТВОИ КЛЮЧИ ===
IR_HUB_ID = "bf21110124fae7e2efs8na"
AC_DEVICE_ID = "bfcac126e460aa3efaw4bl"
API_KEY = "an4agmp34mv7e4gu3fhj"
API_SECRET = "84977990f74d460c81b327a0e0635afd"
API_REGION = "eu"

app = flask.Flask(__name__)

URL_IR = f"/v1.0/infrareds/{IR_HUB_ID}/air-conditioners/{AC_DEVICE_ID}/command"

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Умный Климат</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; text-align: center; background-color: #1a1a1a; color: white; padding-bottom: 50px; margin: 0; padding-top: 20px;}
        .btn { padding: 15px; font-size: 18px; margin: 5px; border-radius: 12px; border: none; font-weight: bold; cursor: pointer; transition: 0.2s; box-shadow: 0 4px 6px rgba(0,0,0,0.3);}
        .btn:active { transform: scale(0.95); }
        .power-on { background-color: #4CAF50; color: white; width: 42%; }
        .power-off { background-color: #f44336; color: white; width: 42%; }
        .temp-btn { background-color: #2196F3; color: white; font-size: 28px; width: 60px; height: 60px; border-radius: 50%; padding: 0;}
        .mode-btn { background-color: #444; color: white; width: 42%; font-size: 16px;}
        .send-temp-btn { background-color: #FF9800; color: white; width: 88%; margin-top: 15px; padding: 20px;}
        .wind-btn { background-color: #607D8B; color: white; width: 42%; font-size: 16px; margin-top: 5px;}
        .temp-display { font-size: 48px; margin: 0 20px; font-weight: bold; vertical-align: middle;}
        .section { margin: 15px auto; padding: 20px 10px; background: #2c2c2c; border-radius: 20px; width: 90%; max-width: 400px;}
        .section-title { font-size: 14px; color: #aaa; margin-bottom: 15px; text-transform: uppercase; letter-spacing: 1px;}
        #status { margin-top: 10px; font-size: 16px; color: #aaa; background: #2c2c2c; padding: 10px; border-radius: 10px; display: inline-block; width: 85%; max-width: 380px;}
    </style>
</head>
<body>
    <h2 style="margin-bottom: 5px;">Кондиционер</h2>
    <div id="status">✅ Облако готово</div>

    <div class="section">
        <div class="section-title">Питание</div>
        <button class="btn power-on" onclick="send('power', 1)">ВКЛЮЧИТЬ</button>
        <button class="btn power-off" onclick="send('power', 0)">ВЫКЛЮЧИТЬ</button>
    </div>

    <div class="section">
        <div class="section-title">Температура</div>
        <div>
            <button class="btn temp-btn" onclick="changeTemp(-1)">-</button>
            <span class="temp-display" id="tempVal">22</span>
            <button class="btn temp-btn" onclick="changeTemp(1)">+</button>
        </div>
        <button class="btn send-temp-btn" onclick="sendTemp()">Установить <span id="tempSend">22</span>°C</button>
    </div>

    <div class="section">
        <div class="section-title">Режим работы</div>
        <button class="btn mode-btn" onclick="send('mode', 0)">❄️ Охлаждение</button>
        <button class="btn mode-btn" onclick="send('mode', 1)">☀️ Обогрев</button>
        <button class="btn mode-btn" onclick="send('mode', 3)">💨 Вентилятор</button>
        <button class="btn mode-btn" onclick="send('mode', 2)">🤖 Авто-режим</button>
    </div>

    <div class="section">
        <div class="section-title">Скорость обдува</div>
        <button class="btn wind-btn" onclick="send('wind', 0)">🤖 Авто</button>
        <button class="btn wind-btn" onclick="send('wind', 1)">🔽 Минимум</button>
        <button class="btn wind-btn" onclick="send('wind', 2)">▶️ Средняя</button>
        <button class="btn wind-btn" onclick="send('wind', 3)">🔼 Максимум</button>
    </div>

    <script>
        let currentTemp = 22;
        function changeTemp(delta) {
            currentTemp += delta;
            if(currentTemp < 16) currentTemp = 30; 
            if(currentTemp > 30) currentTemp = 16;
            document.getElementById('tempVal').innerText = currentTemp;
            document.getElementById('tempSend').innerText = currentTemp;
        }

        function sendTemp() {
            send('temp', currentTemp);
        }

        function send(code, value) {
            let statusDiv = document.getElementById('status');
            statusDiv.innerText = "⏳ Отправка...";
            statusDiv.style.color = "#ffeb3b";
            
            fetch(`/api/command?code=${code}&value=${value}`)
                .then(response => response.json())
                .then(data => {
                    if(data.status === "success") {
                        statusDiv.innerText = "✅ Сигнал отправлен!";
                        statusDiv.style.color = "#4CAF50";
                    } else {
                        statusDiv.innerText = "❌ Ошибка Tuya";
                        statusDiv.style.color = "#f44336";
                    }
                })
                .catch(error => {
                    statusDiv.innerText = "❌ Ошибка сети";
                    statusDiv.style.color = "#f44336";
                });
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

@app.route('/api/command')
def command():
    code = request.args.get('code')
    value = request.args.get('value', '')
    
    if value.isdigit():
        value = int(value)
        
    try:
        cloud = tinytuya.Cloud(apiRegion=API_REGION, apiKey=API_KEY, apiSecret=API_SECRET)
        cmd = {"code": code, "value": value}
        cloud.cloudrequest(URL_IR, post=cmd)
        return jsonify({"status": "success", "message": "Сигнал отправлен!"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
