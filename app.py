import flask
from flask import request, jsonify, render_template_string
import tinytuya
import os
import threading
import time

# === ТВОИ КЛЮЧИ ===
IR_HUB_ID = "bf21110124fae7e2efs8na"
AC_DEVICE_ID = "bfcac126e460aa3efaw4bl"
API_KEY = "an4agmp34mv7e4gu3fhj"
API_SECRET = "84977990f74d460c81b327a0e0635afd"
API_REGION = "eu"

app = flask.Flask(__name__)

URL_IR = f"/v1.0/infrareds/{IR_HUB_ID}/air-conditioners/{AC_DEVICE_ID}/command"

# Список активных таймеров
timers = []

# Фоновый рабочий, который следит за временем
def timer_worker():
    global timers
    while True:
        now = time.time()
        for t in timers[:]:
            if now >= t['execute_at']:
                try:
                    cloud = tinytuya.Cloud(apiRegion=API_REGION, apiKey=API_KEY, apiSecret=API_SECRET)
                    if t['action'] == 'on':
                        # Включаем и сразу ставим макс скорость
                        cloud.cloudrequest(URL_IR, post={"code": "power", "value": 1})
                        cloud.cloudrequest(URL_IR, post={"code": "wind", "value": 3})
                    elif t['action'] == 'off':
                        # Выключаем
                        cloud.cloudrequest(URL_IR, post={"code": "power", "value": 0})
                except Exception as e:
                    print("Ошибка таймера:", e)
                # Удаляем отработавший таймер
                timers.remove(t)
        time.sleep(10) # Проверяем каждые 10 секунд

