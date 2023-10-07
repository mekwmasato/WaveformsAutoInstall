from lakeshore import SSMSystem
from time import sleep
from math import sqrt


M81 = SSMSystem(ip_address='10.10.10.13') #初期値ではUSBから接続、ip指定でTCP
#M81.connect_tcp('10.10.10.13',7777, 500) #多分これでネットワークから接続する
print(M81.query('*IDN?')) #よくわからん。ファームウェアバージョンが出力される

S1 = M81.get_source_module(1) #ソースモジュール
M1 = M81.get_measure_module(1) #計測モジュール

S1.set_shape('SINUSOID') #sin波のこと
S1.set_frequency(1000) #周波数
S1.set_current_amplitude(0.01) #電流[A]
S1.set_current_offset(0)
S1.configure_i_range(0, max_ac_level=0.1) #Range設定(autoを使うか、max_level,max_ac_level,max_dc_level)
S1.set_cmr_source('INTernal') #CMRのソースを設定
S1.enable_cmr() #CMRを有効化

#advanced setting
S1.use_ac_coupling()  #カップリングをACに設定

M1.setup_lock_in_measurement('S1', 0.1) #S1の周波数を参照信号にし、timeconstantを100msに設定

S1.enable() #S1を起動

sleep(1.5)

lock_in_magnitude = M1.get_lock_in_r()
print(lock_in_magnitude)


S1.disable() #S1を停止