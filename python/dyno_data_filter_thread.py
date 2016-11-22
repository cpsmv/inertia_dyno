import threading, time, random
from numpy import zeros as np_zeros
from numpy import sum as np_sum

class dyno_data_filter_thread(threading.Thread):

	def __init__(self, my_raw_rpm_ref, my_rpm_ref, my_torque_ref, my_time_ref):

		super().__init__(name="dyno data filter thread")

		# keep track of when thread it active
		self.active = threading.Event()

		# store passed in parameters
		self.raw_rpm_ref = my_raw_rpm_ref
		self.rpm_ref = my_rpm_ref
		self.torque_ref = my_torque_ref
		self.time_ref = my_time_ref

		self.filter_length_M = 51
		self.filter_freq = 1000 # Hz
		self.filter_period = 1/self.filter_freq # s


		self.moment_of_inertia = 50E-3


	def start(self):

		print(super().getName() + " is starting.\n")
		self.active.set()
		super().start()


	def run(self):

		f = open('out.csv', 'w')

		test_init_time = time.time()
		self.time_ref.put(0)
		last_filter_update_time = 0

		rpm_vector = np_zeros(self.filter_length_M)
		rpm_filt_vector = np_zeros(self.filter_length_M)
		torque_vector = np_zeros(self.filter_length_M)
		i = 0

		# loop forever until thread is terminated
		while self.active.isSet():

			curr_test_time = time.time() - test_init_time
			self.time_ref.put(curr_test_time)

			time.sleep(self.filter_period)
			rpm_vector[0] = self.raw_rpm_ref.get()
			#rpm_vector[0] = 0
			rpm_filt_vector[0] = np_sum(rpm_vector)/self.filter_length_M
			angular_accel = (rpm_filt_vector[0]-rpm_filt_vector[1])/self.filter_period
			torque_vector[0] = self.moment_of_inertia*angular_accel

			self.rpm_ref.put(rpm_filt_vector[0])
			self.torque_ref.put(np_sum(torque_vector)/self.filter_length_M)

			rpm_vector[1:] = rpm_vector[0:rpm_vector.size-1]
			rpm_filt_vector[1:] = rpm_filt_vector[0:rpm_filt_vector.size-1]
			torque_vector[1:] = torque_vector[0:torque_vector.size-1]
			last_filter_update_time = curr_test_time

			"""
			if i == 100:
				print(rpm_vector, torque_vector, curr_test_time)
				i = 0
			else:
				i = i + 1
			"""
				
		f.close()


	def join(self):

		print(super().getName() + " is terminating.")
		self.active.clear()
		super().join(timeout=None)
