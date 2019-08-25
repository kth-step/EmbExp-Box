
# no clashes with the ephermal port range
#https://idea.popcount.org/2014-04-03-bind-before-connect/
#cat /proc/sys/net/ipv4/ip_local_port_range
#32768	60999

def get_port_box_server():
	return 9000

def get_port_box_server_client(instance_idx):
	assert (0 <= instance_idx) and (instance_idx < 100)
	return 9100 + instance_idx

def _calc_board_ports(base_port, idx):
	base_port = base_port + (idx * 100)
	comm_port        = base_port + 0
	oocd_gdb_port    = base_port + 13
	oocd_gdb_window  = (oocd_gdb_port, 16)
	oocd_telnet_port = base_port + 4
	oocd_tcl_port    = base_port + 5
	return (comm_port, (oocd_gdb_window, oocd_telnet_port, oocd_tcl_port))

def get_ports_box_server_board(board_idx):
	assert (0 <= board_idx) and (board_idx < 100)
	return _calc_board_ports(10000, board_idx)

def get_ports_box_server_board_client(instance_idx):
	assert (0 <= instance_idx) and (instance_idx < 100)
	return _calc_board_ports(20000, instance_idx)


