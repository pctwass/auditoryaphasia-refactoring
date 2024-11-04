import pylsl
import logging
import time

ENABLE_STREAM_INLET_RECOVER = True
STREAM_RESOLVE_TIMEOUT_MS = 100


def init_LSL_inlet(stream_name : str, stream_type : str = None, await_stream : bool = False, timeout : int | float = STREAM_RESOLVE_TIMEOUT_MS) -> tuple[pylsl.StreamInfo, pylsl.StreamInlet]:
    if await_stream:
        stream = resolve_stream_awaited(stream_name, stream_type, timeout)
    else:
        stream = resolve_stream(stream_name, stream_type)
    inlet = pylsl.StreamInlet(
        stream, recover=ENABLE_STREAM_INLET_RECOVER
    )
    return inlet, stream


def resolve_stream(stream_name : str, stream_type : str = None) -> tuple[pylsl.StreamInfo, pylsl.StreamInlet]:
    if stream_type is None or stream_type.strip() == "":
        streams = pylsl.resolve_stream('name', stream_name)
    else:
        streams = pylsl.resolve_stream('name', stream_name, 'type', stream_type)

    if not streams:
        except_message : str = f"No stream could be found with the name {stream_name}."
        if stream_type is not None:
            except_message = stream_type.strip('.')
            except_message += f" and of type {stream_type}."

        raise Exception(f"No stream could be found with the name {stream_name} and of type ")

    return streams[0]


def resolve_stream_awaited(stream_name : str, stream_type : str = None, timeout : int | float = STREAM_RESOLVE_TIMEOUT_MS) -> pylsl.StreamInfo:
    start_time = time.time()
    while True:
        try:
            return resolve_stream(stream_name, stream_type)
        except Exception as ex:
            time_passed = (time.time() - start_time) * 1000 # convert to ms
            if time_passed > timeout:
                raise