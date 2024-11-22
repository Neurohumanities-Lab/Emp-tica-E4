import socket
import time
import pylsl
import numpy as np
import pandas as pd
from datetime import datetime
import csv
import matplotlib.pyplot as plt 
import matplotlib.animation as animation
from scipy.fft import rfft,rfftfreq
import json
import sys 

# Un-comment the next line of code if sender and connector files are in another directory. And change the "modules" name 
# to your directory.
#sys.path.append("./modules")
#from sender import Sender

# Function to generate CSVs and post them to the ALAS server.
def jsonPost(csvFilePath, value):
    TemporalArray = []

    with open(csvFilePath) as Document:
        data = csv.reader(Document)
        for row in data:
            #print(row[0])
            #print(row[-1])
            TemporalArray.append({ 'datetime': row[0] , value: row[-1] })

    # We post the information with the next instruction.
    #r = requests.post(url, data=json.dumps(file), headers=headers)

    s = Sender()
    s.post_empatica_record(TemporalArray)
    # print(file)
    # #print(r.text)
    # print("-----------\n\n")
    # print(TemporalArray)

def csv2JSON(csvFilePath, jsonFilePath):
    jsonArray = []

    #read csv file
    with open(csvFilePath, encoding='utf-8') as csvf: 
        #load csv file data using csv library's dictionary reader
        csvReader = csv.DictReader(csvf) 

        #convert each csv row into python dict
        for row in csvReader: 
            #add this python dict to json array
            jsonArray.append(row)

    #convert python jsonArray to JSON String and write to file
    with open(jsonFilePath, 'w', encoding='utf-8') as jsonf: 
        jsonString = json.dumps(jsonArray, indent=4)
        jsonf.write(jsonString)

