import network, socket, time
from machine import Pin, PWM

# --- Motor setup ---
IN1 = Pin(2, Pin.OUT)
IN2 = Pin(3, Pin.OUT)
ENA = PWM(Pin(4))
ENA.freq(1000)

def drive(speed):
    if speed > 0:
        IN1.value(1); IN2.value(0); ENA.duty_u16(speed)
    elif speed < 0:
        IN1.value(0); IN2.value(1); ENA.duty_u16(-speed)
    else:
        IN1.value(0); IN2.value(0); ENA.duty_u16(0)

# --- Wi-Fi setup ---
import wifi
ip = wifi.connect_wifi()
print("Server on http://%s" % ip)

# --- Web server ---
html = """<!DOCTYPE html>
<html>
<head><title>Rova-4 Control</title></head>
<body style='text-align:center;font-family:sans-serif'>
<h2>🧠 Rova-4 Remote</h2>
<a href="/f"><button style='font-size:30px'>⬆️ Forward</button></a><br><br>
<a href="/l"><button style='font-size:30px'>⬅️ Left</button></a>
<a href="/s"><button style='font-size:30px'>⏹️ Stop</button></a>
<a href="/r"><button style='font-size:30px'>➡️ Right</button></a><br><br>
<a href="/b"><button style='font-size:30px'>⬇️ Back</button></a>
</body></html>
"""

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('', 80))
s.listen(5)

while True:
    conn, addr = s.accept()
    request = conn.recv(1024)
    req = str(request)
    print("Request:", req)

    if '/f' in req: drive(40000)
    elif '/b' in req: drive(-40000)
    elif '/s' in req: drive(0)
    elif '/l' in req: print("Left!")  # you can map to left motors
    elif '/r' in req: print("Right!")

    conn.send('HTTP/1.1 200 OK\nContent-Type: text/html\nConnection: close\n\n')
    conn.sendall(html)
    conn.close()
