import re
import time

import gns3fy
from tabulate import tabulate
from ipaddress import IPv4Address
import telnetlib


class Router:
    def __init__(self, name, uid, typeof):
        self.name = name
        self.typeof = typeof
        self.interfaces = {}
        self.uid = uid
        self.asnumber = ""

    def __str__(self):
        return f"""
Name: {self.name} 
Uid : {self.uid}
typeof: {self.typeof}
interfaces : {self.interfaces}
asnumber  {self.asnumber}
"""

    def showInfos(self):
        print("")
        print(f"--------------------------------Name: {self.name}--------------------------------")
        print(f"Uid: {self.uid}")
        print(f"typeof: {self.typeof}")
        print(f"asnumber: {self.asnumber}")
        for interfaceName in self.interfaces:
            print(f"interfaces : {interfaceName}")
            for key in self.interfaces[interfaceName]:
                print(f"    {key} : {self.interfaces[interfaceName][key]}")


def whichTypeOfRouterFromName(name):
    if name.startswith("PE"):
        return "PE"
    elif name.startswith("P"):
        return "P"
    elif name.startswith("CE"):
        return "CE"


# Project is to setup/automate an entire network with MPLS
# Type of router : CE (Customer Edge), P(Provider), PE(Provider Edge)
if __name__ == '__main__':

    # Define the server object to establish the connection
    gns3_server = gns3fy.Gns3Connector("http://localhost:3080")
    print(
        tabulate(
            gns3_server.projects_summary(is_print=False),
            headers=["Project Name", "Project ID", "Total Nodes", "Total Links", "Status"],
        )
    )

    listRouter = []
    setReseaux = {}

    for i in range(4, 248, 4):
        setReseaux[int((i / 4) - 1)] = IPv4Address("10.16.1." + str(i))

    # Default.rdp is actually the name of the project in GNS3
    lab = gns3fy.Project(name="test", connector=gns3_server)
    lab.get()

    # Add object router in list with name and uid
    print("\nStarting list and create router object in listRouteur")
    for node in lab.nodes:
        listRouter.append(Router(node.name, node.node_id, whichTypeOfRouterFromName(node.name)))

    # Add interface of router
    for i in range(len(listRouter)):
        for port in lab.nodes[i].ports:
            # Commented because no need for long name, maybe will be usefull later in project
            # listRouteur[i].interfaces[port['name']] = {}
            # listRouteur[i].interfaces[port['name']]['isConnected'] = "false"
            # listRouteur[i].interfaces[port['name']]['shortName'] = port['short_name']
            listRouter[i].interfaces[port['short_name']] = {}
            listRouter[i].interfaces[port['short_name']]['isConnected'] = "false"

    print(listRouter[0])

    # Add BGP AS
    for router in listRouter:
        if router.typeof == "PE":
            router.asnumber = "1337"
        elif router.typeof == "P":
            router.asnumber = "1337"
        elif router.typeof == "CE":
            if any([_ in router.name for _ in ["R1", "R2"]]):
                router.asnumber = "455"
            elif any([_ in router.name for _ in ["R3", "R4"]]):
                router.asnumber = "8008"

    # finding the link between routers
    print("\nStarting finding the link between routers")
    for i, link in enumerate(lab.links):
        firstRouterConnected = ""
        secondRouterConnected = ""
        firstRouterInterface = ""
        networkIp = ""
        firstRouterIp = ""
        secondRouterIp = ""
        firstRouterAsnumber = ""
        secondRouterAsnumber = ""

        for router in listRouter:
            if router.uid == link.nodes[0]['node_id']:
                firstRouterConnected = router.name
                firstRouterAsnumber = router.asnumber
            elif router.uid == link.nodes[1]['node_id']:
                secondRouterConnected = router.name
                secondRouterAsnumber = router.asnumber
        print("    " + firstRouterConnected + link.nodes[0]['label'][
            'text'] + " is connected to " + secondRouterConnected +
              link.nodes[1]['label']['text'])
        networkIp = setReseaux[i]
        firstRouterIp = setReseaux[i] + 1
        secondRouterIp = setReseaux[i] + 2

        for router in listRouter:
            if router.name == firstRouterConnected:
                for interfaceName in router.interfaces:
                    if interfaceName == link.nodes[0]['label']['text']:
                        router.interfaces[interfaceName]['isConnected'] = "true"
                        router.interfaces[interfaceName]['routerConnectedName'] = secondRouterConnected
                        router.interfaces[interfaceName]['routerConnectedInterfaceName'] = link.nodes[1]['label'][
                            'text']
                        router.interfaces[interfaceName]['RouterConnectedIp'] = secondRouterIp
                        router.interfaces[interfaceName]['RouterConnectedTypeof'] = whichTypeOfRouterFromName(
                            secondRouterConnected)
                        router.interfaces[interfaceName]['RouterConnectedAsnumber'] = secondRouterAsnumber
                        router.interfaces[interfaceName]['ipNetwork'] = networkIp
                        router.interfaces[interfaceName]['ip'] = firstRouterIp

            elif router.name == secondRouterConnected:
                for interfaceName in router.interfaces:
                    if interfaceName == link.nodes[1]['label']['text']:
                        router.interfaces[interfaceName]['isConnected'] = "true"
                        router.interfaces[interfaceName]['routerConnectedName'] = firstRouterConnected
                        router.interfaces[interfaceName]['routerConnectedInterfaceName'] = link.nodes[0]['label'][
                            'text']
                        router.interfaces[interfaceName]['RouterConnectedAsnumber'] = firstRouterAsnumber
                        router.interfaces[interfaceName]['RouterConnectedIp'] = firstRouterIp
                        router.interfaces[interfaceName]['RouterConnectedTypeof'] = whichTypeOfRouterFromName(
                            firstRouterConnected)
                        router.interfaces[interfaceName]['ipNetwork'] = networkIp
                        router.interfaces[interfaceName]['ip'] = secondRouterIp

    # OSPF
    for router in listRouter:
        tn = telnetlib.Telnet("localhost", lab.nodes_inventory()[router.name]["console_port"])
        tn.write(b"\r\n")
        tn.write(b"end\r\n")
        tn.write(b"conf t \r\n")
        tn.write(b"router ospf 10\r\n")
        tn.write(b"router ospf 11\r\n")

        # WIP Loopback design to be defined, below code is not functional anymore
        # numberInRouteurName = str(re.findall(r'\d+', router.name)[0])
        # tn.write(b"int loopback0\r\n")
        # tn.write(b"ip address 200.0.0." + str(numberInRouteurName).encode('ascii') + b" 255.255.255.255" + b"\r\n")
        tn.write(b"int loopback0\r\n")
        numberInRouteurName = str(re.findall(r'\d+', router.name)[0])
        if router.typeof == "P":
            tn.write(b"ip address 1.1.1." + str(numberInRouteurName).encode('ascii') + b" 255.255.255.255" + b"\r\n")
        elif router.typeof == "CE":
            tn.write(b"ip address 1.1.2." + str(numberInRouteurName).encode('ascii') + b" 255.255.255.255" + b"\r\n")
        elif router.typeof == "PE":
            tn.write(b"ip address 1.1.3." + str(numberInRouteurName).encode('ascii') + b" 255.255.255.255" + b"\r\n")


        time.sleep(0.1)

        for interfaceName in router.interfaces:
            if router.interfaces[interfaceName]["isConnected"] == "true":
                tn.write(b"interface " + interfaceName.encode('ascii') + b"\r\n")
                tn.write(b"no shutdown \r\n")
                tn.write(b"ip address " + str(router.interfaces[interfaceName]["ip"]).encode(
                    'ascii') + b" 255.255.255.252" + b"\r\n")

                if router.typeof == "P":
                    tn.write(b"ip ospf 10 area 0 \r\n")
                elif router.typeof == "CE":
                    tn.write(b"ip ospf 11 area 1 \r\n")
                elif router.typeof == "PE":
                    if router.interfaces[interfaceName]["RouterConnectedTypeof"] == "PE":
                        tn.write(b"ip ospf 10 area 0 \r\n")
                    elif router.interfaces[interfaceName]["RouterConnectedTypeof"] == "P":
                        tn.write(b"ip ospf 10 area 0 \r\n")
                    elif router.interfaces[interfaceName]["RouterConnectedTypeof"] == "CE":
                        tn.write(b"ip ospf 11 area 1 \r\n")

                time.sleep(0.1)
    # From here, OSPF work over PE and P router, all can ping each other

    # BGP :
    for router in listRouter:
        tn = telnetlib.Telnet("localhost", lab.nodes_inventory()[router.name]["console_port"])
        tn.write(b"\r\n")
        tn.write(b"end\r\n")
        tn.write(b"conf t \r\n")
        time.sleep(0.1)
        tn.write(b"router bgp " + router.asnumber.encode('ascii') + b"\r\n")
        for interfaceName in router.interfaces:
            if router.interfaces[interfaceName]["isConnected"] == "true":
                tn.write(b"neighbor " + str(router.interfaces[interfaceName]["RouterConnectedIp"]).encode('ascii') + b" remote-as " + router.interfaces[interfaceName]["RouterConnectedAsnumber"].encode('ascii') + b"\r\n")
        time.sleep(0.1)
        tn.write(b"address-family ipv4 unicast \r\n")
        for interfaceName in router.interfaces:
            if router.interfaces[interfaceName]["isConnected"] == "true":
                tn.write(b"network " + str(router.interfaces[interfaceName]["ipNetwork"]).encode('ascii') + b" mask 255.255.255.252 " + b"\r\n")
        time.sleep(0.1)

    # MPLS :
    tn.write(b"router ospf 11\r\n")

    for router in listRouter:
        tn = telnetlib.Telnet("localhost", lab.nodes_inventory()[router.name]["console_port"])
        tn.write(b"\r\n")
        tn.write(b"end\r\n")
        tn.write(b"conf t \r\n")
        tn.write(b"ip cef\r\n")
        time.sleep(0.1)

        for interfaceName in router.interfaces:
            if router.interfaces[interfaceName]["isConnected"] == "true":
                tn.write(b"interface " + interfaceName.encode('ascii') + b"\r\n")
                if router.typeof == "P":
                    tn.write(b"mpls ip \r\n")
                elif router.typeof == "CE":
                    pass  # CE device dont need MPLS
                elif router.typeof == "PE":
                    if router.interfaces[interfaceName]["RouterConnectedTypeof"] == "PE":
                        tn.write(b"mpls ip \r\n")
                    elif router.interfaces[interfaceName]["RouterConnectedTypeof"] == "P":
                        tn.write(b"mpls ip \r\n")
                    elif router.interfaces[interfaceName]["RouterConnectedTypeof"] == "CE":
                        pass  # CE device dont need MPLS
        time.sleep(0.1)

    for router in listRouter:
        router.showInfos()

    print('Hello World')
