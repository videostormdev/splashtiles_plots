
import time
import struct
import sys
import crcmod
import pigpio

import configparser

from bokeh.plotting import figure, output_file, save

from splashtiles import st_pushdata


def read_n_bytes(n):

	try:
		(count, data) = pi.i2c_read_device(h, n)
	except:
		print("error: i2c_read failed")
	if count == n:
		return data
	else:
		print("error: read measurement interval didnt return " + str(n) + "B")
		return False

def i2cWrite(data):
	try:
		pi.i2c_write_device(h, data)
	except:
		print("error: i2c_write failed")
		return -1
	return True


def read_meas_interval():
	ret = i2cWrite([0x46, 0x00])
	if ret == -1:
		return -1

	try:
		(count, data) = pi.i2c_read_device(h, 3)
	except:
		eprint("error: i2c_read failed")
		return -1
	
	if count == 3:
		if len(data) == 3:
			interval = int(data[0])*256 + int(data[1])
			#print "measurement interval: " + str(interval) + "s, checksum " + str(data[2])
			return interval
		else:
			print("error: no array len 3 returned, instead " + str(len(data)) + "type: " + str(type(data)))
	else:
		print("error: read measurement interval didnt return 3B")
	return -1


def read_scd30():
	# read ready status
	while True:
		ret = i2cWrite([0x02, 0x02])
		if ret == -1:
			print("I2c write ready status error")
			return 0.0,0.0,0.0;

		data = read_n_bytes(3)
		if data == False:
			time.sleep(0.1)
			continue

		if data[1] == 1:
			#print "data ready"
			break
		else:
			#eprint(".")
			time.sleep(0.1)

	#read measurement
	i2cWrite([0x03, 0x00])
	data = read_n_bytes(18)

	#print "CO2: "  + str(data[0]) +" "+ str(data[1]) +" "+ str(data[3]) +" "+ str(data[4])

	if data == False:
		print("Error reading measurement!!")
		data = bytearray(0,0,0,0)
	
	struct_co2 = struct.pack('>BBBB', data[0], data[1], data[3], data[4])
	float_co2 = struct.unpack('>f', struct_co2)[0]

	struct_T = struct.pack('>BBBB', data[6], data[7], data[9], data[10])
	float_T = struct.unpack('>f', struct_T)[0]

	struct_rH = struct.pack('>BBBB', data[12], data[13], data[15], data[16])
	float_rH = struct.unpack('>f', struct_rH)[0]

	return float_T,float_rH,float_co2;


PIGPIO_HOST = '::1'
PIGPIO_HOST = '127.0.0.1'

pi = pigpio.pi(PIGPIO_HOST)

pi = pigpio.pi(PIGPIO_HOST)
if not pi.connected:
  eprint("no connection to pigpio daemon at " + PIGPIO_HOST + ".")
  exit(1)

I2C_SLAVE = 0x61
I2C_BUS = 1

try:
	pi.i2c_close(0)
except:
	print("I2c did not close")

try:
	h = pi.i2c_open(I2C_BUS, I2C_SLAVE)
except:
	print("i2c open failed")
	exit(1)

read_meas_result = read_meas_interval()
if read_meas_result != 2:
	# if not every 2s, set it
	print("setting interval to 2")
	ret = i2cWrite([0x46, 0x00, 0x00, 0x02, 0xE3])

pressure_mbar = 1037   # typical breck  mBar
LSB = 0xFF & pressure_mbar
MSB = 0xFF & (pressure_mbar >> 8)
pressure = [MSB, LSB]

f_crc8 = crcmod.mkCrcFun(0x131, 0xFF, False, 0x00)
crc8 = f_crc8(bytearray((pressure[0], pressure[1])))

# write current pressure to sensor 
i2cWrite([0x00, 0x10, pressure[0], pressure[1], crc8])


#pow_switch = digitalio.DigitalInOut(board.D18)
#pow_switch.direction = digitalio.Direction.OUTPUT
#fan_switch = digitalio.DigitalInOut(board.D17)
#fan_switch.direction = digitalio.Direction.OUTPUT

pi.set_mode(18, pigpio.OUTPUT)
pi.set_mode(17, pigpio.OUTPUT)
pi.write(18,0)
pi.write(17,0)

#i2c = busio.I2C(board.SCL, board.SDA)
#sht = adafruit_shtc3.SHTC3(i2c)

# control parameter defaults
target_humid_low = 80.0
target_humid_high = 91.0
target_co2_on = 800.0
target_co2_off = 600.0
humid_interval = 1001
fan_interval = 30

