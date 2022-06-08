from datetime import datetime
import pyuavcan_v0, time, math
import numpy as np

class can_manager:
    def __init__(self, mm, output_file):
        pyuavcan_v0.load_dsdl('/home/mboe/thesis_ws/esc_control_monitor')

        self.input_counter = 0
        self.mm = mm
        self.output_file = output_file
        with open(self.output_file, "a") as output:
                output.write("m_rpm, m_v, m_c, m_temp, p_rpm, p_v, p_c, p_temp, m_pow, p_pow, norm_rpm, norm_pow, norm_temp")
                output.write('\n')

        self.last_T = None
        self.last_throttle = 0

        self.node = pyuavcan_v0.make_node(self.get_device_path(), node_id = 10, bitrate = 1000000, baudrate=1000000)

        # Initializing a dynamic node ID allocator.
        # This would not be necessary if the nodes were configured to use static node ID.
        self.node_monitor = pyuavcan_v0.app.node_monitor.NodeMonitor(self.node)
        self.dynamic_node_id_allocator = pyuavcan_v0.app.dynamic_node_id.CentralizedServer(self.node, self.node_monitor)

        # Waiting for at least one other node to appear online (our local node is already online).
        while len(self.dynamic_node_id_allocator.get_allocation_table()) <= 1:
            # print('Waiting for other nodes to become online...')
            self.node.spin(timeout=1)

        # This is how we invoke the publishing function periodically.
        self.node.periodic(0.01, self.publish_throttle_setpoint)

        # Printing ESC status message to stdout in human-readable YAML format.
        # node.add_handler(uavcan.equipment.esc.Status, lambda msg: print(uavcan.to_yaml(msg)))
        self.node.add_handler(pyuavcan_v0.equipment.esc.Status, lambda msg: self.process_message(pyuavcan_v0.to_yaml(msg)))

    def process_message(self, msg):
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

        dt = 0.01
        if not self.last_T == None:
            dt = t - self.last_T
        self.last_T = t



    def publish_throttle_setpoint(self):
        setpoint = 0
        # print(self.input_counter, X[self.input_counter])
        if self.input_counter < len(X)-1:
            # setpoint = int(1000 * (X[self.input_counter])) #5734 is .7 of the the max thorottle command because this is where the esc caps.
            setpoint = int(5734 * (X[self.input_counter])) #5734 is .7 of the the max thorottle command because this is where the esc caps.
            self.input_counter = self.input_counter + 1

            self.last_throttle = setpoint
            # self.mm.set_throttle(setpoint)
        else:
            raise RuntimeError('end of file') from None
        
        commands = [setpoint, 0, 0, 0]
        message = pyuavcan_v0.equipment.esc.RawCommand(cmd=commands)
        self.node.broadcast(message)

    def get_device_path(self):
        return '/dev/serial/by-id/usb-Silicon_Labs_CP2102N_USB_to_UART_Bridge_Controller_bc97f94c52c5e711b9298568f41b81de-if00-port0'


if __name__ == '__main__':

    mm = model_manager()
    # cm = can_manager(mm, "test_live_5/D4/ramp.csv")
    # cm = can_manager(mm, "test_live_5/D4/static.csv")
    cm = can_manager(mm, "test_live_5/D4/step.csv")
    

    # Running the node until the application is terminated or until first error.
    try:
        cm.node.spin()
    except KeyboardInterrupt:
        pass
