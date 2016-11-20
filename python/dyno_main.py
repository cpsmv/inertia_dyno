import time, asyncio, websockets, random
from hall_effect_thread import hall_effect_thread
from thread_safe import shared_ref
from threading import Lock

#------------------------------------------------------------------------------------------------------------------
#   D Y N O   P A R A M E T E R S
#------------------------------------------------------------------------------------------------------------------

#------------------------------------------------------------------------
#   T H R E A D   S A F E   R E F E R E N C E S
#------------------------------------------------------------------------
speed_r = shared_ref(Lock(), 1E-5)
torque_r = shared_ref(Lock(), 1E-5)
time_r = shared_ref(Lock(), 1E-5)
sample_freq_r = shared_ref(Lock(), 1E-5)

websocket_update_freq = 50

async def data_transmission(websocket, path):

    data = "f%d" % websocket_update_freq
    await websocket.send(data)

    while True:
        data = "s%.0f" % speed_r.get()
        await websocket.send(data)
        data = "T%.1f" % torque_r.get()
        await websocket.send(data)
        data = "t%.2f" % time_r.get()
        await websocket.send(str(data))
        await asyncio.sleep(1/websocket_update_freq)

#------------------------------------------------------------------------------------------------------------------
#   M A I N  
#------------------------------------------------------------------------------------------------------------------
if __name__ == '__main__':

    # initialize sample frequency to 5Hz
    sample_freq_r.put(5)

    # define and launch hall effect thread
    hall_eff_thread = hall_effect_thread(115200, 50E-3, sample_freq_r, speed_r, torque_r, time_r)
    hall_eff_thread.start()

    # get an asyncio loop object
    loop = asyncio.get_event_loop()
    # define a websocket
    server = websockets.serve(data_transmission, '127.0.0.1', 8001)
    # launch the websocket in the asyncio loop
    loop.run_until_complete(server)
    # run the asyncio loop forever until it is interrupted (Ctrl-C keyboard interrupt, for example)
    try:
        loop.run_forever()
    except:
        print('\nTerminating asyncio loop.')
        loop.close()



                    

