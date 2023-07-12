
# %%
import websocket
import json

def close_ws():
    with open('closing.txt') as f:
        return int(f.readline()) > 0 

def on_open(_wsa):
    data = dict(
        method ="SUBSCRIBE",
        id=1,
        params=['btcusdt@depth5', 'btcusdt@kline_3m', 'ethusdt@kline_3m']
    )

    _wsa.send(json.dumps(data))

def append_data_to_file(data, filename):
    with open(filename, 'a') as file:
        json.dump(data, file)
        file.write('\n')

filename = 'binance_data.json'

def on_message(_wsa, data):

    if close_ws(): 
        _wsa.close()
    else:
        append_data_to_file(data, filename)
        print(data, '\n\n')


def run():
    
    stream_name = 'binance_stream'
    wss = 'wss://stream.binance.com:9443/ws/%s' % stream_name
    wsa = websocket.WebSocketApp(wss, on_message=on_message, on_open=on_open)
    wsa.run_forever()


if __name__ == '__main__':
    run()

# %%
