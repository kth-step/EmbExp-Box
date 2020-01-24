
import sys
import logging

import boxportdistrib
import sshslave

OKBLUE = '\033[94m'
ENDC = '\033[0m'


def get_port_dicts(instance_idx, board_idx):
	(comm,     ((oocd_gdb_base,     _), oocd_telnet,     _)) = boxportdistrib.get_ports_box_server_board(board_idx)
	(comm_loc, ((oocd_gdb_base_loc, _), oocd_telnet_loc, _)) = boxportdistrib.get_ports_box_server_board_client(instance_idx)

	# TODO: currently no handling for multiple gdb ports!
	return ({comm_loc:comm}, {oocd_gdb_base_loc:oocd_gdb_base, oocd_telnet_loc:oocd_telnet})
	

def launch_embexp_comm(master, board_idx, board_id, term_handler):
	redir_dict = get_port_dicts(master.instance_idx, board_idx)[0]
	slave_redir = sshslave.SshSlave_Portredir(master, redir_dict, term_handler)
	slave_redir.start()

	try:
		ssh_cmd_list = ["/opt/embexp-box/interface/comm.py %s" % (" ".join(board_id))]
		sshslave.SshSlave("comm", master, ssh_cmd_list, lambda: slave_redir.stop(deregister_handler=False)).start()
	except:
		slave_redir.stop()
		raise
	sys.stdout.write(OKBLUE)
	print("CommPort    = %s" % (str(list(redir_dict.keys()))))
	sys.stdout.write(ENDC)
	sys.stdout.flush()
	logging.info("Redirection = %s" % (str(redir_dict)))


def launch_embexp_openocd(master, board_idx, board_id, term_handler):
	redir_dict = get_port_dicts(master.instance_idx, board_idx)[1]
	slave_redir = sshslave.SshSlave_Portredir(master, redir_dict, term_handler)
	slave_redir.start()

	try:
		ssh_cmd_list = ["/opt/embexp-box/interface/openocd.py %s" % (" ".join(board_id))]
		sshslave.SshSlave("oocd", master, ssh_cmd_list, lambda: slave_redir.stop(deregister_handler=False)).start()
	except:
		slave_redir.stop()
		raise
	sys.stdout.write(OKBLUE)
	print("OOCD GDB&Telnet Ports = %s" % (str(list(redir_dict.keys()))))
	sys.stdout.write(ENDC)
	sys.stdout.flush()
	logging.info("Redirection           = %s" % (str(redir_dict)))

def execute_embexp_programfpga(master, board_id, bitstream_file):
	ssh_cmd_list = ["/opt/embexp-box/interface/fpgaprog.py"] + board_id + [bitstream_file]
	slave_fpgaprog = sshslave.SshSlave("fpgaprog", master, ssh_cmd_list, lambda: None)
	slave_fpgaprog.start()
	slave_fpgaprog.wait(10)

