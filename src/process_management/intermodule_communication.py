import time
import json
from pylsl import StreamInfo, StreamOutlet, StreamInlet, resolve_stream


def get_intermodule_communication_inlet(target_module:str, timeout:float=None):
    if timeout is None:
        timeout = float('inf')

    is_found = False
    start = time.time()
    while is_found is False:
        streams = resolve_stream('type', 'Markers')
        for stream in streams:
            if stream.name() == 'IntermoduleCommunication_' + target_module:
                inlet_intermodule = StreamInlet(stream)
                is_found = True
                return inlet_intermodule
        if time.time() - start > timeout:
            break

    if is_found is False:
        raise ValueError("Stream 'IntermoduleCommunication' was not found.")


def create_intermodule_communication_outlet(
    module_name:str, 
    type:str='Markers', 
    channel_count:int=1, 
    nominal_srate:float=0, channel_format:int|str='string', 
    source_id:str=''
) -> StreamOutlet:
    # srate is set to IRREGULAR_RATE when nominal_srate = 0
    info = StreamInfo('IntermoduleCommunication_' + module_name, type, channel_count, nominal_srate, channel_format, source_id)
    outlet = StreamOutlet(info)

    return outlet


def send_cmd_LSL(
    outlet:StreamOutlet, 
    target_module:str, 
    cmd:str, 
    params:dict[str,any]=None
):
    if outlet.channel_count != 4:
        raise ValueError("channel_count of LSL outlet have to be 4.")
    
    params = json.dumps(params)
    outlet.push_sample([target_module, 'cmd', cmd, params])


def send_params_LSL(
    outlet:StreamOutlet, 
    target_module:str, 
    var_name:str, 
    params:dict[str,any]=None
):
    if outlet.channel_count != 4:
        raise ValueError("channel_count of LSL outlet have to be 4.")
    
    params = json.dumps(params)
    outlet.push_sample([target_module, 'params', var_name, params])