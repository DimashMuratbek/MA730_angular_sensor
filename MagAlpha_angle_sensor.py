from machine import SPI, Pin
import time

N = 16384  # 14-bit counts per rev for MA730
zero_off = 0  # counts


# SPI0 on GP2=SCK, GP3=TX(MOSI), GP4=RX(MISO)
spi = SPI(0, baudrate=1000000, polarity=0, phase=0, bits=8, firstbit=SPI.MSB,
          sck=Pin(2), mosi=Pin(3), miso=Pin(4))
cs = Pin(5, Pin.OUT, value=1)  # CS high idle

def read_raw16():
    cs.value(0)
    # clock out 16 bits (two bytes) while reading
    resp = bytearray(2)
    spi.write_readinto(b'\x00\x00', resp)
    cs.value(1)
    return (resp[0] << 8) | resp[1]

def read_angle_counts():
    v = read_raw16()
    return (v >> 2) & 0x3FFF  # 14-bit angle


def set_zero():
    global zero_off
    zero_off = read_angle_counts()  # call this when the shaft is at 0°
    print("Zero set at counts =", zero_off)


def read_deg_zeroed():
    c = read_angle_counts()
    cz = (c - zero_off) % N  # wrap 0..N-1
    return cz * (360.0 / N)


def rpm_reader(alpha=0.2, deadband=0.5, sleep_s=0.02):
    
    #alpha: 0..1, higher = less smoothing
    #deadband: clamp tiny RPMs to 0 to kill jitter (in RPM)
    #sleep_s: print/update interval; lower -> higher trackable RPM
    
    prev_c = read_angle_counts()
    prev_t = time.ticks_us()
    rpm_filt = 0.0

    while True:
        c = read_angle_counts()
        t = time.ticks_us()
        dt = time.ticks_diff(t, prev_t) / 1000000.0
        if dt <= 0:
            continue

        # unwrap smallest signed delta in counts
        dc = ((c - prev_c + (N // 2)) % N) - (N // 2)
            
        # remove jitter so it doesn't show negative value when shaft stops    
        rpm_inst = ( (dc / N) / dt ) * 60.0
        rpm_filt = (1 - alpha) * rpm_filt + alpha * rpm_inst
        
        if abs(rpm_filt) < deadband:
            rpm_out = 0.0
        else:
            rpm_out = rpm_filt
        
        print(f"RPM: {rpm_out:8.2f}")

        prev_c = c
        prev_t = t
        time.sleep(sleep_s)


# disable set_zero() with while loop to enable rpm reading
set_zero()  # call once at chosen 0°
while True:
    print(f"{read_deg_zeroed():.2f} deg")
    time.sleep(0.05)

# disable rpm_reader() to read degrees
# run rpm reader
# rpm_reader()
