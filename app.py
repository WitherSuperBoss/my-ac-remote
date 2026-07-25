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

timers = []
command_queue = []
device_status = {"online": True, "offline_since": None}

def check_tuya_status():
    try:
        cloud = tinytuya.Cloud(apiRegion=API_REGION, apiKey=API_KEY, apiSecret=API_SECRET)
        res = cloud.cloudrequest(f"/v1.0/devices/{IR_HUB_ID}")
        if res and res.get('success'):
            return res.get('result', {}).get('online', False)
    except:
        pass
    return False

def master_worker():
    global timers, command_queue, device_status
    while True:
        now = time.time()
        
        is_online = check_tuya_status()
        if is_online:
            device_status["online"] = True
            device_status["offline_since"] = None
        else:
            if device_status["online"]:
                device_status["offline_since"] = now
            device_status["online"] = False

        for t in timers[:]:
            if now >= t['execute_at']:
                if t['action'] == 'on':
                    command_queue.append({"code": "power", "value": 1})
                    command_queue.append({"code": "wind", "value": 3, "delay": 1.5})
                elif t['action'] == 'off':
                    command_queue.append({"code": "power", "value": 0})
                timers.remove(t)

        if device_status["online"] and len(command_queue) > 0:
            cloud = tinytuya.Cloud(apiRegion=API_REGION, apiKey=API_KEY, apiSecret=API_SECRET)
            
            while len(command_queue) > 0:
                cmd = command_queue[0]
                if "delay" in cmd:
                    time.sleep(cmd["delay"])
                    
                try:
                    res = cloud.cloudrequest(URL_IR, post={"code": cmd["code"], "value": cmd["value"]})
                    if res and not res.get('success') and 'offline' in str(res).lower():
                        device_status["online"] = False
                        if not device_status["offline_since"]: device_status["offline_since"] = now
                        break
                    
                    command_queue.pop(0)
                    time.sleep(0.5)
                except Exception as e:
                    print("Ошибка отправки:", e)
                    break

        time.sleep(5)

threading.Thread(target=master_worker, daemon=True).start()

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
        #status { margin-top: 10px; font-size: 16px; color: white; background: #444; padding: 12px; border-radius: 12px; display: inline-block; width: 85%; max-width: 380px; font-weight: bold; transition: 0.3s;}
        
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
        <div class="timer-display" id="sliderValDisplay">1 мин</div>
        <input type="range" id="timeSlider" min="1" max="180" step="1" value="1" oninput="updateSlider()">
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
    
    <!-- Кнопка очистки очереди -->
    <div style="margin-top: 10px;">
        <button class="btn" style="background-color: #555; color: white; width: 90%; max-width: 400px; font-size: 14px; border: 1px solid #777;" onclick="clearQueue()">🗑️ Очистить очередь команд</button>
    </div>
    
    <!-- НОВАЯ КНОПКА ДИАГНОСТИКИ -->
    <div style="margin-top: 5px; margin-bottom: 30px;">
        <button class="btn" style="background-color: #2c3e50; color: white; width: 90%; max-width: 400px; font-size: 14px; border: 1px solid #777;" onclick="debugTuya()">🐛 Диагностика Tuya</button>
    </div>

    <script>
        let currentTemp = 22;

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
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    let statusDiv = document.getElementById('status');
                    let text = "";
                    if(data.online) {
                        text = "🟢 Пульт активен";
                        statusDiv.style.background = "#2e7d32";
                    } else {
                        text = "🔴 Не активен (" + data.offline_time + ")";
                        statusDiv.style.background = "#c62828";
                    }
                    
                    if(data.queue_len > 0) {
                        text += ` ⏳ (В очереди: ${data.queue_len})`;
                        if(data.online) statusDiv.style.background = "#ff9800";
                    }
                    
                    statusDiv.innerText = text;
                    
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
            fetch(`/api/timer?action=${action}&minutes=${val}`)
                .then(res => res.json())
                .then(data => { checkStatus(); });
        }

        function send(code, value) {
            fetch(`/api/command?code=${code}&value=${value}`)
                .then(response => response.json())
                .then(data => { checkStatus(); });
        }
        
        function clearQueue() {
            fetch('/api/clear_queue')
                .then(res => res.json())
                .then(data => { checkStatus(); });
        }
        
        function debugTuya() {
            fetch('/api/debug')
                .then(res => res.json())
                .then(data => {
                    alert("Ответ от серверов Tuya:\\n\\n" + JSON.stringify(data, null, 2));
                })
                .catch(err => alert("Ошибка сети при диагностике"));
        }

        window.onload = function() { checkStatus(); updateSlider(); };
        setInterval(checkStatus, 4000); 
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

@app.route('/api/status')
def status():
    offline_time_str = ""
    if not device_status["online"] and device_status["offline_since"]:
        diff = int(time.time() - device_status["offline_since"])
        if diff < 60:
            offline_time_str = f"{diff} сек"
        else:
            h = diff // 3600
            m = (diff % 3600) // 60
            offline_time_str = f"{h} ч {m} мин" if h > 0 else f"{m} мин"

    active_timers = []
    now = time.time()
    for t in timers:
        rem_sec = int(t['execute_at'] - now)
        action_ru = "ВКЛ" if t['action'] == 'on' else "ВЫКЛ"
        if rem_sec >= 0:
            if rem_sec < 120:
                active_timers.append(f"• {action_ru} через {rem_sec} сек")
            else:
                active_timers.append(f"• {action_ru} через ~{rem_sec // 60} мин")
            
    q_len = len([c for c in command_queue if c.get('code') != 'wind' or not c.get('delay')])
            
    return jsonify({
        "status": "success", 
        "online": device_status["online"], 
        "offline_time": offline_time_str,
        "queue_len": q_len,
        "timers": active_timers
    })

@app.route('/api/timer')
def set_timer():
    global timers
    action = request.args.get('action')
    minutes = int(request.args.get('minutes', 0))
    
    timers = [t for t in timers if t['action'] != action]
    execute_at = time.time() + (minutes * 60)
    timers.append({"action": action, "execute_at": execute_at})
    
    return jsonify({"status": "success"})

@app.route('/api/command')
def command():
    global command_queue
    code = request.args.get('code')
    value = request.args.get('value', '')
    if value.isdigit(): value = int(value)
    
    if code == 'power' and value == 1:
        command_queue.append({"code": "power", "value": 1})
        command_queue.append({"code": "wind", "value": 3, "delay": 1.5})
    else:
        command_queue.append({"code": code, "value": value})
        
    return jsonify({"status": "queued"})

@app.route('/api/clear_queue')
def clear_queue():
    global command_queue
    command_queue.clear()
    return jsonify({"status": "success"})

@app.route('/api/debug')
def debug_api():
    try:
        cloud = tinytuya.Cloud(apiRegion=API_REGION, apiKey=API_KEY, apiSecret=API_SECRET)
        res = cloud.cloudrequest(f"/v1.0/devices/{IR_HUB_ID}")
        return jsonify(res)
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
