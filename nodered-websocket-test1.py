import websockets, sys, asyncio
import utils #別ファイルutils.py内の関数をutils.oo()で呼び出せる

websocket_server = "ws://180.19.43.93:1880/ws/test1" #url of Node-Red

try:
    dwf = utils.DWFController()
    print(f"Measurement device connected.")
    pass
except Exception as e:
    print(e)
    print(f"Ensure your measurement device is correctly connected.")


recvdata = None
stop_measurement = asyncio.Event()
recv_queue = asyncio.Queue() #わりこみ

async def receive_messages():
    global recvdata
    while True:
        try:
            async with websockets.connect(websocket_server) as ws:
                print(f"ws conncted.")
                while True:
                    message = await ws.recv()
                    await recv_queue.put(message)
                    #recvdata = utils.json_to_class(await ws.recv())
                    #if not recvdata.measurementOn:
                    #    stop_measurement.set()

        except websockets.ConnectionClosed:
            print("Connection closed. Retrying in 5 seconds...")
            await asyncio.sleep(5)
        except Exception as e:
            print(f"Error occurred: {e}. Retrying in 5 seconds...")
            await asyncio.sleep(5)


async def perform_measurement():
    is_measuring = False  # 計測中かどうかを示すフラグ
    accumulated_data = []  # 蓄積されたデータを保存するリスト

    while True:
        #await asyncio.sleep(0.1)
        recvdata = utils.json_to_class(await recv_queue.get())
        if recvdata:
            if recvdata.measurementOn and not is_measuring:
                print("計測開始")
                await dwf.set(recvdata.frequency, recvdata.seclog)
                is_measuring = True
            
            if is_measuring:
                print(f"計測中")
                accumulated_data.append(await dwf.getdata())

            if not recvdata.measurementOn and is_measuring:
                print(f"計測終了")
                print("Processing data...")
                print(accumulated_data)
                # accumulated_dataをCSVに変換する処理を追加
                accumulated_data.clear()  # データをリセット
                is_measuring = False


async def main():
    asyncio.create_task(receive_messages())
    await perform_measurement()


if __name__ == "__main__":
    try:
        asyncio.get_event_loop().run_until_complete(main())
    except KeyboardInterrupt:
        print(f"Program interrupted by user. Exiting...")
        sys.exit(0)
    except Exception as e:
        print(f"{e}")