from multiprocessing import Process
import os
import time

def info(title):
    print(title)
    print('module name:', __name__)
    print('parent process:', os.getppid())
    print('process id:', os.getpid())

def f(name):
    info('function f')
    print('hello', name)

def loop(title, cnt):
    #cnt = 0
    print(id(cnt))
    while True:
        print(id(cnt))
        print('%s, elapsed time : %ds' %(title, cnt))
        cnt += 1
        time.sleep(1)

if __name__ == '__main__':
    cnt = 0
    print(id(cnt))
    p1 = Process(target=loop, args=('p1',cnt,))
    p1.start()
    #p1.join() #ここのjoinが結構重要
    time.sleep(3)
    print(cnt)
    print('3s')
    p1.terminate()
    print('terminated')