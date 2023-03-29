import re
import time

import gns3fy
from tabulate import tabulate
from ipaddress import IPv4Address
import telnetlib
import json


class Router:
    def __init__(self, name, uid, typeof):
        self.name = name
        self.typeof = typeof
        self.interfaces = {}
        self.uid = uid
        self.asNumber = ""

    def __str__(self):
        return f"""
Name: {self.name} 
Uid : {self.uid}
typeof: {self.typeof}
interfaces : {self.interfaces}
asNumber  {self.asNumber}
"""

    def showInfos(self):
        print("")
        print(f"--------------------------------Name: {self.name}--------------------------------")
        print(f"Uid: {self.uid}")
        print(f"typeof: {self.typeof}")
        print(f"asNumber: {self.asNumber}")
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


def whichClientFromRouterName(name):
    if any([_ in name for _ in ["CER1", "CER2"]]):
        return "Client_A"
    if any([_ in name for _ in ["CER3", "CER4"]]):
        return "Client_B"
    else:
        return "NOT A CLIENT"

def whichAsFromRouterName(name):
    if any([_ in name for _ in ["CER1"]]):
        return "1111"
    if any([_ in name for _ in ["CER2"]]):
        return "2222"
    if any([_ in name for _ in ["CER3"]]):
        return "3333"
    if any([_ in name for _ in ["CER4"]]):
        return "4444"
    else:
        return "NO AS ON THIS ROUTER"

