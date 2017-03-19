import threading, serial, glob, time, random

class tpu_thread(threading.Thread):

	def __init__(self, my_baud, my_ser_timeout, my_rpm_unfilt_q): # *****************REVIEW LATER with Pink*****************

		super().__init__(name="peripheral can thread")

		# keep track of when thread it active
		self.active = threading.Event()

		# store passed in parameters
		self.baud = my_baud
		self.ser_timeout = my_ser_timeout
		self.rpm_unfilt_q = my_rpm_unfilt_q

		# intialization of important variables
		self.ser_port = None
		self.handshake_wait_interval = 2 # seconds


	def start(self):

		print(super().getName() + " is starting.")
		self.active.set()
		super().start()


	def run(self):

		# loop forever until thread is terminated
		while self.active.isSet():
			
			# find a serial port if one hasn't been found yet
			if self.ser_port == None:
				# find all available serial ports in the file system
				port_names = self.find_serial_ports()
				if not(port_names == None):
					for port in port_names:
						print('Initializing',super().getName(), 'serial port at', port)
						# open the serial port under consideration
						self.ser_port = serial.Serial(port, self.baud, timeout=self.ser_timeout)
						# wait for Arduino to initialize its Serial stuff before handshaking
						time.sleep(2000E-3)
						# begin the handshake process with the Arduino
						self.ser_port.write('handshake_type\n'.encode('ascii'))
						print('Handshaking with tpu arduino.')
						# wait for the Arduino to send back its type (eg, (hall_effect) "tpu" or (peripheral_can)"can")
						handshake_success = False
						handshake_wait_init = time.time()
						# only wait for handshaking to complete for a couple seconds 
						while time.time() - handshake_wait_init < self.handshake_wait_interval:
							ser_in = None
							try:
								ser_in = self.ser_port.readline().decode('ascii')[:-2]
							except:
								pass
							# check to see if the correct Arduino responded 
							if ser_in == 'can':
								# if it did, keep this serial port and stop looking at the others
								print('Successful handshake with hall effect arduino at '+self.ser_port.name)
								handshake_success = True
								break

						if handshake_success:
							self.ser_port.write('handshake_ok'.encode('ascii'))
							break
						else:
							self.ser_port.close()
							self.ser_port = None

			# only proceed if a serial port has been found
			else:

				# Read a line and the endline character from received string
				line_in = self.ser_port.readline()[:-1].decode('ascii')

				# only continue if the serial port did not timeout and successfully read a line
				if line_in != '':
        
          # capture can message index and data from Arduino
          dataindex = int(line_in[0], 10)
					temp_data = int(line_in[1:2].lower(), 16)	# 16 = number system base (hex)
          # Add if statements for different multipliers and adders *****************REVIEW LATER*****************
					# Apply CAN data multiplier and adder
          can_data[dataindex] = temp_data*multiplier+adder

					print(dataindex, can_data[dataindex])
					
					self.can_data.put(can_data) # *****************REVIEW LATER with Pink*****************

				# if the serial port timed-out before reading a line, assume current RPM is 0
        # *****************REVIEW LATER with Pink***************** What should we do?
				else: 
					self.rpm_unfilt_q.put(0)
					continue
				

	def join(self):

		print(super().getName() + " is terminating.")
		self.active.clear()

		if not(self.ser_port == None):
			# send out a message to the hall effect arduino to reboot itself
			self.ser_port.write('reboot_now\n'.encode('ascii'))
			print('Rebooting tpu arduino.')
			# close serial port, if one is active
			self.ser_port.close()

		super().join(timeout=None)



	def scan_all(self):
		"""scan for available ports. prints out list, and returns a list of tuples (num, name)"""
		available = []
		for i in range(256):
			try:
				s = serial.Serial(i)
				available.append( (i, s.portstr))
				print ("(%d) %s" % (i, s.portstr))
				s.close()   # explicit close 'cause of delayed GC in java
			except serial.SerialException:
				pass
		return available


	def find_serial_ports(self):

		serial_port = None
		ports_avail = glob.glob('/dev/ttyA*')
		return ports_avail
