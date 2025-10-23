# ---- Rova-4: Pico 2 W wireless 4-motor controller ----
# Works with two L298N H-bridges (4 channels total)

import network, socket, time
from machine import Pin, PWM

# ====== Wi-Fi config ======
# Edit here or move these into config.py and import them.
WIFI_SSID = "YOUR_WIFI_2G"
WIFI_PASSWORD = "YOUR_PASSWORD"

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Connecting to WiFi…")
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        while not wlan.isconnected():
            time.sleep(0.3)
            print(".", end="")
    ip = wlan.ifconfig()[0]
    print("\nConnected, IP:", ip)
    return ip

# ====== Motor helper ======
class Motor:
    def __init__(self, in1, in2, ena, pwm_freq=20000, invert=False):
        self.in1 = Pin(in1, Pin.OUT, value=0)
        self.in2 = Pin(in2, Pin.OUT, value=0)
        self.pwm = PWM(Pin(ena))
        self.pwm.freq(pwm_freq)
        self.invert = invert
        self.stop()

    def drive_u16(self, s):  # s: -65535..65535
        s = max(-65535, min(65535, s))
        if self.invert:
            s = -s
        if s > 0:
            self.in1.value(1); self.in2.value(0); self.pwm.duty_u16(s)
        elif s < 0:
            self.in1.value(0); self.in2.value(1); self.pwm.duty_u16(-s)
        else:
            self.stop()

    def stop(self):
        self.in1.value(0); self.in2.value(0); self.pwm.duty_u16(0)

# ====== Pin map (edit if your wiring differs) ======
# L298 #1
M1 = Motor(in1=19, in2=18, ena=16)   # Channel A
M2 = Motor(in1=20, in2=21, ena=17)   # Channel B
# L298 #2
M3 = Motor(in1=13, in2=12, ena=15)   # Channel A
M4 = Motor(in1=11, in2=10, ena=14)   # Channel B

# Define sides (swap tuples if your left/right are reversed)
LEFT  = (M1, M3)
RIGHT = (M2, M4)

# Default speeds (0..65535)
SPEED_FWD  = 42000
SPEED_TURN = 38000
SPEED_BACK = 36000

def all_stop():
    for m in (M1, M2, M3, M4): m.stop()

def set_pair(pair, s):
    for m in pair: m.drive_u16(s)

def forward():
    set_pair(LEFT,  SPEED_FWD)
    set_pair(RIGHT, SPEED_FWD)

def back():
    set_pair(LEFT,  -SPEED_BACK)
    set_pair(RIGHT, -SPEED_BACK)

def left():
    set_pair(LEFT,  -SPEED_TURN)
    set_pair(RIGHT,  SPEED_TURN)

def right():
    set_pair(LEFT,   SPEED_TURN)
    set_pair(RIGHT, -SPEED_TURN)

# ====== Web UI ======
HTML = """<!doctype html><html><head>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>Rova-4 Controller</title>
<style>
body{{font-family:sans-serif;text-align:center;margin:20px}}
button{{font-size:28px;padding:12px 22px;margin:6px}}
#row{{display:flex;justify-content:center;gap:10px}}
</style></head><body>
<h2>Rova-4 Remote</h2>
<div><a href="/f"><button>^ Forward</button></a></div>
<div id=row>
  <a href="/l"><button><- Left</button></a>
  <a href="/s"><button>• Stop</button></a>
  <a href="/r"><button>-> Right</button></a>
</div>
<div><a href="/b"><button> Back</button></a></div>
<p>Speed: <input type="range" id="sp" min="10000" max="65535" value="{sp}" 
oninput="fetch('/speed?v='+this.value)"></p>
</body></html>
"""


def serve(ip):
    addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(2)
    print("HTTP server on http://%s" % ip)

    global SPEED_FWD, SPEED_TURN, SPEED_BACK

    try:
        while True:
            conn, _ = s.accept()
            req = conn.recv(1024).decode()
            path = req.split(" ")[1] if " " in req else "/"

            if path.startswith("/speed"):
                # /speed?v=NNNN
                try:
                    v = int(path.split("v=")[1])
                    v = max(1000, min(65535, v))
                    SPEED_FWD = SPEED_TURN = SPEED_BACK = v
                except:
                    pass
                body = "OK"
                conn.send("HTTP/1.1 200 OK\r\nContent-Type:text/plain\r\n\r\n"+body)
                conn.close()
                continue

            if path == "/f": forward()
            elif path == "/b": back()
            elif path == "/l": left()
            elif path == "/r": right()
            elif path == "/s": all_stop()

            page = HTML.format(sp=SPEED_FWD)
            conn.send("HTTP/1.1 200 OK\r\nContent-Type:text/html\r\nConnection: close\r\n\r\n")
            conn.sendall(page)
            conn.close()
    finally:
        s.close()
        all_stop()

# ====== Boot ======
ip = connect_wifi()
serve(ip)
