#!/usr/bin/env python
# encoding: utf-8
"""
Created by Peter Huewe on 2009-10-26.
Copyright 2009 Peter Huewe <peterhuewe@gmx.de>
Based on the spi testscript from Sean Nelson

This file is part of pyBusPirate.

pyBusPirate is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

pyBusPirate is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with pyBusPirate.  If not, see <http://www.gnu.org/licenses/>.
"""
import sys
import time
import serial
import Queue
import csv
from pyBusPirateLite.I2C import *
""" enter binary mode """

read_scale_table  = {}
read_scale_table['Voltage'] = [20.0, 'Volts', 100]
read_scale_table['Ripple'] = [4.0, 'Volts', 20]
read_scale_table['Current'] = [50.0, 'Amps', 250]
read_scale_table['Throttle'] = [1.0, 'Milliseconds', 2.5]
read_scale_table['Power'] = [0.2502, 'Percent', 1]
read_scale_table['RPM'] = [20416.66, 'Elec RPM', 100,000]
read_scale_table['BEC Voltage'] = [4.0, 'Volts', 20]
read_scale_table['BEC Current'] = [4.0, 'Amps', 20]
read_scale_table['Temp'] = [30.0, 'Deg C', 150]
read_scale_table['Raw NTC'] = [63.8125, '?', 255]
read_scale_table['Raw Linear'] = [30.0, 'Deg C', 150]

read_register_table_tmp = {}
read_register_table_tmp[0x00] =  'Voltage'
read_register_table_tmp[0x01] =  'Ripple'
read_register_table_tmp[0x02] =  'Current'
read_register_table_tmp[0x03] =  'Throttle'
read_register_table_tmp[0x04] =  'Power'
read_register_table_tmp[0x05] =  'RPM'
read_register_table_tmp[0x06] =  'Temp'
read_register_table_tmp[0x07] =  'BEC Voltage'
read_register_table_tmp[0x08] =  'BEC Current'
#read_register_table_tmp[0x09] =  'Raw NTC'
#read_register_table_tmp[0x0A] =  'Raw Linear'
read_register_table_tmp[0x19] =  'Link Live'
read_register_table_tmp[0x1A] =  'Fail Safe'
read_register_table_tmp[0x1B] =  'E.Stop'
#read_register_table_tmp[0x1C] =  'Packet In'
#read_register_table_tmp[0x1D] =  'Packet Out'
read_register_table_tmp[0x1E] =  'Check Bad'
#read_register_table_tmp[0x1F] =  'Packet Bad'

read_register_table_dup = {}
for x,y in read_register_table_tmp.iteritems():
	read_register_table_dup[y] =  x
read_register_table = dict(read_register_table_dup.items() + read_register_table_tmp.items())


T = time.localtime()
filename = str(T.tm_mon)+'_'+str(T.tm_mday)+'_'+str(T.tm_year)+'('+str(T.tm_hour)+'-'+str(T.tm_min)+')'
CSV = csv.writer(open('data/'+filename+'.csv','wb'),dialect='excel')
CSV.writerow(read_register_table_tmp.values())



def check_sum_calc(data):
	#Example args
	#check_sum_calc(['8e', '80', '00', '00'])
	sum = 0
	for arg in data:
		sum += int(arg,base=16)
	check_sum =  0xff & (0-sum)
	return hex(check_sum)

def i2c_write_data(data):
	i2c.send_start_bit()
	i2c.bulk_trans(len(data),data)
	i2c.send_stop_bit()

def i2c_read_bytes(data, data2, ret=False):
	out = []
	i2c.send_start_bit()
	i2c.bulk_trans(len(data),data)
	i2c.send_stop_bit()
	numbytes = 3
	data_out=[]
	i2c.send_start_bit()
	i2c.bulk_trans(len(data2),data2)
	while numbytes > 0:
		data_out.append(ord(i2c.read_byte()))	
		if numbytes > 1:
			i2c.send_ack()
		numbytes-=1
	i2c.send_nack()
	i2c.send_stop_bit()
	
	return data_out