def empatica():
    global BVP_array
    global Acc_array
    global GSR_array
    global Temp_array
    global IBI_array
    global BVP_tuple
    global ACC_tuple
    global GSR_tuple
    global Temp_tuple
    global IBI_tuple
    global Temporal_BVP_array
    global Temporal_GSR_array
    global Temporal_Temp_array
    global Temporal_IBI_array
    global BVP_Graph_value
    global counter
    global x_BVP_val
    global x_GSR_val
    global x_Temp_val
    global x_IBI_val
    global y_BVP_val
    global y_GSR_val
    global y_Temp_val
    global y_IBI_val
    # VARIABLES USED TO STORE & GRAPH DATA
    BVP_array = []
    Acc_array = [] 
    GSR_array = []
    Temp_array = []
    IBI_array = []
    BVP_tuple = ()
    ACC_tuple = ()
    GSR_tuple = ()
    Temp_tuple = ()
    IBI_tuple = ()
    Temporal_BVP_array = []
    Temporal_GSR_array = []
    Temporal_Temp_array = []
    Temporal_IBI_array = []
    BVP_Graph_value = None
    counter = 0 # Used to pop values from arrays to perform a "moving" graph.
    x_BVP_val = []
    x_GSR_val = []
    x_Temp_val = []
    x_IBI_val = []
    y_BVP_val = []
    y_GSR_val = []
    y_Temp_val = []
    y_IBI_val = []

    # SELECT DATA TO STREAM
    acc = True      # 3-axis acceleration
    bvp = True      # Blood Volume Pulse
    gsr = True      # Galvanic Skin Response (Electrodermal Activity)
    tmp = True      # Temperature
    ibi = True

    serverAddress = '127.0.0.1'  #'FW 2.1.0' #'127.0.0.1'
    serverPort = 28000 #28000 #4911
    bufferSize = 4096
    # The wristband with SN A027D2 worked here with deviceID 8839CD
    deviceID = '8839CD' #'834ACD' #'8839CD' #'1451CD' # 'A02088' #'A01FC2'

    def connect():
        global s
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)

        print("Connecting to server")
        s.connect((serverAddress, serverPort))
        print("Connected to server\n")

        print("Devices available:")
        s.send("device_list\r\n".encode())
        response = s.recv(bufferSize)
        print(response.decode("utf-8"))

        print("Connecting to device")
        s.send(("device_connect " + deviceID + "\r\n").encode())
        response = s.recv(bufferSize)
        print(response.decode("utf-8"))

        print("Pausing data receiving")
        s.send("pause ON\r\n".encode())
        response = s.recv(bufferSize)
        print(response.decode("utf-8"))
        
    connect()

    time.sleep(1)

    def suscribe_to_data():
        if acc:
            print("Suscribing to ACC")
            s.send(("device_subscribe " + 'acc' + " ON\r\n").encode())
            response = s.recv(bufferSize)
            print(response.decode("utf-8"))
        if bvp:
            print("Suscribing to BVP")
            s.send(("device_subscribe " + 'bvp' + " ON\r\n").encode())
            response = s.recv(bufferSize)
            print(response.decode("utf-8"))
        if gsr:
            print("Suscribing to GSR")
            s.send(("device_subscribe " + 'gsr' + " ON\r\n").encode())
            response = s.recv(bufferSize)
            print(response.decode("utf-8"))
        if tmp:
            print("Suscribing to Temp")
            s.send(("device_subscribe " + 'tmp' + " ON\r\n").encode())
            response = s.recv(bufferSize)
            print(response.decode("utf-8"))
        if ibi:
            print("Suscribing to Ibi")
            s.send(("device_subscribe " + 'ibi' + " ON\r\n").encode())
            response = s.recv(bufferSize)
            print(response.decode("utf-8"))

        print("Resuming data receiving")
        s.send("pause OFF\r\n".encode())
        response = s.recv(bufferSize)
        print(response.decode("utf-8"))
    suscribe_to_data()

    def prepare_LSL_streaming():
        print("Starting LSL streaming")
        if acc:
            infoACC = pylsl.StreamInfo('acc','ACC',3,32,'int32','ACC-empatica_e4')
            global outletACC
            outletACC = pylsl.StreamOutlet(infoACC)
        if bvp:
            infoBVP = pylsl.StreamInfo('bvp','BVP',1,64,'float32','BVP-empatica_e4')
            global outletBVP
            outletBVP = pylsl.StreamOutlet(infoBVP)
        if gsr:
            infoGSR = pylsl.StreamInfo('gsr','GSR',1,4,'float32','GSR-empatica_e4')
            global outletGSR
            outletGSR = pylsl.StreamOutlet(infoGSR)
        if tmp:
            infoTemp = pylsl.StreamInfo('tmp','Temp',1,4,'float32','Temp-empatica_e4')
            global outletTemp
            outletTemp = pylsl.StreamOutlet(infoTemp)
        if ibi:
            infoIbi = pylsl.StreamInfo('ibi','Ibi',1,2,'float32','IBI-empatica_e4')
            global outletIbi
            outletIbi = pylsl.StreamOutlet(infoIbi)
    prepare_LSL_streaming()

    time.sleep(1)

    def reconnect():
        print("Reconnecting...")
        connect()
        suscribe_to_data()
        stream()

    def stream():
        try:
            print("Streaming...")
            try:
                response = s.recv(bufferSize).decode("utf-8")
                #print(response)
                if "connection lost to device" in response:
                    print(response.decode("utf-8"))
                    reconnect()
                samples = response.split("\n") #Variable "samples" contains all the information collected from the wristband.
                print(samples)
                # We need to clean every temporal array before entering the for loop.
                global Temporal_BVP_array
                global Temporal_GSR_array
                global Temporal_Temp_array
                global Temporal_IBI_array
                global flag_Temp #We only want one value of the Temperature to reduce the final file size.
                flag_Temp = 0
                for i in range(len(samples)-1):
                    try:
                        stream_type = samples[i].split()[0]
                    except:
                        continue
                    #print(samples)
                    if (stream_type == "E4_Acc"):
                        global Acc_array
                        global ACC_tuple
                        timestamp = float(samples[i].split()[1].replace(',','.'))
                        data = [int(samples[i].split()[2].replace(',','.')), int(samples[i].split()[3].replace(',','.')), int(samples[i].split()[4].replace(',','.'))]
                        outletACC.push_sample(data, timestamp=timestamp)
                        timestamp = datetime.fromtimestamp(timestamp)
                        #print(data)#Added in 02/12/20 to show values
                        ACC_tuple = (timestamp.strftime('%Y-%m-%d %H:%M:%S.%f'), data)
                        Acc_array.append(ACC_tuple)
                    if stream_type == "E4_Bvp":
                        global BVP_tuple
                        global BVP_array
                        timestamp = float(samples[i].split()[1].replace(',','.'))
                        data = float(samples[i].split()[2].replace(',','.'))
                        outletBVP.push_sample([data], timestamp=timestamp)
                        timestamp = datetime.fromtimestamp(timestamp)
                        #print(data)
                        Temporal_BVP_array.append(data)
                        BVP_tuple = (timestamp.strftime('%Y-%m-%d %H:%M:%S.%f'), data)
                        BVP_array.append(BVP_tuple)
                    if stream_type == "E4_Gsr":
                        global GSR_array
                        global GSR_tuple
                        timestamp = float(samples[i].split()[1].replace(',','.'))
                        data = float(samples[i].split()[2].replace(',','.'))
                        outletGSR.push_sample([data], timestamp=timestamp)
                        timestamp = datetime.fromtimestamp(timestamp)
                        #print(data)
                        Temporal_GSR_array.append(data)
                        GSR_tuple = (timestamp.strftime('%Y-%m-%d %H:%M:%S.%f'), data)
                        GSR_array.append(GSR_tuple)
                    if stream_type == "E4_Temperature":
                        global Temp_array
                        global Temp_tuple
                        timestamp = float(samples[i].split()[1].replace(',','.'))
                        data = float(samples[i].split()[2].replace(',','.'))
                        outletTemp.push_sample([data], timestamp=timestamp)
                        timestamp = datetime.fromtimestamp(timestamp)
                        #print(data)
                        Temporal_Temp_array.append(data)
                        if flag_Temp == 0:
                            Temp_tuple = (timestamp.strftime('%Y-%m-%d %H:%M:%S.%f'), Temporal_Temp_array[0])
                            Temp_array.append(Temp_tuple)
                            flag_Temp = 1
                    if stream_type == "E4_Ibi":
                        global IBI_array
                        global IBI_tuple
                        timestamp = float(samples[i].split()[1].replace(',','.'))
                        data = float(samples[i].split()[2].replace(',','.'))
                        outletIbi.push_sample([data], timestamp=timestamp)
                        timestamp = datetime.fromtimestamp(timestamp)
                        #print(data)
                        Temporal_IBI_array.append(data)
                        IBI_tuple = (timestamp.strftime('%Y-%m-%d %H:%M:%S.%f'), data)
                        IBI_array.append(IBI_tuple)
                # We get the mean of the temperature and append them to the final array.
                # Temp_tuple = (datetime.now().isoformat(), np.mean(Temporal_Temp_array))
                # Temp_array.append(Temp_tuple)

                # We pause the acquisition of signals for one second
                #time.sleep(3)
            except socket.timeout:
                print("Socket timeout")
                reconnect()
        except KeyboardInterrupt:
            """
            #Debugging print variables
            print(BVP_array)
            print("*********************************************")
            print()
            print(Acc_array)
            print("*********************************************")
            print()
            print(GSR_array)
            print("*********************************************")
            print()
            print(Temp_array)
            print()
            """
            #print("Disconnecting from device")
            #s.send("device_disconnect\r\n".encode())
            #s.close()
    #stream()

    # MATPLOTLIB'S FIGURE AND SUBPLOTS SETUP
    """
    Gridspec is a function that help's us organize the layout of the graphs,
    first we need to create a figure, then assign a gridspec to the figure.
    Finally create the subplots objects (ax's) assigning a format with gs (gridspec).
    """
    fig = plt.figure(constrained_layout = True)
    gs = fig.add_gridspec(5,1)
    ax1 = fig.add_subplot(gs[0,0])
    ax1.set_title("Temperature")
    ax2 = fig.add_subplot(gs[1,0])
    ax2.set_title("Electrodermal Activity")
    ax3 = fig.add_subplot(gs[2,0])
    ax3.set_title("Blood Volume Pulse")
    ax4 = fig.add_subplot(gs[3,0])
    ax4.set_title("IBI")
    ax5 = fig.add_subplot(gs[4,0])
    ax5.set_title("Fast Fourier Transform")

    # Animation function: this function will update the graph in real time,
    # in order for it to work properly, new data must be collected inside this function.
    def animate(frame):
        global BVP_array
        global GSR_array
        global Temp_array
        global IBI_array
        global Temporal_BVP_array
        global Temporal_GSR_array
        global Temporal_Temp_array
        global Temporal_IBI_array
        global counter
        stream() # This is the function that connects to the Empatica.
        
        #x_BVP_val = np.linspace(0,len(Temporal_BVP_array)-1,num= len(Temporal_BVP_array))
        #x_GSR_val = np.linspace(0,len(Temporal_GSR_array)-1,num= len(Temporal_GSR_array))
        #x_Temp_val = np.linspace(0,len(Temporal_Temp_array)-1,num= len(Temporal_Temp_array))
        #x_IBI_val = np.linspace(0,len(Temporal_IBI_array)-1,num= len(Temporal_IBI_array))
        
        x_BVP_val = np.arange(0.015625,((len(Temporal_BVP_array))*0.015625)+0.015625,0.015625)
        x_GSR_val = np.arange(0.25,((len(Temporal_GSR_array))*0.25)+0.25,0.25)
        x_Temp_val = np.linspace(0,len(Temporal_Temp_array)-1,num= len(Temporal_Temp_array))
        x_IBI_val = np.linspace(0,len(Temporal_IBI_array)-1,num= len(Temporal_IBI_array))
        
        X = rfft(Temporal_BVP_array)
        xf = rfftfreq(len(Temporal_BVP_array), 1/64)

        # GRAPHING ASSIGNMENT SECTION
        # First the previous data must be cleaned, then we plot the array with the updated info.
        ax1.clear()
        ax2.clear()
        ax3.clear()
        ax4.clear()
        ax5.clear()
        ax1.set_ylim(25,40) #We fixed the y-axis values to observe a better data representation.
        #ax2.set_ylim(0, 0.5)
        ax3.set_ylim(-150,150)
        ax4.set_ylim(0,1)
        ax1.set_title("Temperature")
        ax2.set_title("Electrodermal Activity")
        ax3.set_title("Blood Volume Pulse")
        ax4.set_title("IBI")
        ax5.set_title("Fast Fourier Transform")
        ax1.set_ylabel("Celsius (°C)")
        ax2.set_ylabel("Microsiemens (µS)")
        ax3.set_ylabel("Nano Watt")
        ax4.set_ylabel("Seconds (s)")
        ax5.set_ylabel("Magnitude")
        ax1.set_xlabel("Samples")
        ax2.set_xlabel("Seconds")
        ax3.set_xlabel("Seconds")
        ax4.set_xlabel("Samples")
        ax5.set_xlabel("Frequency (Hz)")

        if (counter >= 2400):
            ax1.plot(x_Temp_val,Temporal_Temp_array, color = "#F1C40F")
            ax2.plot(x_GSR_val[-200:],Temporal_GSR_array[-200:], color = "#16A085")
            ax3.plot(x_BVP_val[-2000:],Temporal_BVP_array[-2000:])
            ax4.plot(x_IBI_val, Temporal_IBI_array, color = '#F2220C')
            ax5.plot(xf, np.abs(X))

        else:
            ax1.plot(x_Temp_val,Temporal_Temp_array, color = "#F1C40F")
            ax2.plot(x_GSR_val,Temporal_GSR_array, color = "#16A085")
            ax3.plot(x_BVP_val,Temporal_BVP_array)
            ax4.plot(x_IBI_val, Temporal_IBI_array, color = '#F2220C')
            ax5.plot(xf, np.abs(X))

        counter += 60  

    # Here es where the animation is executed. Try encaspsulation allows us
    # to stop the code anytime with Ctrl+C.
    try:
        anim = animation.FuncAnimation(fig, animate,
                                    frames = 500, 
                                    interval = 1000)
        # Once the Animation Function is ran, plt.show() is necesarry, 
        # otherwise it won't show the image. Also, plt.show() will stop the execution of the code 
        # that is located after. So if we want to continue with the following code, we must close the 
        # tab generated by matplotlib.   
        plt.show()
        
        # The next lines allow us to create a CSV file with data retrieved from E4 wristband.
        # This code is repeated if a KeyboardInterrupt exception arises as a redundant case
        # for storing the data recorded.
        with open("fileBVP.csv", 'w', newline = '') as document:
            writer = csv.writer(document)
            writer.writerow(['Datetime', 'valueBVP'])
            writer.writerows(BVP_array)

        with open("fileACC.csv", 'w', newline = '') as document:
                    writer = csv.writer(document)
                    writer.writerow(['Datetime', 'valueACC'])
                    writer.writerows(Acc_array)   

        with open("fileEDA.csv", 'w', newline = '') as document:
                    writer = csv.writer(document)
                    writer.writerow(['Datetime', 'valueEDA'])
                    writer.writerows(GSR_array)        

        with open("fileTemp.csv", 'w', newline = '') as document:
                    writer = csv.writer(document)
                    writer.writerow(['Datetime', 'valueTemp'])
                    writer.writerows(Temp_array)        

        with open("fileIBI.csv", 'w', newline = '') as document:
                    writer = csv.writer(document)
                    writer.writerow(['Datetime', 'valueIBI'])
                    writer.writerows(IBI_array)   
        
        # Once we have the data stored locally on CSV files, we store it in json files to send them through a socket.
        csvFilePath = 'fileBVP.csv'
        jsonPost(csvFilePath, 'valueBVP')
        csvFilePath = 'fileACC.csv'
        jsonPost(csvFilePath, 'valueACC')
        csvFilePath = 'fileEDA.csv'
        jsonPost(csvFilePath, 'valueEDA')
        csvFilePath = 'fileTemp.csv'
        jsonPost(csvFilePath, 'valueTemp')
        csvFilePath = 'fileIBI.csv'
        jsonPost(csvFilePath, 'valueIBI')

        # These next instructions should be executed only once, and exactly where we want the program to finish.
        # Otherwise, it may rise a Socket Error. These lines also written below in case of a KeyBoardInterrupt 
        # exception arising.
        global s
        print("Disconnecting from device")
        s.send("device_disconnect\r\n".encode())
        s.close()

    except KeyboardInterrupt:
        #The next lines allow us to create a CSV file with data retrieved from E4 wristband.
        with open("fileBVP.csv", 'w', newline = '') as document:
            writer = csv.writer(document)
            writer.writerow(['Datetime', 'valueBVP'])
            writer.writerows(BVP_array)

        with open("fileACC.csv", 'w', newline = '') as document:
                    writer = csv.writer(document)
                    writer.writerow(['Datetime', 'valueACC'])
                    writer.writerows(Acc_array)   

        with open("fileEDA.csv", 'w', newline = '') as document:
                    writer = csv.writer(document)
                    writer.writerow(['Datetime', 'valueEDA'])
                    writer.writerows(GSR_array)        

        with open("fileTemp.csv", 'w', newline = '') as document:
                    writer = csv.writer(document)
                    writer.writerow(['Datetime', 'valueTemp'])
                    writer.writerows(Temp_array)        

        with open("fileIBI.csv", 'w', newline = '') as document:
                    writer = csv.writer(document)
                    writer.writerow(['Datetime', 'valueIBI'])
                    writer.writerows(IBI_array)   

        # Once we have the data stored locally on CSV files, we store it in json files to send them through a socket.
        csvFilePath = 'fileBVP.csv'
        jsonPost(csvFilePath, 'valueBVP')
        csvFilePath = 'fileACC.csv'
        jsonPost(csvFilePath, 'valueACC')
        csvFilePath = 'fileEDA.csv'
        jsonPost(csvFilePath, 'valueEDA')
        csvFilePath = 'fileTemp.csv'
        jsonPost(csvFilePath, 'valueTemp')
        csvFilePath = 'fileIBI.csv'
        jsonPost(csvFilePath, 'valueIBI')

        # We close connections
        print("Disconnecting from device")
        s.send("device_disconnect\r\n".encode())
        s.close()

# To run the script, the empatica() function contains everything necessary for the connection, acquisition, and 
# data storage
empatica()

# # # # SOURCES # # # # 
# Source for matplotlib's animation
# https://www.geeksforgeeks.org/matplotlib-animation-funcanimation-class-in-python/
# https://www.youtube.com/watch?v=ZmYPzESC5YY
# Source to remove the first values of the graph using .pop(), use if necessary
# https://medium.com/intel-student-ambassadors/live-graph-simulation-using-python-matplotlib-and-pandas-30ea4e50f883
# Gridspec Detail's and examples
# https://matplotlib.org/tutorials/intermediate/gridspec.html