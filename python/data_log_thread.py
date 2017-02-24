import threading, time

class data_log_thread(threading.Thread):

	def __init__(self, my_sample_freq, my_thread_timing, my_rpm_res, my_torque_res, my_test_time_res):

		super().__init__(name="data log thread")

		# keep track of when thread it active
		self.active = threading.Event()

		# store passed in parameters
		self.sample_freq = my_sample_freq
		self.thread_timing = my_thread_timing
		self.test_time_res = my_test_time_res
		self.rpm_res = my_rpm_res
		self.torque_res = my_torque_res

		# sleep the thread every 1 us, effectively updating the test time about that fast
		self.thread_block_period = 1E-6 

	def start(self):

		print(super().getName() + " is starting.")
		self.active.set()
		super().start()


	def run(self):

		f = open('out.csv', 'w')

		# time variables
		init_test_time = time.time()
		curr_test_time = 0
		last_test_time = 0

		while self.active.isSet():

			# update the test time
			curr_test_time = time.time()-init_test_time
			# update time shared resource (used by data filter to ensure accurate timing)
			self.test_time_res.put(curr_test_time)

			# check if it is time to store data (also grab the most up-to-date data sampling time, updated by the webserver loop)
			if curr_test_time - last_test_time > self.sample_freq:
				# store data

				# write to CSV in this loop??
				
				# store current test time so that data logging stores at correct rate
				last_test_time = curr_test_time

			# sleep the thread according to timing set above
			time.sleep(self.thread_timing)
				
		f.close()


	def join(self):

		print(super().getName() + " is terminating.")
		self.active.clear()
		super().join(timeout=None)
