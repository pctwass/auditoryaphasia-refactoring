import pylsl
import time

ENABLE_STREAM_INLET_RECOVER = True
STREAM_RESOLVE_TIMEOUT_MS = 100


def init_LSL_inlet(
        stream_name : str = None, 
        stream_type : str = None, 
        stream_name_keyword : str = None, 
        await_stream : bool = False, 
        timeout : int | float = STREAM_RESOLVE_TIMEOUT_MS
) -> tuple[pylsl.StreamInfo, pylsl.StreamInlet]:
    if await_stream:
        stream = resolve_stream_awaited(stream_name, stream_type, stream_name_keyword, timeout)
    else:
        stream = resolve_stream(stream_name, stream_type, stream_name_keyword)
    inlet = pylsl.StreamInlet(
        stream, recover=ENABLE_STREAM_INLET_RECOVER
    )
    return inlet, stream


def resolve_stream(stream_name : str = None, stream_type : str = None, stream_name_keyword : str = None) -> tuple[pylsl.StreamInfo, pylsl.StreamInlet]:
    if stream_name and stream_type:
        streams = pylsl.resolve_stream('name', stream_name, 'type', stream_type)
    elif stream_name:
        streams = pylsl.resolve_stream('name', stream_name)
    elif stream_type:
        streams = pylsl.resolve_stream('name', stream_name, 'type', stream_type)
    else:
        raise Exception(f"Could not resolve stream, neither the stream name nor type was provided")

    if not streams:
        except_message : str = f"No stream could be found given the following criteria:"
        if stream_name:
            except_message += f" name {stream_name}"
        if stream_type:
            except_message += f" type {stream_type}"
        raise Exception(f"{except_message}.")
    
    if not stream_name and stream_name_keyword:
        for stream in streams:
            if  stream_name_keyword in stream.name():
                return stream
        raise Exception(f"Could not find a stream of type {stream_type} with a name containing the keyword: {stream_name_keyword}")

    return streams[0]


def resolve_stream_awaited(stream_name : str, stream_type : str = None, stream_name_keyword : str = None, timeout : int | float = STREAM_RESOLVE_TIMEOUT_MS) -> pylsl.StreamInfo:
    start_time = time.time()
    while True:
        try:
            return resolve_stream(stream_name, stream_type, stream_name_keyword)
        except Exception as ex:
            time_passed = (time.time() - start_time) * 1000 # convert to ms
            if time_passed > timeout:
                raise


def get_LSL_channel_names(inlet : pylsl.StreamInlet) -> enumerate[str]:
    channel_names = list()

    info = inlet.info()
    ch = info.desc().child("channels").child("channel")
    for k in range(info.channel_count()):
        channel_names.append(ch.child_value('label'))
        ch = ch.next_sibling()
    
    return channel_names