import RPi.GPIO as GPIO
import time
from time import sleep
import dht11
import datetime
import smbus
#from Lesson18_LCD1602 import Screen



# DHT11 set-up (temperature sensor)
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
sensor = dht11.DHT11(pin=7)

# Motor set-up (fan)
MotorPin_A = 11 #GPIO 17 
MotorPin_B = 12 #GPIO 18

def motorStop():
	GPIO.output(MotorPin_A, GPIO.HIGH)
	GPIO.output(MotorPin_B, GPIO.HIGH)

def setup():
	GPIO.setwarnings(False)
	GPIO.setmode(GPIO.BOARD)
	GPIO.setup(MotorPin_A, GPIO.OUT)
	GPIO.setup(MotorPin_B, GPIO.OUT)
	motorStop()

def motor(status, direction):
	if status == 1:  # run
		if direction == 1:
			GPIO.output(MotorPin_A, GPIO.HIGH)
			GPIO.output(MotorPin_B, GPIO.LOW)
		else:
			GPIO.output(MotorPin_A, GPIO.LOW)
			GPIO.output(MotorPin_B, GPIO.HIGH)
	else:  # stop
		motorStop()

def loop():
	while True:
		motor(1, 1)
		time.sleep(5000)
		motor(0, 1)
		time.sleep(5000)
		motor(1, 0)
		time.sleep(5000)

def destroy():
	motorStop()
	GPIO.cleanup()             # Release resource


def fan_on():
    GPIO.output(MotorPin_A, GPIO.HIGH)
    GPIO.output(MotorPin_B, GPIO.LOW)

def fan_off():
    GPIO.output(MotorPin_A, GPIO.HIGH)
    GPIO.output(MotorPin_B, GPIO.HIGH)

    
# Temperature Thresholds
FAN_ON_TEMP = 28.5
FAN_OFF_TEMP = 28
fan_running = False


# Setup for LCD Screen

def delay(time):
    sleep(time/1000.0)

def delayMicroseconds(time):
    sleep(time/1000000.0)


class Screen():

    enable_mask = 1<<2
    rw_mask = 1<<1
    rs_mask = 1<<0
    backlight_mask = 1<<3

    data_mask = 0x00

    def __init__(self, cols = 16, rows = 2, addr=0x27, bus=1):
        self.cols = cols
        self.rows = rows        
        self.bus_num = bus
        self.bus = smbus.SMBus(self.bus_num)
        self.addr = addr
        self.display_init()
        
    def enable_backlight(self):
        self.data_mask = self.data_mask|self.backlight_mask
        
    def disable_backlight(self):
        self.data_mask = self.data_mask& ~self.backlight_mask
       
    def display_data(self, *args):
        self.clear()
        for line, arg in enumerate(args):
            self.cursorTo(line, 0)
            self.println(arg[:self.cols].ljust(self.cols))
           
    def cursorTo(self, row, col):
        offsets = [0x00, 0x40, 0x14, 0x54]
        self.command(0x80|(offsets[row]+col))
    
    def clear(self):
        self.command(0x10)

    def println(self, line):
        for char in line:
            self.print_char(char)     

    def print_char(self, char):
        char_code = ord(char)
        self.send(char_code, self.rs_mask)

    def display_init(self):
        delay(1.0)
        self.write4bits(0x30)
        delay(4.5)
        self.write4bits(0x30)
        delay(4.5)
        self.write4bits(0x30)
        delay(0.15)
        self.write4bits(0x20)
        self.command(0x20|0x08)
        self.command(0x04|0x08, delay=80.0)
        self.clear()
        self.command(0x04|0x02)
        delay(3)

    def command(self, value, delay = 50.0):
        self.send(value, 0)
        delayMicroseconds(delay)
        
    def send(self, data, mode):
        self.write4bits((data & 0xF0)|mode)
        self.write4bits((data << 4)|mode)

    def write4bits(self, value):
        value = value & ~self.enable_mask
        self.expanderWrite(value)
        self.expanderWrite(value | self.enable_mask)
        self.expanderWrite(value)        

    def expanderWrite(self, data):
        self.bus.write_byte_data(self.addr, 0, data|self.data_mask)

# Motor Set-up
       
# Main Loop 
try:
    setup()
    # LCD set-up 
    lcd = Screen(bus=1, addr=0x27, cols=16, rows=2)
    lcd.enable_backlight()
    while True:
        result = sensor.read()
        if result.is_valid():   #esuring data is readable and valid
            temp = result.temperature
            hum = result.humidity

            # Display on LCD
            lcd.display_data(f"Temp: {temp:.1f} C", f"Humidity: {hum:.1f}%")

            # Fan control logic with hysteresis
            if temp > FAN_ON_TEMP and not fan_running:
                fan_on()
                fan_running = True
            elif temp < FAN_OFF_TEMP and fan_running:
                fan_off()
                fan_running = False
        time.sleep(2)

except KeyboardInterrupt:
    print("Cleanup")
    fan_off()
    GPIO.cleanup()
