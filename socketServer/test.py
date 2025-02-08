import socketio

sio = socketio.SimpleClient()
sio.connect('http://localhost:5000', transports=['websocket'], auth="client auth hehe")

sio