# Project is to setup/automate an entire network with MPLS
# Type of router : CE (Customer Edge), P(Provider), PE(Provider Edge)
if __name__ == '__main__':
    #Open json file
    with open("ConfigIntention.json", "r") as fileObject:
        jsonContent = fileObject.read()
        data = json.loads(jsonContent)
    print(data['client']['insa']['rsvp'])
    #print(data['client']['insa']['rsvp'])

    # Define the server object to establish the connection
    gns3_server = gns3fy.Gns3Connector("http://localhost:3080")
    print(
        tabulate(
            gns3_server.projects_summary(is_print=False),
            headers=["Project Name", "Project ID", "Total Nodes", "Total Links", "Status"],
        )
    )
    nameProject= ""
    for name in gns3_server.projects_summary(is_print=False):
        if name[4] == "opened":
            nameProject = name[0]
                
    # Default.rdp is actually the name of the project in GNS3
    lab = gns3fy.Project(name=nameProject, connector =gns3_server)
    lab.get()

    listRouter = []
    setReseaux = {}
    
    #Create IP @ of networks
    for i in range(4, 248, 4):
        setReseaux[int((i / 4) - 1)] = IPv4Address("10.16.1." + str(i))

    # Default.rdp is actually the name of the project in GNS3
    lab = gns3fy.Project(name=nameProject, connector =gns3_server)
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
        listRouter[i].interfaces["l0"] = {}
        listRouter[i].interfaces["l0"]['isConnected'] = "true"
        numberInRouteurName = str(re.findall(r'\d+', listRouter[i].name)[0])
        if whichTypeOfRouterFromName(listRouter[i].name) == "P":
            listRouter[i].interfaces["l0"]["ip"] = IPv4Address("1.1.3." + str(numberInRouteurName))
        elif whichTypeOfRouterFromName(listRouter[i].name) == "CE":
            listRouter[i].interfaces["l0"]["ip"] = IPv4Address("1.1.1." + str(numberInRouteurName))
        elif whichTypeOfRouterFromName(listRouter[i].name) == "PE":
            listRouter[i].interfaces["l0"]["ip"] = IPv4Address("1.1.2." + str(numberInRouteurName))

    # Add BGP AS in router object
    for router in listRouter:
        if router.typeof == "P" or router.typeof == "PE":
            router.asNumber = "1337"
        elif router.typeof == "CE":
            router.asNumber = whichAsFromRouterName(router.name)

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
                firstRouterAsnumber = router.asNumber
            elif router.uid == link.nodes[1]['node_id']:
                secondRouterConnected = router.name
                secondRouterAsnumber = router.asNumber
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

    # Add loopback address on router
    print("Add loopback address on router")
    for router in listRouter:
        tn = telnetlib.Telnet("localhost", lab.nodes_inventory()[router.name]["console_port"])
        tn.write(b"\r\n")
        tn.write(b"! Add loopback address on router \r\n")
        tn.write(b"end\r\n")
        tn.write(b"conf t \r\n")
        tn.write(b"ip cef \r\n")
        tn.write(b"router ospf 10\r\n")

        # Loopback address attribution
        tn.write(b"int loopback0\r\n")
        tn.write(b"ip address " + str(router.interfaces["l0"]["ip"]).encode('ascii') + b" 255.255.255.255" + b"\r\n")
        if router.typeof == "PE" or router.typeof == "P":
            tn.write(b"ip ospf 10 area 0\r\n")
        time.sleep(0.1)


    # Add ip address on connected interfaces
    print("Add ip address on connected interfaces")
    for router in listRouter:
        tn = telnetlib.Telnet("localhost", lab.nodes_inventory()[router.name]["console_port"])
        tn.write(b"\r\n")
        tn.write(b"! Add ip address on connected interfaces \r\n")
        tn.write(b"end\r\n")
        tn.write(b"conf t \r\n")
        for interfaceName in router.interfaces:
            if router.interfaces[interfaceName]["isConnected"] == "true" and interfaceName != "l0":
                tn.write(b"interface " + interfaceName.encode('ascii') + b"\r\n")
                tn.write(b"no shutdown \r\n")
                tn.write(b"ip address " + str(router.interfaces[interfaceName]["ip"]).encode(
                    'ascii') + b" 255.255.255.252" + b"\r\n")
            time.sleep(0.1)


    # Add OSPF in core network
    print("Add OSPF in core network")
    for router in listRouter:
        tn = telnetlib.Telnet("localhost", lab.nodes_inventory()[router.name]["console_port"])
        tn.write(b"\r\n")
        tn.write(b"! Add OSPF in core network \r\n")
        tn.write(b"end\r\n")
        tn.write(b"conf t \r\n")

        for interfaceName in router.interfaces:
            if router.interfaces[interfaceName]["isConnected"] == "true":
                if "RouterConnectedTypeof" in router.interfaces[interfaceName]:
                    tn.write(b"interface " + interfaceName.encode('ascii') + b"\r\n")
                    if router.typeof == "P":
                        tn.write(b"ip ospf 10 area 0 \r\n")
                    elif router.typeof == "PE":
                        if router.interfaces[interfaceName]["RouterConnectedTypeof"] == "P":
                            tn.write(b"ip ospf 10 area 0 \r\n")
                        elif router.interfaces[interfaceName]["RouterConnectedTypeof"] == "PE":
                            tn.write(b"ip ospf 10 area 0 \r\n")
            time.sleep(0.1)

    # Add mpls on core network
    print("Add mpls on core network")
    for router in listRouter:
        if router.typeof == "PE" or router.typeof == "P":
            tn = telnetlib.Telnet("localhost", lab.nodes_inventory()[router.name]["console_port"])
            tn.write(b"\r\n")
            tn.write(b"! Add mpls on core network \r\n")
            tn.write(b"end\r\n")
            tn.write(b"conf t \r\n")
            tn.write(b"mpls label protocol ldp \r\n")
            tn.write(b"mpls ldp router-id Loopback0 \r\n")
            tn.write(b"mpls ip \r\n")
        time.sleep(0.1)

    # Configuring MP-BGP on PE Routers
    print("Configuring MP-BGP on PE Routers")
    for router in listRouter:
        if router.typeof == "PE":
            tn = telnetlib.Telnet("localhost", lab.nodes_inventory()[router.name]["console_port"])
            tn.write(b"\r\n")
            tn.write(b"! Configuring MP-BGP on PE Routers \r\n")
            tn.write(b"end\r\n")
            tn.write(b"conf t \r\n")
            for router2 in listRouter:
                if router2.typeof == "PE":
                    tn.write(b"router bgp " + router.asNumber.encode('ascii') + b"\r\n")
                    if router.name != router2.name:
                        tn.write(b"neighbor " + str(router2.interfaces["l0"]["ip"]).encode('ascii') + b" remote-as " + router2.asNumber.encode('ascii') + b"\r\n")
                        tn.write(b"neighbor " + str(router2.interfaces["l0"]["ip"]).encode('ascii') + b" update-source lo0 \r\n")
                        tn.write(b"address-family vpnv4 \r\n")
                        tn.write(b"neighbor " + str(router2.interfaces["l0"]["ip"]).encode('ascii') + b" activate \r\n")
                        tn.write(b"neighbor " + str(router2.interfaces["l0"]["ip"]).encode('ascii') + b" next-hop-self \r\n")
                        tn.write(b"neighbor " + str(router2.interfaces["l0"]["ip"]).encode('ascii') + b" send-community both \r\n")
                time.sleep(0.1)



    # Add eBGP between CE and PE
    print("Add eBGP between CE and PE")
    for router in listRouter:
        tn = telnetlib.Telnet("localhost", lab.nodes_inventory()[router.name]["console_port"])
        if router.typeof == "CE":
            tn.write(b"\r\n")
            tn.write(b"! Add eBGP between CE and PE \r\n")
            tn.write(b"end\r\n")
            tn.write(b"conf t \r\n")
            tn.write(b"router bgp " + router.asNumber.encode('ascii') + b"\r\n")
            for interfaceName in router.interfaces:
                if router.interfaces[interfaceName]["isConnected"] == "true":
                    if "RouterConnectedTypeof" in router.interfaces[interfaceName]:
                        if router.interfaces[interfaceName]["RouterConnectedTypeof"] == "PE":
                            tn.write(b"neighbor " + str(router.interfaces[interfaceName]["RouterConnectedIp"]).encode(
                                'ascii') + b" remote-as " + str(router.interfaces[interfaceName]["RouterConnectedAsnumber"]).encode(
                                'ascii') + b"\r\n")
                            tn.write(b"network " + str(router.interfaces[interfaceName]["ipNetwork"]).encode('ascii') + b" mask 255.255.255.252 \r\n")
                time.sleep(0.1)
        elif router.typeof == "PE":
            tn.write(b"\r\n")
            tn.write(b"! Add eBGP between CE and PE \r\n")
            tn.write(b"end\r\n")
            tn.write(b"conf t \r\n")
            tn.write(b"router bgp " + router.asNumber.encode('ascii') + b"\r\n")
            for interfaceName in router.interfaces:
                if router.interfaces[interfaceName]["isConnected"] == "true":
                    if "RouterConnectedTypeof" in router.interfaces[interfaceName]:
                        if whichClientFromRouterName(router.interfaces[interfaceName]["routerConnectedName"]) != "NOT A CLIENT":
                            tn.write(b"address-family ipv4 vrf " + str(whichClientFromRouterName(router.interfaces[interfaceName]["routerConnectedName"])).encode('ascii') + b" \r\n")
                            tn.write(b"neighbor " + str(router.interfaces[interfaceName]["RouterConnectedIp"]).encode(
                                'ascii') + b" remote-as " + str(router.interfaces[interfaceName]["RouterConnectedAsnumber"]).encode(
                                'ascii') + b"\r\n")
                            tn.write(b"neighbor " + str(router.interfaces[interfaceName]["RouterConnectedIp"]).encode(
                                'ascii') + b" activate \r\n")
                time.sleep(0.1)


    # Enable MPLS on PE and P Routers
    print("Add OSPF in core network")
    for router in listRouter:
        if router.typeof == "PE" or router.typeof == "P":
            tn = telnetlib.Telnet("localhost", lab.nodes_inventory()[router.name]["console_port"])
            tn.write(b"\r\n")
            tn.write(b"! Add OSPF in core network \r\n")
            tn.write(b"end\r\n")
            tn.write(b"conf t \r\n")
            for interfaceName in router.interfaces:
                if router.interfaces[interfaceName]["isConnected"] == "true":
                    if "RouterConnectedTypeof" in router.interfaces[interfaceName]:
                        if router.interfaces[interfaceName]["RouterConnectedTypeof"] == "PE" or router.interfaces[interfaceName]["RouterConnectedTypeof"] == "P":
                            tn.write(b"interface " + interfaceName.encode('ascii') + b"\r\n")
                            tn.write(b"mpls ip \r\n")
                time.sleep(0.1)


    # Add vrf on PE
    print("Add vrf on PE")
    for router in listRouter:
        if router.typeof == "PE":
            tn = telnetlib.Telnet("localhost", lab.nodes_inventory()[router.name]["console_port"])
            tn.write(b"\r\n")
            tn.write(b"! Add vrf on PE\r\n")
            tn.write(b"end\r\n")
            tn.write(b"conf t \r\n")

            tn.write(b"ip vrf Client_A \r\n")
            tn.write(b"rd 100:100 \r\n")
            tn.write(b"route-target import 100:100 \r\n")
            tn.write(b"route-target export 100:100 \r\n")

            tn.write(b"ip vrf Client_B \r\n")
            tn.write(b"rd 200:200 \r\n")
            tn.write(b"route-target import 200:200 \r\n")
            tn.write(b"route-target export 200:200 \r\n")

            for interfaceName in router.interfaces:
                if router.interfaces[interfaceName]["isConnected"] == "true":
                    if "RouterConnectedTypeof" in router.interfaces[interfaceName]:
                        if whichClientFromRouterName(router.interfaces[interfaceName]["routerConnectedName"]) != "NOT A CLIENT":
                            tn.write(b"interface " + interfaceName.encode('ascii') + b"\r\n")
                            tn.write(b"ip vrf forwarding " + str(whichClientFromRouterName(router.interfaces[interfaceName]["routerConnectedName"])).encode('ascii') + b" \r\n")
                            tn.write(b"ip address " + str(router.interfaces[interfaceName]["ip"]).encode('ascii') + b" 255.255.255.252" + b"\r\n")
                time.sleep(0.1)

    # PE-CE BGP Configuration
    print("PE-CE BGP Configuration")
    for router in listRouter:
        if router.typeof == "PE":
            tn = telnetlib.Telnet("localhost", lab.nodes_inventory()[router.name]["console_port"])
            tn.write(b"\r\n")
            tn.write(b"! PE-CE BGP Configuration \r\n")
            tn.write(b"end\r\n")
            tn.write(b"conf t \r\n")
            tn.write(b"router bgp " + router.asNumber.encode('ascii') + b"\r\n")
            for interfaceName in router.interfaces:
                if router.interfaces[interfaceName]["isConnected"] == "true":
                    if "RouterConnectedTypeof" in router.interfaces[interfaceName]:
                        if whichClientFromRouterName(router.interfaces[interfaceName]["routerConnectedName"]) != "NOT A CLIENT":
                            tn.write(b"address-family ipv4 vrf " + str(whichClientFromRouterName(
                                router.interfaces[interfaceName]["routerConnectedName"])).encode('ascii') + b"\r\n")

                            tn.write(b"neighbor " + str(router.interfaces[interfaceName]["RouterConnectedIp"]).encode(
                                'ascii') + b" remote-as " + router.interfaces[interfaceName]["RouterConnectedAsnumber"].encode('ascii') + b"\r\n")
                time.sleep(0.1)
    for router in listRouter:
         router.showInfos()
    listRouter[0].showInfos()
    print('Hello World')