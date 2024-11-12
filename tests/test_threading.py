import threading
import time

class test(object):
    def __init__(self, param, a):
        self.a = a
        self.thread = threading.Thread(target=self.main_thread, args = (param,))

    def start(self):
        self.thread.start()

    def main_thread(self, name):
        time.sleep(1)
        print("thread %d" %name)
        time.sleep(1)
        print("thread : " + self.a)


def main():
    th = test(1, 'a')
    th.start()

    th_2 = test(2,'b')
    th_2.start()



if __name__ == '__main__':
    main()