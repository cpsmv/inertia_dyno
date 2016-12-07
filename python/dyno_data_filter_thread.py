import threading, time
from numpy import zeros as np_zeros, sum as np_sum, ones as np_ones, array as np_array

class dyno_data_filter_thread(threading.Thread):

	def __init__(self, my_rpm_unfilt_q, my_rpm_res, my_torque_res, my_thread_timing):

		super().__init__(name="dyno data filter thread")

		# keep track of when thread it active
		self.active = threading.Event()

		# store passed in parameters
		self.rpm_unfilt_q = my_rpm_unfilt_q
		self.rpm_res = my_rpm_res
		self.torque_res = my_torque_res
		self.thread_timing = my_thread_timing

		# filtering variables
		self.filter_sample_freq = 1000 # Hz, hardcoded into Arduino
		self.filter_sample_period = 1/self.filter_sample_freq # s

		# low pass filter variables
		self.filter_length_M = 51

		# smooth noise-robust differentiator - N=9, n=4 (exact on polynomials up to x**4)
		# see dyno manual for link for more polynomials and differentiation
		self.diff_num = np_array([2,1,-16,-27,0,27,16,-1,-2])
		self.diff_denom = 96*self.filter_sample_period 

		# mechanical information
		self.moment_of_inertia = 50E-3


	def start(self):

		print(super().getName() + " is starting.")
		self.active.set()
		super().start()


	def run(self):

		# define filter vectors (keep track of old values) of size M
		rpm_vector = np_zeros(self.filter_length_M)
		rpm_filt_vector = np_zeros(self.filter_length_M)
		torque_vector = np_zeros(self.filter_length_M)

		# loop forever until thread is terminated
		while self.active.isSet():

			# get the current raw rpm from the hall effect thread
			new_rpm = self.rpm_unfilt_q.get()
			# only proceed if a new RPM value was successfully retrieved from the queue
			if new_rpm != None:
				rpm_vector[0] = new_rpm
				# filter the raw rpm using a moving average filter
				rpm_filt_vector[0] = np_sum(rpm_vector)/self.filter_length_M
				# take the derivative of the filtered rpm data using a smooth noise differentiator
				angular_accel = np_sum(self.diff_num*rpm_vector[0:self.diff_num.size])/self.diff_denom
				# real time torque equals the dyno's moment of inertia times its angular acceleration 
				torque_vector[0] = self.moment_of_inertia*angular_accel
				# filter the torque data (extremely noisy) using a moving average filter
				torque_filt = np_sum(torque_vector)/self.filter_length_M

				# update the rpm and torque shared resources (consumed by data log thread and webserver asynchronous loop)
				self.rpm_res.put(rpm_filt_vector[0])
				self.torque_res.put(torque_vector[0])

				# shift vector values
				rpm_vector[1:] = rpm_vector[:rpm_vector.size-1]
				rpm_filt_vector[1:] = rpm_filt_vector[:rpm_filt_vector.size-1]
				torque_vector[1:] = torque_vector[:torque_vector.size-1]

		# sleep thread according to set timing
		#time.sleep(self.thread_timing)


	def join(self):

		print(super().getName() + " is terminating.")
		self.active.clear()
		super().join(timeout=None)
