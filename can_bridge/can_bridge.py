from datetime import datetime
import pyuavcan_v0, time, math
import numpy as np

class fifo_manager:
    def __init__(self, fifo_path):
        self.filtersize = 10

        self.meassurements_voltage = [0] * self.filtersize
        self.meassurements_current = [0] * self.filtersize


        try:
            os.mkfifo(fifo_path)
        except:
            pass
        try:
            self.fifo = open(fifo_path, "w")
            # time.sleep(3)
        except Exception as e:
            print (e)
            sys.exit()


    def get_filtered_voltage(self, new_voltage):
        self.meassurements_voltage.append(new_voltage)
        self.meassurements_voltage.pop(0)
        return sum(self.meassurements_voltage) / self.filtersize
        
    def get_filtered_current(self, new_current):
        self.meassurements_current.append(new_current)
        self.meassurements_current.pop(0)
        return sum(self.meassurements_current) / self.filtersize

    def format_data(self, data):
        return f"{data[0]},{data[1]},{data[2]},{data[3]},{data[4]},{data[5]}"

    def close_fifo(self):
        try:
            print("---- closing fifo ---- ")
            self.fifo.close()
            os.unlink(self.fifo)
        except:
            print("closing fifo failed")

    def send_data(self, data):
        self.fifo.write(str(data))
        self.fifo.flush()

class can_manager:
    def __init__(self, esc1_manager):
        pyuavcan_v0.load_dsdl('/home/ubuntu/prediction_model_ws/can_bridge')
        print("dsdl loaded")

        self.last_T = None
        self.last_throttle = 1000
        self.esc1_manager = esc1_manager

        self.node = pyuavcan_v0.make_node(self.get_device_path(), node_id = 10, bitrate = 1000000, baudrate=1000000)
        print("node made")

        # Initializing a dynamic node ID allocator.
        # This would not be necessary if the nodes were configured to use static node ID.
        self.node_monitor = pyuavcan_v0.app.node_monitor.NodeMonitor(self.node)
        self.dynamic_node_id_allocator = pyuavcan_v0.app.dynamic_node_id.CentralizedServer(self.node, self.node_monitor)
        print("id centrulized")

        # Waiting for at least one other node to appear online (our local node is already online).
        while len(self.dynamic_node_id_allocator.get_allocation_table()) <= 1:
            print('Waiting for other nodes to become online...')
            self.node.spin(timeout=1)

        # This is how we invoke the publishing function periodically.
        # self.node.periodic(0.01, self.publish_throttle_setpoint)

        # Printing ESC status message to stdout in human-readable YAML format.
        # node.add_handler(uavcan.equipment.esc.Status, lambda msg: print(uavcan.to_yaml(msg)))
        self.node.add_handler(pyuavcan_v0.equipment.esc.Status, lambda msg: self.process_message_status(pyuavcan_v0.to_yaml(msg)))
        self.node.add_handler(pyuavcan_v0.equipment.esc.RawCommand, lambda msg: self.process_message_command(pyuavcan_v0.to_yaml(msg)))
        print("end initializer")

    def get_device_path(self):
        return '/dev/serial/by-id/usb-Zubax_Robotics_Zubax_Babel_30003D000757424E3430302000000000-if00'
        # return '/dev/serial/by-id/usb-Silicon_Labs_CP2102N_USB_to_UART_Bridge_Controller_bc97f94c52c5e711b9298568f41b81de-if00-port0'
 

    def process_message_command(self, msg):
        self.last_throttle = int(msg.split(',')[2])

    def process_message_status(self, msg):
        if "esc_index: 3" in msg:
            t, v, c, rpm, temp = 0, 0, 0, 0 ,0
            for line in msg.split('\n'):
                splitted_line = line.split(':')
                if 'ts_mono' in line:
                    t = float(line.split('ts_mono=')[1].split('  ts_real=')[0])
                elif 'voltage' in line:
                    v = float(splitted_line[1])
                elif 'current' in line:
                    c = float(splitted_line[1])
                elif 'temperature' in line:
                    temp = float(splitted_line[1])
                elif 'rpm' in line:
                    rpm = float(splitted_line[1])

            v = rnn_esc1.get_filtered_voltage(v)
            c = rnn_esc1.get_filtered_current(c)


            dt = 0.01
            if not self.last_T == None:
                dt = t - self.last_T
            self.last_T = t
            self.esc1_manager.send_data(rnn_esc1.format_data([self.last_throttle, dt, rpm, v, c, temp]))


    def publish_throttle_setpoint(self):
        
        commands = [1000, 0, 0, 0]
        message = pyuavcan_v0.equipment.esc.RawCommand(cmd=commands)
        self.node.broadcast(message)



if __name__ == '__main__':
    rnn_esc1 = fifo_manager("../rnn/esc1_data")
    cm = can_manager(rnn_esc1)
    
    try:
        cm.node.spin()
    except KeyboardInterrupt:
        pass

rnn_esc1.close_fifo()