# Запускаем фоновый поток при старте сервера
threading.Thread(target=timer_worker, daemon=True).start()


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
        #status { margin-top: 10px; font-size: 16px; color: #white; background: #444; padding: 12px; border-radius: 12px; display: inline-block; width: 85%; max-width: 380px; font-weight: bold; transition: 0.3s;}
        
        /* Стили для ползунка */
        input[type=range] { -webkit-appearance: none; width: 90%; margin: 15px 0; background: transparent; }
        input[type=range]::-webkit-slider-thumb { -webkit-appearance: none; height: 24px; width: 24px; border-radius: 50%; background: #FF9800; cursor: pointer; margin-top: -8px; box-shadow: 0 0 10px rgba(255,152,0,0.5); }
        input[type=range]::-webkit-slider-runnable-track { width: 100%; height: 8px; cursor: pointer; background: #444; border-radius: 4px; }
        .timer-display { font-size: 24px; font-weight: bold; color: #FF9800; margin-bottom: 5px; }
        #activeTimers { margin-top: 15px; font-size: 14px; color: #03a9f4; font-weight: bold; text-align: left; padding: 0 20px;}
    </style>
</head>
<body>
    <h2 style="margin-bottom: 5px;">Кондиционер</h2>
    <div id="status">🔍 Проверка связи...</div>

    <div class="section">
        <div class="section-title">Питание</div>
        <button class="btn power-on" onclick="send('power', 1)">ВКЛЮЧИТЬ</button>
        <button class="btn power-off" onclick="send('power', 0)">ВЫКЛЮЧИТЬ</button>
    </div>
    
    <div class="section" style="border: 2px dashed #444;">
        <div class="section-title">Таймер</div>
        <div class="timer-display" id="sliderValDisplay">30 мин</div>
        <input type="range" id="timeSlider" min="10" max="720" step="10" value="30" oninput="updateSlider()">
        <div>
            <button class="btn power-on" style="width: 42%; font-size: 14px; background-color: #388E3C;" onclick="setTimer('on')">ВКЛ через...</button>
            <button class="btn power-off" style="width: 42%; font-size: 14px; background-color: #d32f2f;" onclick="setTimer('off')">ВЫКЛ через...</button>
        </div>
        <div id="activeTimers"></div>
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
        let isSending = false;

        function updateSlider() {
            let val = document.getElementById('timeSlider').value;
            let display = document.getElementById('sliderValDisplay');
            if (val < 60) {
                display.innerText = val + " мин";
            } else {
                let h = Math.floor(val / 60);
                let m = val % 60;
                display.innerText = h + " ч " + (m > 0 ? m + " мин" : "00 мин");
            }
        }

        function changeTemp(delta) {
            currentTemp += delta;
            if(currentTemp < 16) currentTemp = 30; 
            if(currentTemp > 30) currentTemp = 16;
            document.getElementById('tempVal').innerText = currentTemp;
            document.getElementById('tempSend').innerText = currentTemp;
        }

        function sendTemp() { send('temp', currentTemp); }

        function checkStatus() {
            if (isSending) return;
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    let statusDiv = document.getElementById('status');
                    if(data.online) {
                        statusDiv.innerText = "🟢 Пульт активен";
                        statusDiv.style.background = "#2e7d32";
                    } else {
                        statusDiv.innerText = "🔴 Пульт не активен";
                        statusDiv.style.background = "#c62828";
                    }
                    
                    let timersDiv = document.getElementById('activeTimers');
                    if(data.timers && data.timers.length > 0) {
                        timersDiv.innerHTML = "⏳ <b>Ожидают выполнения:</b><br>" + data.timers.join('<br>');
                    } else {
                        timersDiv.innerHTML = "";
                    }
                }).catch(() => {});
        }

        function setTimer(action) {
            let val = document.getElementById('timeSlider').value;
            let actionText = action === 'on' ? 'ВКЛЮЧЕНИЕ' : 'ВЫКЛЮЧЕНИЕ';
            
            isSending = true;
            let statusDiv = document.getElementById('status');
            statusDiv.innerText = "⏳ Ставлю таймер...";
            statusDiv.style.background = "#ff9800";

            fetch(`/api/timer?action=${action}&minutes=${val}`)
                .then(res => res.json())
                .then(data => {
                    statusDiv.innerText = `✅ ${actionText} через ${val} мин`;
                    statusDiv.style.background = "#4CAF50";
                    setTimeout(() => { isSending = false; checkStatus(); }, 2000);
                });
        }

        function send(code, value) {
            isSending = true;
            let statusDiv = document.getElementById('status');
            statusDiv.innerText = "⏳ Отправка команды...";
            statusDiv.style.background = "#ff9800";
            
            fetch(`/api/command?code=${code}&value=${value}`)
                .then(response => response.json())
                .then(data => {
                    if(data.status === "success") {
                        statusDiv.innerText = "✅ " + data.message;
                        statusDiv.style.background = "#4CAF50";
                    } else {
                        statusDiv.innerText = "❌ Ошибка Tuya";
                        statusDiv.style.background = "#f44336";
                    }
                    setTimeout(() => { isSending = false; checkStatus(); }, 3000);
                })
                .catch(error => {
                    statusDiv.innerText = "❌ Ошибка сети";
                    statusDiv.style.background = "#f44336";
                    setTimeout(() => { isSending = false; checkStatus(); }, 3000);
                });
        }

        window.onload = function() { checkStatus(); updateSlider(); };
        setInterval(checkStatus, 12000);
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

@app.route('/api/status')
def status():
    try:
        cloud = tinytuya.Cloud(apiRegion=API_REGION, apiKey=API_KEY, apiSecret=API_SECRET)
        res = cloud.cloudrequest(f"/v1.0/devices/{IR_HUB_ID}")
        is_online = False
        if res and res.get('success'):
            is_online = res.get('result', {}).get('online', False)
        
        # Считаем, сколько минут осталось активным таймерам
        active_timers = []
        now = time.time()
        for t in timers:
            rem = int((t['execute_at'] - now) / 60)
            if rem >= 0:
                action_ru = "ВКЛ" if t['action'] == 'on' else "ВЫКЛ"
                active_timers.append(f"• {action_ru} через ~{rem} мин")
                
        return jsonify({"status": "success", "online": is_online, "timers": active_timers})
    except:
        return jsonify({"status": "error", "online": False, "timers": []})

@app.route('/api/timer')
def set_timer():
    global timers
    action = request.args.get('action')
    minutes = int(request.args.get('minutes', 0))
    
    # Удаляем старые таймеры на такое же действие (чтобы не было дублей)
    timers = [t for t in timers if t['action'] != action]
    
    execute_at = time.time() + (minutes * 60)
    timers.append({"action": action, "execute_at": execute_at})
    
    return jsonify({"status": "success"})

@app.route('/api/command')
def command():
    code = request.args.get('code')
    value = request.args.get('value', '')
    if value.isdigit(): value = int(value)
        
    try:
        cloud = tinytuya.Cloud(apiRegion=API_REGION, apiKey=API_KEY, apiSecret=API_SECRET)
        if code == 'power' and value == 1:
            cloud.cloudrequest(URL_IR, post={"code": "power", "value": 1})
            cloud.cloudrequest(URL_IR, post={"code": "wind", "value": 3})
            return jsonify({"status": "success", "message": "Включен на макс. скорость!"})
        else:
            cloud.cloudrequest(URL_IR, post={"code": code, "value": value})
            return jsonify({"status": "success", "message": "Сигнал отправлен!"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
