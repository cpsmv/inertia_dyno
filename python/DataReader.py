import time, asyncio, websockets, random
from serial_thread import serial_thread
from threading import Lock


sample_freq = 50 # Hz
sample_period = 1/sample_freq # s

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
			#print("Did not get a value from " + str(lock))
			return None

	def put(self, val):
		try:
			self._lock.acquire(timeout=self._timeout)
			self._value = val
			self._lock.release()
		except:
			#print("Did not put " + val + " into " + str(lock))
			pass

#------------------------------------------------------------------------
#   W E B S O C K E T   S H A R E D   R E F S
#------------------------------------------------------------------------
speed_ref = shared_ref(Lock(), 1E-5)
torque_ref = shared_ref(Lock(), 1E-5)
time_ref = shared_ref(Lock(), 1E-5)

async def data_transmission(websocket, path):

	data = "f%d" % sample_freq
	await websocket.send(data)

	while True:
		data = "s%.0f" % speed_ref.get()
		await websocket.send(data)
		data = "T%.1f" % torque_ref.get()
		await websocket.send(data)
		data = "t%.2f" % time_ref.get()
		await websocket.send(str(data))
		await asyncio.sleep(sample_period)

#------------------------------------------------------------------------------------------------------------------
#   M A I N  
#------------------------------------------------------------------------------------------------------------------
if __name__ == '__main__':

	# launch serial thread
	ser_thread = serial_thread(115200, 200E-6, sample_freq, speed_ref, torque_ref, time_ref)
	ser_thread.start()

	# launch websocket and run it forever
	server = websockets.serve(data_transmission, '127.0.0.1', 8001)
	loop = asyncio.get_event_loop()
	loop.run_until_complete(server)
	loop.run_forever()



					

