from ctypes import *
import math
import time
import matplotlib.pyplot as plt
import sys
import requests
import csv

#websocket 
import websocket
import json
#websocket server's url, proxy
websocket_server = "ws://180.19.43.93:1880/ws/itayaken" #url of Node-Red
http_proxy_host = ""
http_proxy_port = 1880

##create websocket , and connect
ws = websocket.create_connection(websocket_server, http_proxy_host=http_proxy_host, http_proxy_port=http_proxy_port)


if sys.platform.startswith("win"):
    dwf = cdll.dwf
elif sys.platform.startswith("darwin"):
    dwf = cdll.LoadLibrary("/Library/Frameworks/dwf.framework/dwf")
else:
    dwf = cdll.LoadLibrary("libdwf.so")

hdwf = c_int()
sts = c_byte()
secLog = 1 # logging rate in seconds
nSamples = 8000
rgdSamples = (c_double*nSamples)()
cValid = c_int(0)
frequency = 1000

version = create_string_buffer(16)
dwf.FDwfGetVersion(version)
print("DWF Version: "+str(version.value))

print("Opening first device")
dwf.FDwfDeviceOpen(c_int(-1), byref(hdwf))

if hdwf.value == 0:
    szerr = create_string_buffer(512)
    dwf.FDwfGetLastErrorMsg(szerr)
    print(str(szerr.value))
    print("failed to open device")
    quit()

print("Press Ctrl+C to stop")
try:
    while True:
        recvdata = ws.recv()
        if recvdata["status"] == 1:
            frequency = double(recvdata["frequency"])
            print("Generating sine wave... (" + str(frequency) + "[Hz)]")
            dwf.FDwfAnalogOutNodeEnableSet(hdwf, c_int(0), c_int(0), c_int(1)) # carrier
            dwf.FDwfAnalogOutNodeFunctionSet(hdwf, c_int(0), c_int(0), c_int(1)) # sine
            dwf.FDwfAnalogOutNodeFrequencySet(hdwf, c_int(0), c_int(0), c_double(frequency)) #Hz
            dwf.FDwfAnalogOutNodeAmplitudeSet(hdwf, c_int(0), c_int(0), c_double(5)) #Amplitude(V)
            dwf.FDwfAnalogOutNodeOffsetSet(hdwf, c_int(0), c_int(0), c_double(0)) #offset(0V)
            dwf.FDwfAnalogOutConfigure(hdwf, c_int(0), c_int(1))

            #set up acquisition
            dwf.FDwfAnalogInChannelEnableSet(hdwf, c_int(0), c_int(1))
            dwf.FDwfAnalogInChannelRangeSet(hdwf, c_int(0), c_double(50)) #range of Volt
            dwf.FDwfAnalogInAcquisitionModeSet(hdwf, c_int(1)) #acqmodeScanShift
            dwf.FDwfAnalogInFrequencySet(hdwf, c_double(nSamples/secLog)) 
            dwf.FDwfAnalogInBufferSizeSet(hdwf, c_int(nSamples))

            #wait at least 2 seconds for the offset to stabilize
            time.sleep(1)

            #begin acquisition
            dwf.FDwfAnalogInConfigure(hdwf, c_int(0), c_int(1))

            cnt = 0
            f = open("record.csv", "w")
            writer = csv.writer(f,delimiter=',')
            writer.writerow(['DC','TrueRMS','ACRMS'])
            while True:
                recvdata = ws.recv()
                
                if recvdata["status"] == "stop":
                    print("stop sine wave")
                dwf.FDwfAnalogOutConfigure(hdwf, c_int(0), c_int(0))
                break

                cnt = cnt +1  #counter
                time.sleep(secLog)
                dwf.FDwfAnalogInStatus(hdwf, c_int(1), byref(sts))
                dwf.FDwfAnalogInStatusSamplesValid(hdwf, byref(cValid))
                for iChannel in range(1):
                    dwf.FDwfAnalogInStatusData(hdwf, c_int(iChannel), byref(rgdSamples), cValid) # get channel 1 data
                    dc = 0
                    for i in range(nSamples):
                        dc += rgdSamples[i]
                    dc /= nSamples
                    dcrms = 0
                    acrms = 0
                    for i in range(nSamples):
                        dcrms += rgdSamples[i] ** 2
                        acrms += (rgdSamples[i]-dc) ** 2
                    dcrms /= nSamples
                    dcrms = math.sqrt(dcrms)
                    acrms /= nSamples
                    acrms = math.sqrt(acrms)
                    print(f"CH:{iChannel+1} DC:{dc:.5f}V TrueRMS:{dcrms:.5f}V ACRMS:{acrms:.5f}V")

                    data = [dc ,dcrms , acrms]
                    writer.writerow(data)

                    ##send to websocketserver
                    data = {'cnt':cnt, 'dcrms':dcrms, 'acrms':acrms}
                    ws.send(json.dumps(data)) #transform to JSON and send




except KeyboardInterrupt:
    pass

f.close()
dwf.FDwfAnalogOutConfigure(hdwf, c_int(0), c_int(0))
dwf.FDwfDeviceCloseAll()

