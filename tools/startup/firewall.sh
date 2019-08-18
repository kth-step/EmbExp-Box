export EXPERIMENT_IF=enx00e04c680037


# completely initialize iptables
iptables -P INPUT ACCEPT
iptables -P FORWARD ACCEPT
iptables -P OUTPUT ACCEPT
iptables -t nat -F
iptables -t mangle -F
iptables -F
iptables -X

# drop by default, just to be sure
iptables -P INPUT   DROP
iptables -P OUTPUT  DROP
iptables -P FORWARD DROP

# accept SSH on all interfaces
iptables -A INPUT  -p tcp --dport ssh -j ACCEPT
iptables -A OUTPUT -p tcp --sport ssh -j ACCEPT

# accept ping on all interfaces
iptables -A INPUT  -p icmp --icmp-type echo-request -j ACCEPT
iptables -A OUTPUT -p icmp --icmp-type echo-reply -j ACCEPT

# accept all traffic on the loopback interface
iptables -A INPUT  -i lo -j ACCEPT
iptables -A OUTPUT -o lo -j ACCEPT

# allow to establish arbitrary connections
iptables -A OUTPUT -j ACCEPT -m state --state NEW
iptables -A OUTPUT -j ACCEPT -m state --state ESTABLISHED
iptables -A INPUT  -j ACCEPT -m state --state ESTABLISHED

# accept everything on ${EXPERIMENT_IF}
iptables -A INPUT  -i ${EXPERIMENT_IF} -j ACCEPT
iptables -A OUTPUT -o ${EXPERIMENT_IF} -j ACCEPT

# reject everything else
iptables -A INPUT   -j REJECT
iptables -A OUTPUT  -j REJECT
iptables -A FORWARD -j REJECT


