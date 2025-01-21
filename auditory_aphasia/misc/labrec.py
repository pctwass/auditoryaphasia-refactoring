import socket

def send_lab_recorder(commands, host="localhost", RCS_PORT=22345, fname_dict=None):
    import socket
    s = socket.create_connection((host, RCS_PORT))

    if commands == 'filename':
        if fname_dict is None:
            raise ValueError("fname_dict is required.")
        keys = fname_dict.keys()
        for key in keys:
            if fname_dict[key] is not None:
                commands += " {" + key + ":" + fname_dict[key] + "}"
    commands += "\n"
    s.sendall(commands.encode())
    s.close()

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument('commands')
    parser.add_argument('--root')
    parser.add_argument('--template')
    parser.add_argument('--task')
    parser.add_argument('--run')
    parser.add_argument('--participant')
    parser.add_argument('--session')
    parser.add_argument('--acquisition')
    parser.add_argument('--modality')
    
    args = parser.parse_args()
    
    import sys

    fname_dict = None
    if args.commands == 'filename':
        fname_dict = dict()
        for key in args.__dict__.keys():
            if key != 'commands':
                fname_dict[key] = args.__dict__[key]
    
    send_lab_recorder(args.commands, fname_dict=fname_dict)