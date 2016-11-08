	def find_serial_ports(self):

		process_serial = None
		serial_port = None
		ports_avail = glob.glob('/dev/tty[A-Za-z]*')
		ser_port = None

		for port in ports_avail:
			try:
				serial_port = serial.Serial(port)
				serial_port.close()
				print("Serial port found: %s" % port)
				# we only want one serial port, so break if one is found
				ser_port = port
				break										
			#except (OSError, serial.SerialException):
			except:
				pass   

		return ser_port