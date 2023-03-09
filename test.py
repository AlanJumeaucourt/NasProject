from ipaddress import IPv4Address
if __name__ == '__main__':
    interface={}
    print(interface)
    interface['fa0/0'] = {}
    print(interface)
    interface['fa0/0']['isConnected'] = "false"
    print(interface)
    interface['fa0/0']['connectedTo'] = "r1"
    print(interface)

    ip = IPv4Address('192.0.2.1')
    print(ip)
