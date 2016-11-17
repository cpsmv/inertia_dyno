from threading import Lock

#------------------------------------------------------------------------------------------------------------------
#   S H A R E D   R E F E R E N C E   C L A S S
#------------------------------------------------------------------------------------------------------------------
class shared_ref():

	def __init__(self, my_lock, my_timeout, my_val=None): 
		self._lock = my_lock
		self._timeout = my_timeout
		self._value = my_val

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
