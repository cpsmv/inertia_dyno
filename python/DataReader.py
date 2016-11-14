import serial, csv, sys, time, asyncio, websockets
from serial_thread import serial_thread


sample_freq = 50 # Hz
sample_period = 1/sample_freq # s

#------------------------------------------------------------------------------------------------------------------
#   S H A R E D   R E F E R E N C E   C L A S S
#------------------------------------------------------------------------------------------------------------------
class shared_ref():

	def __init__(self, val): 
		self._value = val

	def get(self): 
		return self._value

	def put(self, val):
		self._value = val

speed_ref = shared_ref(0)
torque_ref = shared_ref(0)
time_ref = shared_ref(0)

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
	ser_thread = serial_thread(115200, 1, sample_freq, speed_ref, torque_ref, time_ref)
	ser_thread.start()

	# launch websocket and run it forever
	server = websockets.serve(data_transmission, '127.0.0.1', 8001)
	loop = asyncio.get_event_loop()
	loop.run_until_complete(server)
	loop.run_forever()



					