if __name__ == '__main__':
	i2c = I2C("COM4", 115200)
	print "Entering binmode: ",
	if i2c.BBmode():
		print "OK."
	else:
		print "failed."
		sys.exit()

	print "Entering raw I2C mode: ",
	if i2c.enter_I2C():
		print "OK."
	else:
		print "failed."
		sys.exit()
		
	print "Configuring I2C."
	if not i2c.cfg_pins(I2CPins.POWER | I2CPins.PULLUPS):
		print "Failed to set I2C peripherals."
		sys.exit()
	if not i2c.set_speed(I2CSpeed._400KHZ):
		print "Failed to set I2C Speed."
		sys.exit()
	i2c.timeout(0.2)
	
	print "Reading EEPROM."
	'''
	i2c_write_data([0x8E, 0x80,0x0F, 0x00, 0xE3])
	time.sleep(1)
	i2c_read_bytes([0x8E, 0x05, 0x00, 0x00, 0x6D],[0x8F])
	i2c_read_bytes([0x8E, 5, 0, 0, 0x6D],[0x8F])
	print check_sum_calc(['0x8E', '0x05', '0x00', '0x00']),'!!!!!!'
	'''
	tmp_clock = time.clock()
	set_rpm_value = 30000
	count = 0

	# 50 samples in 10 seconds
	'''
	while (time.clock() - tmp_clock < 10):
		count += 1
		print count
		raw_rpm = i2c_read_bytes([0x8E, 0x05, 0x00, 0x00, 0x6D],[0x8F])
		raw_rpm_readable = (raw_rpm[0] << 8)+ raw_rpm[1]
		rpm_val = raw_rpm_readable/2042.0 * read_scale_table['RPM'][0]
		print rpm_val, "RPM VAL"
		raw_thro = i2c_read_bytes([0x8E, 0x03, 0x00, 0x00, 0x6F],[0x8F])
		print raw_thro
		print "dif", set_rpm_value - rpm_val
		
		if (set_rpm_value - rpm_val > 100):
			adder = raw_rpm[1] + 10
			priming = ['0x8E']
			priming.append('0x80')
			priming.append(hex(raw_rpm[0]))
			priming.append(hex(adder))
			priming.append(check_sum_calc(priming))
			for x in range(len(priming)):
				priming[x] = int(priming[x],16)
			#i2c_write_data(priming)
			print priming
			#i2c_write_data([0x8E, 0x80,adder, 0x00, 0xE3])

		elif (rpm_val - set_rpm_value > 100):
			print raw_rpm, "RAW"
			subter = raw_rpm[1] - 10
			priming = ['0x8E']
			priming.append('0x80')
			priming.append(hex(raw_rpm[0]))
			priming.append(hex(subter))
			priming.append(check_sum_calc(priming))
			for x in range(len(priming)):
				priming[x] = int(priming[x],16)
			#i2c_write_data(priming)
			print priming
			#i2c_write_data([0x8E, 0x80,subter, 0x00, 0xE3])
		'''
			


		### READING DATA!####
	'''
	i2c_write_data([0x8E, 0x81,0x00, 0x1A, 0xD7])##set Fail Speed
	time.sleep(1)
	i2c_write_data([0x8E, 0x82,0x00, 0x01, 0xEF])#Enable fail
	time.sleep(1)
	i2c_write_data([0x8E, 0x81,0x00, 0x02, 0xEF])
	time.sleep(1)
	i2c_write_data([0x8E, 0x81,0x00, 0x1A, 0xD7])
	time.sleep(1)
	i2c_write_data([0x8E, 0x82,0x00, 0x00, 0xF0])	
	'''
	#i2c_write_data([0x8E, 0x80,0x00, 0x00, 0xE3])
	#i2c_read_bytes([0x8E, 0x05, 0x00, 0x00, 0x6D],[0x8F])i2c_read_bytes([0x8E, 5, 0, 0, 0x6D],[0x8F])
	throttle_value = []
	#i2c_write_data([0x8E, 0x81,0x00, 0x1A, 0xD7])##set Fail Speed
	#i2c_write_data([0x8E, 0x82,0x00, 0x01, 0xEF])#Enable fail
	#time.sleep(5)
	#i2c_write_data([0x8E, 0x81,0x00, 0x00, 0xf1])#Write to 0
	#time.sleep(5)
	#i2c_write_data([0x8E, 0x82,0x00, 0x00, 0xF0])#Disable fail
	Failed = False
	i2c_write_data([0x8E, 0x81,0x00, 0x1A, 0xD7])
	while (time.clock() - tmp_clock < 30): 
		#print "here"
		##get throttle value
		#i2c_write_data([0x8E, 0x81,0x00, 0x1A, 0xD7])##set Fail Speed
		#i2c_write_data([0x8E, 0x82,0x00, 0x01, 0xEF])#Enable fail
		#i2c_write_data([0x8E, 0x81,0x00, 0x02, 0xEF])#Write to 0
		#i2c_write_data([0x8E, 0x82,0x00, 0x00, 0xF0])#Disable fail
		#time.sleep(5)
		#i2c_write_data([0x8E, 0x82,0x00, 0x00, 0xF0])##disable fail
		
		priming = ['0x8E']
		priming.append('0x04')
		priming.append('0x00')
		priming.append('0x00')
		priming.append(check_sum_calc(priming))
		for x in range(len(priming)):
			priming[x] = int(priming[x],16)
		val = i2c_read_bytes(priming,[0x8F])
		raw_readable_val = (val[0] << 8)+ val[1]
		readable_val = raw_readable_val/2042.0 *0.2502
		print "%%%%%%%%", readable_val

	
		if readable_val > 0.04 and readable_val < 1:
			i2c_write_data([0x8E, 0x82,0x00, 0x00, 0xF0]) ##disable Fail
			new_val = int(readable_val*100.0)
			priming = ['0x8E']
			priming.append('0x81')
			priming.append('0x00')
			priming.append(hex(new_val))
			priming.append(check_sum_calc(priming))
			for x in range(len(priming)):
				priming[x] = int(priming[x],16)
			throttle_value = list(priming)
			#print "WRITE TO NEW THROTTLE",  readable_val, throttle_value, val, new_val
			#print val
			i2c_write_data(throttle_value)##set Fail Speed
			i2c_write_data([0x8E, 0x82,0x00, 0x01, 0xEF])
			Failed = False
		
		if readable_val < .03:
			Failed = True
			#time.sleep(10)
			#let the fail value do its thing
			#i2c_write_data([0x8E, 0x82,0x00, 0x01, 0xEF])
			print "DONT DO ANYTHING",  readable_val, throttle_value, val
			#i2c_write_data(throttle_value)
			#i2c_write_data([0x8E, 0x82,0x00, 0x01, 0xEF])
		
		#print "%%%%%%%%", readable_val
		
		count += 1
		print count	
		row=[]
		for key,values in read_register_table_tmp.iteritems():
			priming = ['0x8E']
			priming.append(hex(key))
			priming.append('0x00')
			priming.append('0x00')
			priming.append(check_sum_calc(priming))
			for x in range(len(priming)):
				priming[x] = int(priming[x],16)
			val = i2c_read_bytes(priming,[0x8F])
			#time.sleep(.01)
			raw_readable_val = (val[0] << 8)+ val[1]

			if values in read_scale_table.keys():
				
				#print key, values
				
				#i2c_write_data([0x8E, 0x80,0x0F, 0x00, 0xE3])
				#time.sleep(1)
				#i2c_read_bytes([0x8E, 0x05, 0x00, 0x00, 0x6D],[0x8F])
				#i2c_read_bytes([0x8E, 5, 0, 0, 0x6D],[0x8F])
				#

				readable_val = raw_readable_val/2042.0 * read_scale_table[values][0] 
				tmp = [values, readable_val]
				row.append(tmp)
			else:
				row.append([values,val]) 
			#if key == 5:
			print values, readable_val, "RAW", val 
			
			CSV.writerow(row)
		

	'''
	i2c_write_data([0x8E, 0x80,0x00, 0x00,0xF2])
		
	i2c_write_data([0x8E, 0x80,0x0F, 0x00, 0xE3])
	time.sleep(5)		
	i2c_read_bytes([142, 5, 0, 0, 109],[0x8F]), '1!!!'
	i2c_write_data([0x8E, 0x80,0x00, 0x00,0xF2])
	'''


	
	#i2c_write_data([0x8E, 0x82,0x00, 0x00, 0xF0])#Disable fail
	
	print "Reset Bus Pirate to user terminal: "
	if i2c.resetBP():
		print "OK."
	else:
		print "failed."
		sys.exit()
		
