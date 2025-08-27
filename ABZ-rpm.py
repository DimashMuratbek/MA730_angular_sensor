from machine import Pin, Timer
import time

PPR = 1023  # pulses per revolution
UPDATE_HZ = 10  # how often to print RPM
DEADBAND = 0.5

pinA = Pin(10, Pin.IN, Pin.PULL_UP)
pinB = Pin(11, Pin.IN, Pin.PULL_UP)

edge_count = 0 # signed edges since last update

def on_A_rising(pin):
    global edge_count
     # Direction from B at A's rising edge (flip +1/-1 if backwards)
    if pinB.value() == 0:
        direction = +1
    else:
        direction = -1
        
    edge_count += direction

pinA.irq(trigger=Pin.IRQ_RISING, handler=on_A_rising)

last_t = time.ticks_us()

def on_timer(t):
    global edge_count, last_t
    
    now = time.ticks_us()
    dt = time.ticks_diff(now, last_t) / 1000000.0
    last_t = now
    
    # grab & reset counter (tiny race possible; negligible in practice)
    cnt = edge_count; edge_count = 0
    if dt <= 0: return
    
    rpm = (cnt / dt) * (60.0 / PPR)
    
    # deadband to kill jitter near zero
    rpm = 0.0 if abs(rpm) < DEADBAND else rpm
    
    print(f"RPM: {rpm:8.2f}")

tmr = Timer()                                   # <<< keep a reference
tmr.init(freq=UPDATE_HZ, mode=Timer.PERIODIC, callback=on_timer)

while True:
    time.sleep(1)  # keep the script alive
