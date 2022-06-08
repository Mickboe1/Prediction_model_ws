from datetime import datetime
from re import L
from more_itertools import last
import pyuavcan_v0, time, math
import tensorflow as tf
from tensorflow.keras import layers, models
import keras.backend as K
import numpy as np

class model_manager:
    def __init__(self) -> None:
        self.last_throttle = 0
        self.last_T = None
        self.model = self.create_model_rnn_0p181(n_historical=5)
        self.n_historical = 5
        self.data = []
        self.last_prediction_set = False
        self.last_prediction = None
        for i in range(self.n_historical):
            # initialize Throti, DTi-1, RPMi-1, Vi-1, Ci-1, TEMPi-1
            self.data.append([0,0,0,0,0,0])
                # data.append(float(line_data[6]))  # THROTTLE[i]
                # data.append(float(prev_line_data[1]))  # DT_i-1
                # data.append(float(prev_line_data[2]))  # RPM_i-1
                # data.append(float(prev_line_data[3]))  # V_i-1
                # data.append(float(prev_line_data[4]))  # C_i-1
                # data.append(float(prev_line_data[5]))  # TEMP_i-1

    def push_data(self, T, RPM, V, C, Temp):
        Dt = 0.1
        if not self.last_T == None:
            Dt = T - self.last_T
        self.last_T = T

        newdata = []
        newdata.append(self.last_throttle)
        newdata.append(Dt)
        newdata.append(RPM)
        newdata.append(V)
        newdata.append(C)
        newdata.append(Temp)
        self.data.pop(0)
        self.data.append(newdata)

    def set_throttle(self, throttle):
        self.last_throttle = throttle

    def get_prediction_data(self):
        return np.array([self.data])


    def get_rnn_model_file_location(self):
        return "rnn_model_files/checkpoint.ckpt"

    def get_lstm_model_file_location(self):
        return "lstm_model_files/checkpoint.ckpt"

    def euclidean_distance_loss(y_true, y_pred):
        """
        Euclidean distance loss
        https://en.wikipedia.org/wiki/Euclidean_distance
        :param y_true: TensorFlow/Theano tensor
        :param y_pred: TensorFlow/Theano tensor of the same shape as y_true
        :return: float
        """ 
        weights = [0.3, 0.3, 0.3, 0.1] #RPM, V, C, T
        return K.sqrt(K.mean(K.square((y_pred - y_true)*weights), axis=-1))

    def create_model_rnn_0p181(self, n_historical):
        model = models.Sequential()
        model.add(layers.SimpleRNN(units=48, input_shape = (n_historical,6), activation='selu'))
        model.add(layers.Dense(units=4, activation="linear"))


        opt = tf.keras.optimizers.Adam(
            learning_rate=0.15,
            beta_1=0.9,
            beta_2=0.999,
            epsilon=1e-07,
            amsgrad=False,
            name="Adam")
        
        
        model.compile(optimizer = opt, 
                    loss = self.euclidean_distance_loss)

        checkpoint_path = self.get_rnn_model_file_location()

        try:
            model.load_weights(checkpoint_path)
            # print("Succesfully loaded checkpoint file.")
        except:
            print("No models exists, creating new one")

        return model


    def create_model_lstm_0p195(self, n_historical):
        model = models.Sequential()
        model.add(layers.LSTM(units=64, input_shape = (n_historical,6), activation='selu'))
        model.add(layers.Dense(units=4, activation="linear"))


        opt = tf.keras.optimizers.Adam(
            learning_rate=0.15,
            beta_1=0.9,
            beta_2=0.999,
            epsilon=1e-07,
            amsgrad=False,
            name="Adam")
        
        
        model.compile(optimizer = opt, 
                    loss = self.euclidean_distance_loss)

        checkpoint_path = self.get_lstm_model_file_location()

        try:
            model.load_weights(checkpoint_path)
            # print("Succesfully loaded checkpoint file.")
        except:
            print("No models exists, creating new one")

        return model

    def process_data(self):
        self.last_prediction = self.model.predict(self.get_prediction_data())
        self.last_prediction_set = True
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

        with open(self.output_file, "a") as output:
            output.write("{0},{1},{2},{3},{4},{5}\n".format(self.last_throttle, dt, rpm, v, c, temp))

        # self.mm.push_data(t,rpm, v, c, temp)
        # if self.mm.last_prediction_set:
        #     m_pow = v*c
        #     p_pow = self.mm.last_prediction[0][1]*self.mm.last_prediction[0][2]
        #     normalized_rpm_diff = (self.mm.last_prediction[0][0] - rpm) / self.mm.last_prediction[0][0]
        #     normalized_pow_diff = (p_pow - m_pow) / p_pow
        #     normalized_temp_diff = (self.mm.last_prediction[0][3] - temp) / self.mm.last_prediction[0][3]
        #     with open(self.output_file, "a") as output:
        #         output.write("{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},{12}".format(rpm,v,c,temp,
        #             self.mm.last_prediction[0][0],self.mm.last_prediction[0][1],self.mm.last_prediction[0][2],self.mm.last_prediction[0][3],
        #             m_pow, p_pow, normalized_rpm_diff,normalized_pow_diff, normalized_temp_diff))
        #         output.write('\n')
        # self.mm.process_data()


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


X = []
# with open("input_ramp_0p005.in", 'r') as input_file:
# with open("input_static.in", 'r') as input_file:
with open("input_step.in", 'r') as input_file:
    data = input_file.readlines()[0].replace("[", "").replace("]", "").replace("\n", "").split(',')
    for data_element in data:
        X.append(float(data_element))



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
