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

#Button Set
BtnUpPin = 16    # GPIO23
BtnDownPin = 18  # GPIO14

#Button Set Up
def setupButtons():
    GPIO.setup(BtnUpPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(BtnDownPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def checkButtons():
    global globalCounter

    # Debounce delay
    time.sleep(0.05)

    if GPIO.input(BtnUpPin) == GPIO.LOW:
        globalCounter += 1
        print(f"Increased threshold: {globalCounter}")

    if GPIO.input(BtnDownPin) == GPIO.LOW:
        globalCounter -= 1
        print(f"Decreased threshold: {globalCounter}")



#Motor Functions
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
FAN_ON_TEMP = 83
FAN_OFF_TEMP = 72
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

# Rotary Encoder Set-up

RoAPin = 29    # pin11
RoBPin = 31    # pin12
BtnPin = 32    # Button Pin

globalCounter = 0

flag = 0
Last_RoB_Status = 0
Current_RoB_Status = 0

def setupR():
    GPIO.setmode(GPIO.BOARD)       # Numbers GPIOs by physical location
    GPIO.setup(RoAPin, GPIO.IN)    # input mode
    GPIO.setup(RoBPin, GPIO.IN)
    GPIO.setup(RoAPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(RoBPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(BtnPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(BtnPin, GPIO.FALLING, callback=btnISR)

def rotaryDeal():
    global globalCounter
    global Last_RoB_Status
    global Current_RoB_Status

    if GPIO.input(RoAPin) == 0:
        Current_RoB_Status = GPIO.input(RoBPin)
        if Current_RoB_Status != Last_RoB_Status:
            if Current_RoB_Status == 0:
                globalCounter += 1
            else:
                globalCounter -= 1
        Last_RoB_Status = Current_RoB_Status
        time.sleep(0.01)  # Small debounce delay

def btnISR(channel):
	global globalCounter
	globalCounter = 0

def loopR():
    global globalCounter
    global fan_running  
    tmp = 0	# Rotary Temperary

    while True:
        rotaryDeal()
        checkButtons()

        result = sensor.read()
        

        if tmp != globalCounter:
            print('globalCounter = %d' % globalCounter)

        if result.is_valid():   #esuring data is readable and valid
            
            temp_c = result.temperature
            temp_f = (temp_c * 9/5) + 32
            hum = result.humidity

            # Rotary Encoder Adjustment
            
            dynamic_fan_on_temp = FAN_ON_TEMP + globalCounter
            dynamic_fan_off_temp = FAN_OFF_TEMP + globalCounter

            # Prepare screen lines
            temp_str = "T:{:.1f}F H:{:.0f}%".format(temp_f, hum)
            fan_target_str = "Fan ON > {:.0f}F".format(dynamic_fan_on_temp)

            # Display both
            lcd.display_data(temp_str, fan_target_str)

            # Then use dynamic_fan_on_temp instead of FAN_ON_TEMP
            if temp_f > dynamic_fan_on_temp and not fan_running:
                fan_on()
                fan_running = True
            elif temp_f < dynamic_fan_off_temp and fan_running:
                fan_off()
                fan_running = False

        time.sleep(0.1)

def destroy():
	GPIO.cleanup()             # Release resource

       

# Main Loop 
if __name__ == '__main__':
    setup()
    setupR()
    setupButtons()

    try:
        # LCD set-up 
        lcd = Screen(bus=1, addr=0x27, cols=16, rows=2)
        lcd.enable_backlight()
        loopR()

    except KeyboardInterrupt:
        print("Cleanup")
        fan_off()
        GPIO.cleanup()
        destroy()

