import time
from logging import getLogger
logger = getLogger('pyscab.'+__name__)

def get_required_time(plans, data):
    end_times = list()
    for plan in plans:
        end_time = data.get_length_by_id(plan[1])
        end_time += plan[0]
        end_times.append(end_time)
    return max(end_times)

class StimulationController(object):

    def __init__(self, AudioHardwareController, marker_send, correct_latency = True, time_tick = 0.0001, share=0):
        """
        class for playing stimulating plan.

        Attributes
        ----------
        AudioHardwareController : An instance of pyscab.AudioHardwareController class
        marker_send : reference to a function
            A reference to function for send a marker
        mode : str {'serial', 'pararell'} default = 'serial'
            If it's set to 'pararell', it can be controll from parent process.
        time_tick : float, default=0.0001
            pause between each loop in play() function. In terms of real time, it should be reduced.
            However, it also caused intence compulational load.
        share : int or instance of multiprocessing[0] class
            0 : stopped
            1 : running
            When mode is set to 'serial', type of share is Boolean.
            When mode is set to 'pararell', type of share is an instance of multiprocessing.Array class.

            share[0] is used for sharing runnin status.
            When it's working in pararell mode, it will be stop playing immediate after share is changed to 0.
            e.g., when you are presenting stimulus in online BCI application with dynamic stopping,
            you need to stop playing when it's triggered. In that case, you need to set mode to pararell and use share variable.

            share[1] is used for sharing current marker value.

        """
        self.ahc = AudioHardwareController
        self.time_tick = time_tick
        self.share = share
        self.marker_send = marker_send
        logger.info("time_tick for Stimulation Controller was set to %s", str(self.time_tick))