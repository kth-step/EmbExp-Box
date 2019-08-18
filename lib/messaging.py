
import json

class SocketDiedException(Exception):
	pass


def send_message(s, dictmsg):
	strmsg = json.dumps(dictmsg)
	strmsg_len = len(strmsg)

	# send length
	try:
		s.sendall(strmsg_len.to_bytes(2, byteorder='little', signed=False))
	except OverflowError:
		raise ValueError("the message could not be sent because its encoding is too big")
	# send message itself
	s.sendall(strmsg.encode('utf-8'))


def recv_fixedsize(s, size):
	data = b''
	while size > 0:
		data_new = s.recv(size)
		if not data_new:
			raise SocketDiedException()
		size = size - len(data_new)
		data = data + data_new

	return data


def recv_message(s):
	# receive length
	msg_len = int.from_bytes(recv_fixedsize(s, 2), byteorder='little', signed=False)
	# receive message itself
	msg = json.loads(recv_fixedsize(s, msg_len).decode('utf-8'))

	return msg


