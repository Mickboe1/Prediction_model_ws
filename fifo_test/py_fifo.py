import sys, os, time
path = "esc1_data"

data = [1500, 0.1, 16.7500, 0.0238, 1944, 299.500]

def format_data(data):
    return f"{data[0]},{data[1]},{data[2]},{data[3]},{data[4]},{data[5]}"




class fifo_manager:
    def __init__(self, fifo_path):
        try:
            os.mkfifo(fifo_path)
        except:
            pass
        try:
            self.fifo = open(fifo_path, "w")
            time.sleep(3)
        except Exception as e:
            print (e)
            sys.exit()

    def close_fifo(self):
        try:
            self.fifo.close()
            os.unlink(self.fifo)
        except:
            print("closing fifo failed")

    def send_data(self, data):
        self.fifo.write(str(data))
        self.fifo.flush()



rnn_esc1 = fifo_manager(path)
for i in range(500):
    print(i)
    rnn_esc1.send_data(str(i) +format_data( data))
    time.sleep(0.01)
