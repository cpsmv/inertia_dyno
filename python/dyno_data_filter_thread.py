import threading, time, random
from numpy import zeros as np_zeros
from numpy import sum as np_sum
from numpy import ones as np_ones

class dyno_data_filter_thread(threading.Thread):

	def __init__(self, my_raw_rpm_res, my_rpm_res, my_torque_res, my_test_time_res, my_thread_timing):

		super().__init__(name="dyno data filter thread")

		# keep track of when thread it active
		self.active = threading.Event()

		# store passed in parameters
		self.raw_rpm_res = my_raw_rpm_res
		self.rpm_res = my_rpm_res
		self.torque_res = my_torque_res
		self.test_time_res = my_test_time_res
		self.thread_timing = my_thread_timing

		self.filter_length_M = 51
		self.filter_sample_freq = 200 # Hz
		self.filter_sample_period = 1/self.filter_sample_freq # s


		self.moment_of_inertia = 50E-3


	def start(self):

		print(super().getName() + " is starting.\n")
		self.active.set()
		super().start()


	def run(self):

		# define filter vectors (keep track of old values) of size M
		rpm_vector = np_zeros(self.filter_length_M)
		rpm_filt_vector = np_zeros(self.filter_length_M)
		torque_vector = np_zeros(self.filter_length_M)
		# keep track of actually achieved filter sampling time (imprecise due to non realtime threading)
		filter_sample_time = np_ones(400)*self.filter_sample_period

		# keep track of actual filter sampling time (initialize the previous occurrence variable to 0)
		last_filter_time = 0

		# loop forever until thread is terminated
		while self.active.isSet():

			# get the current test time from the data log thread
			curr_test_time = self.test_time_res.get()
			# only proceed if it is time for another sample
			if curr_test_time-last_filter_time > self.filter_sample_period:

				# get the current raw rpm from the hall effect thread
				rpm_vector[0] = self.raw_rpm_res.get()
				# filter the raw rpm using a moving average filter
				rpm_filt_vector[0] = np_sum(rpm_vector)/self.filter_length_M
				# take the derivative of the filtered rpm data using a 2 point finite difference scheme
				angular_accel = (rpm_filt_vector[0]-rpm_filt_vector[1])/self.filter_sample_period
				# real time torque equals the dyno's moment of inertia times its angular acceleration 
				torque_vector[0] = self.moment_of_inertia*angular_accel
				# filter the torque data (extremely noisy) using a moving average filter
				torque_filt = np_sum(torque_vector)/self.filter_length_M

				# store the actually achieved filter sampling time (it's never exactly the desired filter sample period)
				filter_sample_time[0] = curr_test_time-last_filter_time
				#print(np_sum(filter_sample_time)/filter_sample_time.size)

				# update the rpm and torque shared resources (used by data log thread and webserver asynchronous loop)
				self.rpm_res.put(rpm_filt_vector[0])
				self.torque_res.put(torque_filt)

				# shift vector values
				rpm_vector[1:] = rpm_vector[0:rpm_vector.size-1]
				rpm_filt_vector[1:] = rpm_filt_vector[0:rpm_filt_vector.size-1]
				torque_vector[1:] = torque_vector[0:torque_vector.size-1]
				filter_sample_time[1:] = filter_sample_time[0:filter_sample_time.size-1]

				# store current test time so sampling works correctly
				last_filter_time = curr_test_time

			# sleep thread according to set timing
			time.sleep(self.thread_timing)


	def join(self):

		print(super().getName() + " is terminating.")
		self.active.clear()
		super().join(timeout=None)
