import json, sys, math, asyncio
from ctypes import *

def json_to_class(json_str, class_name="DynamicClass"):
    data_dict = json.loads(json_str)
    return type(class_name, (object,), data_dict)


class DWFController():
    def __init__(self):
        if sys.platform.startswith("win"):
            self.dwf = cdll.dwf
        elif sys.platform.startswith("darwin"):
            self.dwf = cdll.LoadLibrary("/Library/Frameworks/dwf.framework/dwf")
        else:
            self.dwf = cdll.LoadLibrary("libdwf.so")

        self.hdwf = c_int()
        self.sts = c_byte()
        self.nSamples = 8000
        self.rgdSamples = (c_double*self.nSamples)()
        self.cValid = c_int(0)

        version = create_string_buffer(16)
        self.dwf.FDwfGetVersion(version)
        print("DWF Version: "+str(version.value))

        print("Opening first device")
        self.dwf.FDwfDeviceOpen(c_int(-1), byref(self.hdwf))

        if self.hdwf.value == 0:
            szerr = create_string_buffer(512)
            self.dwf.FDwfGetLastErrorMsg(szerr)
            print(str(szerr.value))
            print("failed to open device")
            quit()

    async def set(self, frequency, secLog):
        print(f"frequency:{frequency},seclog:{secLog}")
        self.secLog = secLog
        print("Generating sine wave...")
        self.dwf.FDwfAnalogOutNodeEnableSet(self.hdwf, c_int(0), c_int(0), c_int(1)) # carrier
        self.dwf.FDwfAnalogOutNodeFunctionSet(self.hdwf, c_int(0), c_int(0), c_int(1)) # sine
        self.dwf.FDwfAnalogOutNodeFrequencySet(self.hdwf, c_int(0), c_int(0), c_double(frequency)) #Hz
        self.dwf.FDwfAnalogOutNodeAmplitudeSet(self.hdwf, c_int(0), c_int(0), c_double(5)) #Amplitude(V)
        self.dwf.FDwfAnalogOutNodeOffsetSet(self.hdwf, c_int(0), c_int(0), c_double(0)) #offset(0V)
        self.dwf.FDwfAnalogOutConfigure(self.hdwf, c_int(0), c_int(1))

        # set up acquisition
        self.dwf.FDwfAnalogInChannelEnableSet(self.hdwf, c_int(0), c_int(1))
        self.dwf.FDwfAnalogInChannelRangeSet(self.hdwf, c_int(0), c_double(50)) #range of Volt
        self.dwf.FDwfAnalogInAcquisitionModeSet(self.hdwf, c_int(1)) #acqmodeScanShift
        self.dwf.FDwfAnalogInFrequencySet(self.hdwf, c_double(self.nSamples/self.secLog)) 
        self.dwf.FDwfAnalogInBufferSizeSet(self.hdwf, c_int(self.nSamples))

        # wait at least 2 seconds for the offset to stabilize
        await asyncio.sleep(1)

        # begin acquisition
        self.dwf.FDwfAnalogInConfigure(self.hdwf, c_int(0), c_int(1))

    async def getdata(self):
        self.dwf.FDwfAnalogInStatus(self.hdwf, c_int(1), byref(self.sts))
        self.dwf.FDwfAnalogInStatusSamplesValid(self.hdwf, byref(self.cValid))
        data_list = []
        for iChannel in range(1):
            self.dwf.FDwfAnalogInStatusData(self.hdwf, c_int(iChannel), byref(self.rgdSamples), self.cValid) # get channel 1 data
            dc = sum(self.rgdSamples) / self.nSamples
            dcrms = math.sqrt(sum([x**2 for x in self.rgdSamples]) / self.nSamples)
            acrms = math.sqrt(sum([(x-dc)**2 for x in self.rgdSamples]) / self.nSamples)
            data_list.append((dc, dcrms, acrms))
        return data_list

    def close(self):
        self.dwf.FDwfAnalogOutConfigure(self.hdwf, c_int(0), c_int(0))
        self.dwf.FDwfDeviceCloseAll()