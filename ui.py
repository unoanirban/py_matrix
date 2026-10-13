# ui.py - OLED + TTP224 4-channel touch input in TOGGLE mode (module 1 of 2)
#
# Wiring (power the TTP224 from 3.3 V so its outputs are safe for the ESP8266):
#   TTP224 OUT1 -> D5 (GPIO14)   channel 1 : +
#   TTP224 OUT2 -> D6 (GPIO12)   channel 2 : -
#   TTP224 OUT3 -> D7 (GPIO13)   channel 3 : enter (tap) / back (double tap)
#   TTP224 OUT4 -> D0 (GPIO16)   channel 4 : scroll up/down on the result
#   TTP224 VCC -> 3V3, GND -> GND
#   OLED   SCL -> D2 (GPIO4), SDA -> D1 (GPIO5)   (as found by scanning your board)
# Works with the TTP224 in either mode - set TOGGLE below to match your module:
#   TOGGLE = False : normal/momentary mode (output is on while touched)  <- default
#   TOGGLE = True  : toggle mode (each touch flips the output; TOG jumper closed)
import time, framebuf, machine
from machine import Pin, I2C
import ssd1306

machine.freq(160000000)

found = []
for f in (400000, 100000):                  # fall back to a slower bus if needed
    i2c = I2C(scl=Pin(4), sda=Pin(5), freq=f)
    found = i2c.scan()
    if found:
        break
addr = 0x3D if (0x3D in found and 0x3C not in found) else 0x3C
print('I2C scan:', [hex(a) for a in found], '-> using', hex(addr))
oled = ssd1306.SSD1306_I2C(128, 64, i2c, addr)

TP = [Pin(n, Pin.IN) for n in (14, 12, 13, 16)]
last = [p.value() for p in TP]      # baseline: whatever state the outputs are in now
base = last[:]                      # idle level of each output
TOGGLE = False                      # False: TTP224 in normal/momentary mode (output follows your finger)
                                    # True : TTP224 in toggle mode (every touch flips the output)
LOCK = 80                           # ms: ignore a re-trigger of the same channel (chatter)
tc = [-1000] * 4                    # time of the last accepted touch per channel
tl = [time.ticks_ms() - 1000] * 4   # time of the previous tap per channel
st = [0, 0, 0, 0]                   # fast-tap streak per channel
pend = 0                            # time of a first tap on ch3 waiting for a 2nd
DBL = 350                           # double-tap window (ms)


def step(i):
    """Step size for +/-: 1 normally, bigger if you keep tapping quickly."""
    now = time.ticks_ms()
    if time.ticks_diff(now, tl[i]) < 500:
        st[i] += 1
    else:
        st[i] = 0
    tl[i] = now
    n = st[i]
    return 1 if n < 4 else (5 if n < 10 else 20)


def ev():
    """Block until a touch happens. Returns (delta, ok, scroll):
    delta  = +n (ch1) / -n (ch2)
    ok     = 0 none, 1 = ch3 single tap (enter), 2 = ch3 double tap (back)
    scroll = 1 when ch4 was touched"""
    global pend
    while True:
        d = s = 0
        dbl = False
        for i in range(4):
            v = TP[i].value()
            if v != last[i]:
                time.sleep_ms(5)                    # debounce
                v = TP[i].value()
                if v == last[i]:
                    continue
                last[i] = v
                if not TOGGLE and v == base[i]:
                    continue                        # momentary mode: ignore the release
                now = time.ticks_ms()
                if time.ticks_diff(now, tc[i]) < LOCK:
                    continue                        # ignore chatter
                tc[i] = now
                if i == 0:
                    d += step(0)
                elif i == 1:
                    d -= step(1)
                elif i == 2:
                    if pend:
                        pend = 0
                        dbl = True
                    else:
                        pend = max(1, time.ticks_ms())
                else:
                    s = 1
        if dbl:
            return d, 2, s
        if pend and time.ticks_diff(time.ticks_ms(), pend) >= DBL:
            pend = 0
            return d, 1, s
        if d or s:
            return d, 0, s
        time.sleep_ms(10)


def header(txt):
    oled.fill_rect(0, 0, 128, 10, 1)
    oled.text(txt, 2, 1, 0)


def big(txt, y, s=3):
    """Draw text scaled up s times, centred horizontally."""
    n = len(txt)
    w = n * 8
    buf = bytearray(n * 8)
    fb = framebuf.FrameBuffer(buf, w, 8, framebuf.MONO_HLSB)
    fb.text(txt, 0, 0, 1)
    x0 = (128 - w * s) // 2
    for r in range(8):
        for c in range(w):
            if fb.pixel(c, r):
                oled.fill_rect(x0 + c * s, y + r * s, s, s, 1)