co2_level = 0

run_val =0 
run_acc = 0
acc_vals = [0] * 1440

temp_vals = [0.0] * 1440
humid_vals = [0.0] * 1440
co2_vals = [0.0] * 1440

# if we kill this, need to POWER CYCLE board for the I2C to work again
#   something doesn't close properly...

timer_val = 0

last_timestamp = time.time()

while True:

	# run at 1 min intervals
	while (time.time() - last_timestamp < 60):
		time.sleep(1);	
	last_timestamp = time.time()

	#  pull run params from file
	config = configparser.ConfigParser()
	config.read("config.cnf")   #this should load to mem and close file...
	target_humid_low = int(config.get('config','humid_start'))
	target_humid_high = int(config.get('config','humid_stop'))
	target_co2_on = int(config.get('config','co2_on'))
	target_co2_off = int(config.get('config','co2_off'))
	humid_interval = int(config.get('config','humid_interval'))
	fan_interval = int(config.get('config','fan_interval'))
	token = (config.get('config','token'))

	tempature = 0
	rel_humid = 0
	co2_level = 0
	try:
		#tempature, rel_humid = sht.measurements
		tempature, rel_humid, co2_level = read_scd30()

	except:
		print("I2C error")
	temp_f = ((tempature * 9/5)+32)


	temp_vals =  temp_vals[1:] + [temp_f/100.0]
	humid_vals = humid_vals[1:] + [rel_humid/100.0]
	co2_vals = co2_vals[1:] + [co2_level/1000.0]

	if (rel_humid < target_humid_low):
		run_val = 1
	elif (rel_humid >= target_humid_high):
		run_val = 0 

	# currently co2 blower is on humidifier, so it is forced is above on value
	if (co2_level > target_co2_on):
		run_val = 1

	# interval running 
	if ((timer_val % humid_interval) == 0):
		run_val = 1

	pi.write(18,run_val)

	acc_vals = acc_vals[1:] + [run_val]
	run_acc = sum(acc_vals)

	# fan interval
	if ((timer_val % fan_interval) == 0):
		pi.write(17,1)
	else:
		pi.write(17,0)

	outvar = "Temp: %0.1f F  Humidity: %0.1f %%  CO2: %0.1f  Pow: %d %d" % (temp_f, rel_humid,co2_level,run_val,run_acc)
	print(outvar)

	# print time stamp with current values to tmp file
	fo = open("/tmp/mon_runstat","w")
	print("Temp: %0.1f F" % temp_f, file=fo)
	print("Humidity: %0.1f %%" % rel_humid, file=fo)
	print("CO2: %0.1f ppm" % co2_level, file=fo)
	print("Pow: %d %d" % (run_val,run_acc), file=fo)
	fo.close

	# plot data
	#x = list(range(0,1440))
	x = list(range(-1440,0))
	output_file("/tmp/mon_plot")
	p = figure(title=outvar, x_axis_label='Time (min)', y_axis_label='Y', sizing_mode='stretch_both')
	p.border_fill_color = "black"
	p.border_fill_alpha = 0.9
	p.yaxis.major_label_text_color = "white"
	p.xaxis.major_label_text_color = "white"
	p.title.text_color = "white"
	p.background_fill_color = "black"
	p.background_fill_alpha = 0.9
	p.line(x,temp_vals, legend_label="Temp (F/100)", line_color="red", line_width=2) 
	p.line(x,humid_vals, legend_label="Humid (%)", line_color="blue", line_width=4) 
	p.line(x,co2_vals, legend_label="Co2 (ppm/1000)", line_color="white", line_width=6) 
	p.vbar(x,1,acc_vals,0, legend_label="Running", line_color="white", line_alpha=0, fill_color="white", fill_alpha=0.4, line_width=1) 
	p.legend.location = "bottom_left"
	save(p)


	# push data
	#st_pushdata(0)      #don't want to send too often, will exceed quota
	if ((timer_val % 2)==0):
		st_pushdata(2,"/tmp/mon_plot","",token)


	timer_val = timer_val + 1

	if (timer_val == 20):
		#push image
		#  this example is using pi camera to fetch an image on timer and save to this directory
		flist = glob.glob('./photos/*.jpg')
        	latest_file = max(flist, key=os.path.getctime)
		st_pushdata(1,"/tmp/mon_runstat",latest_file,token)

	if (timer_val > 239):
		timer_val = 0


pi.i2c_close(h)

