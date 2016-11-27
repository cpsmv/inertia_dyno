import time, asyncio, websockets, random
from threading import Lock
from hall_effect_thread import hall_effect_thread
from dyno_data_filter_thread import dyno_data_filter_thread
from data_log_thread import data_log_thread
from thread_safe import shared_res

#------------------------------------------------------------------------------------------------------------------
#   D Y N O   P A R A M E T E R S 
#------------------------------------------------------------------------------------------------------------------

#------------------------------------------------------------------------
#   T H R E A D   S A F E   R E F E R E N C E S
#------------------------------------------------------------------------
raw_rpm_r = shared_res(Lock(), 1E-5)
rpm_r = shared_res(Lock(), 1E-5)
torque_r = shared_res(Lock(), 1E-5)
test_time_r = shared_res(Lock(), 1E-5)
sample_freq_r = shared_res(Lock(), 1E-5)

websocket_update_freq = 50

async def data_transmission(websocket, path):

    data = "f%d" % websocket_update_freq
    await websocket.send(data)

    while True:
        data = "s%.5f" % rpm_r.get()
        await websocket.send(data)
        data = "T%.5f" % torque_r.get()
        await websocket.send(data)
        data = "t%.5f" % test_time_r.get()
        await websocket.send(str(data))
        await asyncio.sleep(1/websocket_update_freq)

#------------------------------------------------------------------------------------------------------------------
#   M A I N  
#------------------------------------------------------------------------------------------------------------------
if __name__ == '__main__':

    # initialize sample frequency to 5Hz
    sample_freq_r.put(5)
    # set thread timing
    thread_update_time = 1E-6

    # define and launch hall effect thread
    hall_eff_thread = hall_effect_thread(115200, 1000E-3, raw_rpm_r)
    hall_eff_thread.start()

    # define and launch data log thread 
    data_log_thread = data_log_thread(sample_freq_r, test_time_r, thread_update_time)
    data_log_thread.start()

    # define and launch dyno data filter thread (check 10 times faster than data log updates time, to ensure precise filter sampling)
    dyno_filt_thread = dyno_data_filter_thread(raw_rpm_r, rpm_r, torque_r, test_time_r, thread_update_time/10)
    dyno_filt_thread.start()

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



                    

