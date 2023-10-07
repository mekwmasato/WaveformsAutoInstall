"""
   DWF Python Example
   Author:  Digilent, Inc.
   Revision:  2018-07-19

   Requires:                       
       Python 2.7, 3
   Description:
   Generates AM modulated signal on AWG1 channel
   Scope performs scan shift acquisition and logs DC and AC/DC-RMS values
"""

from ctypes import *
import math
import time
import matplotlib.pyplot as plt
import sys
import requests
import csv
import datetime
import os
import boto3

if sys.platform.startswith("win"):
    dwf = cdll.dwf
elif sys.platform.startswith("darwin"):
    dwf = cdll.LoadLibrary("/Library/Frameworks/dwf.framework/dwf")
else:
    dwf = cdll.LoadLibrary("libdwf.so")

hdwf = c_int()
sts = c_byte()
secLog = 1.0 # logging rate in seconds
nSamples = 8000
rgdSamples = (c_double*nSamples)()
cValid = c_int(0)

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

print("Generating  sine wave...")
dwf.FDwfAnalogOutNodeEnableSet(hdwf, c_int(0), c_int(0), c_int(1)) # carrier
dwf.FDwfAnalogOutNodeFunctionSet(hdwf, c_int(0), c_int(0), c_int(1)) # sine
dwf.FDwfAnalogOutNodeFrequencySet(hdwf, c_int(0), c_int(0), c_double(1000)) #Hz
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

#csvファイル名の設定
now = datetime.datetime.today()
hourstr = "_" + now.strftime("%H%M%S")
"""filename = "record_" + now.strftime("%Y%m%d") + hourstr +  ".csv"""
filename = "record_" + now.strftime("%Y%m%d") + hourstr + "_number4 " + ".csv"
number = 1

print("Press Ctrl+C to stop")
try:
    os.makedirs('record'+ now.strftime("%Y%m%d"),exist_ok=True)
    #create CSV
    with open(os.path.join('record'+ now.strftime("%Y%m%d"),filename), 'a', newline= '') as f:
        writer = csv.writer(f)
        writer.writerow(["time","number","ACRMS[V]","DCRMS[V]"])
    
        while True:
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
                
                now_ser = datetime.datetime.today()
                print(f"CH:{iChannel+1} time:{now_ser} ACRMS:{acrms:.7f}V DCRMS:{dcrms:.7f}V")
                data = [now_ser,number,acrms,dcrms]
                writer.writerow(data)
                number += 1
                

except KeyboardInterrupt:
    pass

f.close() 
#Access Key AKIA6J6EPNOB67TN7FX7
#Secret access Key  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

#Create client
s3 = boto3.client("s3")

S3_BUCKET_NAME = "test-raspberrypi-to-upload-to-s3"
S3_FOLDER_ROUTE = "python/csv-folder/"

#upload
with open(os.path.join('record'+ now.strftime("%Y%m%d"),filename),"rb") as f:
    s3.upload_fileobj(f,S3_BUCKET_NAME, S3_FOLDER_ROUTE + filename)
#complleted upload to s3
print("finish")

dwf.FDwfAnalogOutConfigure(hdwf, c_int(0), c_int(0))
dwf.FDwfDeviceCloseAll()

