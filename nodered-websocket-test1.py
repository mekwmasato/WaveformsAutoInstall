import websockets, sys, asyncio
import utils #別ファイルutils.py内の関数をutils.oo()で呼び出せる

websocket_server = "ws://127.0.0.1:1880/ws/test1" #url of Node-Red

try:
    #dwf=...ここで機器に接続確認
    print(f"Measurement device connected.")
    pass
except Exception as e:
    print(e)
    print(f"Ensure your measurement device is correctly connected.")


recvdata = None
stop_measurement = asyncio.Event()

async def receive_messages():
    while True:
        try:
            async with websockets.connect(websocket_server) as ws:
                while True:
                    recvdata = utils.json_to_class(await ws.recv())
                    if not recvdata.measurementOn:
                        stop_measurement.set()

        except websockets.ConnectionClosed:
            print("Connection closed. Retrying in 5 seconds...")
            await asyncio.sleep(5)
        except Exception as e:
            print(f"Error occurred: {e}. Retrying in 5 seconds...")
            await asyncio.sleep(5)
        

async def perform_measurement():
    while True:
        await asyncio.sleep(0.1)  # このスリープは計測のサンプルレートを模倣するためのものです。適切な計測のロジックに置き換えてください。
        if recvdata and recvdata.measurementOn:
            print("Measurement On")
        if stop_measurement.is_set():
            print("Processing data...")
            # ここにデータの処理を追加
            stop_measurement.clear()


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