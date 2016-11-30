from threading import Lock, Condition
from queue import Queue

#------------------------------------------------------------------------------------------------------------------
#   S H A R E D   R E S O U R C E   C L A S S
#------------------------------------------------------------------------------------------------------------------
class shared_res():

	def __init__(self, my_timeout, my_val=None): 

		self._timeout = my_timeout
		self._value = my_val
		self._lock = Lock()

	def get(self): 
		try:
			self._lock.acquire(timeout=self._timeout)
			val = self._value
			self._lock.release()
			return val
		except:
			#print("Did not get a value from " + str(self._lock))
			return None

	def put(self, val):
		try:
			self._lock.acquire(timeout=self._timeout)
			self._value = val
			self._lock.release()
		except:
			#print("Did not put " + val + " into " + str(self._lock))
			pass

#------------------------------------------------------------------------------------------------------------------
#   Q U E U E   W I T H   C O N D I T I O N   C L A S S
#------------------------------------------------------------------------------------------------------------------
class queue_c():

	def __init__(self, my_timeout): 

		self._timeout = my_timeout
		self._queue = Queue()
		self._condition = Condition()

	def put(self, data):

		# acquire the condition, ensuring it is the only thread using the queue at the moment
		self._condition.acquire()
		# assume the queue is not full yet
		not_full = True

		# check if the queue is full
		if self._queue.full():
			# wait for the specified timeout, returns True if a consumer takes at least one item from the queue
			not_full = self._condition.wait(self._timeout)

		# only proceed putting data in the queue if the queue is not full
		if not_full == True:
			self._queue.put(data)
			# tell other threads waiting to consume in this queue that it is ready
			self._condition.notify()
			self._condition.release()
		#else:
			#print("Timeout on putting data into the following queue_c:", self)
	#
	#
	#
	def get(self):

		# initialize data empty, and assume the queue is not empty
		data = None
		not_empty = True

		# acquire the thread condition, ensuring it is the only thread using the queue at the moment
		self._condition.acquire()

		# check if the queue is empty
		if self._queue.empty():
			# wait for the specified timeout, returns Turn if a producer adds at least one item to the queue
			not_empty = self._condition.wait(self._timeout)

		# only proceed getting data from queue if the queue is not empty
		if not_empty == True:
			data = self._queue.get()
			# tell other threads waiting to produce in this queue that it is ready
			self._condition.notify()
			self._condition.release()
		#else:
			#print("Timeout on putting data into the following queue:", self)

		return data
