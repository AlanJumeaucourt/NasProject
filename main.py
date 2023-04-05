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


def whichVrfFromRouterName(name):
    for client in data["client"]:
        for link in data["client"][client]["link"]:
            if name in link.split("&"):
                return (link)


def wichRtFromRouterName(name):
    links = []
    for client in data["client"]:
        for link in data["client"][client]["link"]:
            if name in link.split("&"):
                links.append(numberInString(link) + ":" + numberInString(link))
    return links


def whichAsFromRouterName(name):
    for client in data["client"]:
        for router in data["client"][client]["ASrouterIP"]:
            if router == name:
                return data["client"][client]["ASrouterIP"][router]


def numberInString(text):
    final = ""
    for letter in text:
        if letter.isdigit():
            final += letter
    return str(final)


def AddLoopbackAddressOnRouter(router):
    tn = telnetlib.Telnet("localhost", lab.nodes_inventory()[router.name]["console_port"])
    tn.write(b"\r\n")
    tn.write(b"! Add loopback address on router \r\n")
    tn.write(b"end\r\n")
    tn.write(b"conf t \r\n")
    tn.write(b"ip cef \r\n")
    tn.write(b"router ospf 10\r\n")

    # Loopback address attribution
    tn.write(b"int loopback0\r\n")
    tn.write(b"ip address "
             + str(router.interfaces["l0"]["ip"]).encode('ascii')
             + b" 255.255.255.255" + b"\r\n")

    if router.typeof == "PE" or router.typeof == "P":
        tn.write(b"ip ospf 10 area 0\r\n")
    time.sleep(0.1)


def addIpAddressOnConnectedInterfaces(router, interfaceName):
    tn = telnetlib.Telnet("localhost", lab.nodes_inventory()[router.name]["console_port"])
    tn.write(b"\r\n")
    tn.write(b"! Add ip address on connected interfaces \r\n")
    tn.write(b"end\r\n")
    tn.write(b"conf t \r\n")
    if router.interfaces[interfaceName]["isConnected"] == "true" and interfaceName != "l0":
        tn.write(b"interface "
                 + interfaceName.encode('ascii')
                 + b"\r\n")

        tn.write(b"no shutdown \r\n")

        tn.write(b"ip address "
                 + str(router.interfaces[interfaceName]["ip"]).encode('ascii')
                 + b" 255.255.255.252"
                 + b"\r\n")
    time.sleep(0.1)


def addOspfOnPeAndPRouters(router, interfaceName):
    tn = telnetlib.Telnet("localhost", lab.nodes_inventory()[router.name]["console_port"])
    tn.write(b"\r\n")
    tn.write(b"! Add OSPF in core network \r\n")
    tn.write(b"end\r\n")
    tn.write(b"conf t \r\n")

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


def activateMplsOnPeAndPRouters(router):
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


def enableMplsOnPeAndPRouters(router, interfaceName):
    if router.typeof == "PE" or router.typeof == "P":
        tn = telnetlib.Telnet("localhost", lab.nodes_inventory()[router.name]["console_port"])
        tn.write(b"\r\n")
        tn.write(b"! Enable MPLS on PE and P Routers \r\n")
        tn.write(b"end\r\n")
        tn.write(b"conf t \r\n")
        if router.interfaces[interfaceName]["isConnected"] == "true":
            if "RouterConnectedTypeof" in router.interfaces[interfaceName]:
                if router.interfaces[interfaceName]["RouterConnectedTypeof"] == "PE" or \
                        router.interfaces[interfaceName]["RouterConnectedTypeof"] == "P":
                    tn.write(b"interface "
                             + interfaceName.encode('ascii')
                             + b"\r\n")

                    tn.write(b"mpls ip \r\n")
    time.sleep(0.1)


def addVrfOnPe(router, interfaceName):
    if router.typeof == "PE":
        tn = telnetlib.Telnet("localhost", lab.nodes_inventory()[router.name]["console_port"])
        tn.write(b"\r\n")
        tn.write(b"! Add vrf on PE\r\n")
        tn.write(b"end\r\n")
        tn.write(b"conf t \r\n")
        if router.interfaces[interfaceName]["isConnected"] == "true":
            if "routerConnectedName" in router.interfaces[interfaceName]:
                if router.interfaces[interfaceName]["RouterConnectedTypeof"] == "CE":
                    tn.write(b"ip vrf "
                             + str(router.interfaces[interfaceName]["routerConnectedName"]).encode('ascii')
                             + b" \r\n")

                    tn.write(b"rd "
                             + str(router.interfaces[interfaceName]["RouterConnectedAsnumber"]).encode('ascii')
                             + b":"
                             + str(numberInString(str(whichVrfFromRouterName(router.interfaces[interfaceName]["routerConnectedName"])))).encode('ascii')
                             + b" \r\n")

                    for rt in wichRtFromRouterName(router.interfaces[interfaceName]["routerConnectedName"]):
                        tn.write(b"route-target import "
                                 + str(rt).encode('ascii')
                                 + b" \r\n")
                        tn.write(b"route-target export "
                                 + str(rt).encode('ascii')
                                 + b" \r\n")

                    tn.write(b"interface "
                             + interfaceName.encode('ascii')
                             + b"\r\n")

                    tn.write(b"ip vrf forwarding "
                             + str(router.interfaces[interfaceName]["routerConnectedName"]).encode('ascii')
                             + b" \r\n")

                    tn.write(b"ip address "
                             + str(router.interfaces[interfaceName]["ip"]).encode('ascii')
                             + b" 255.255.255.252" + b"\r\n")
    time.sleep(0.1)


def eBgpConfigurationOnCe(router, interfaceName):
    if router.typeof == "CE":
        tn = telnetlib.Telnet("localhost", lab.nodes_inventory()[router.name]["console_port"])
        tn.write(b"\r\n")
        tn.write(b"! Add eBGP between CE and PE \r\n")
        tn.write(b"end\r\n")
        tn.write(b"conf t \r\n")
        tn.write(b"router bgp " + str(router.asNumber).encode('ascii') + b"\r\n")
        if router.interfaces[interfaceName]["isConnected"] == "true":
            if "RouterConnectedTypeof" in router.interfaces[interfaceName]:
                if router.interfaces[interfaceName]["RouterConnectedTypeof"] == "PE":
                    tn.write(b"neighbor "
                             + str(router.interfaces[interfaceName]["RouterConnectedIp"]).encode('ascii')
                             + b" remote-as "
                             + str(router.interfaces[interfaceName]["RouterConnectedAsnumber"]).encode('ascii')
                             + b"\r\n")

                    tn.write(b"network " + str(router.interfaces[interfaceName]["ipNetwork"]).encode(
                        'ascii') + b" mask 255.255.255.252 \r\n")
    time.sleep(0.1)


def eBgpConfigurationOnPe(router, interfaceName):
    if router.typeof == "PE":
        tn = telnetlib.Telnet("localhost", lab.nodes_inventory()[router.name]["console_port"])
        tn.write(b"\r\n")
        tn.write(b"! Add eBGP between CE and PE \r\n")
        tn.write(b"end\r\n")
        tn.write(b"conf t \r\n")
        tn.write(b"router bgp " + router.asNumber.encode('ascii') + b"\r\n")
        if router.interfaces[interfaceName]["isConnected"] == "true":
            if "RouterConnectedTypeof" in router.interfaces[interfaceName]:
                if "routerConnectedName" in router.interfaces[interfaceName]:
                    if router.interfaces[interfaceName]["RouterConnectedTypeof"] == "CE":
                        tn.write(b"address-family ipv4 vrf "
                                 + str(router.interfaces[interfaceName]["routerConnectedName"]).encode('ascii')
                                 + b" \r\n")

                        tn.write(b"neighbor "
                                 + str(router.interfaces[interfaceName]["RouterConnectedIp"]).encode('ascii')
                                 + b" remote-as "
                                 + str(router.interfaces[interfaceName]["RouterConnectedAsnumber"]).encode('ascii')
                                 + b"\r\n")

                        tn.write(b"neighbor "
                                 + str(router.interfaces[interfaceName]["RouterConnectedIp"]).encode('ascii')
                                 + b" activate \r\n")
    time.sleep(0.1)


def iBgpConfigurationOnPe(router):
    if router.typeof == "PE":
        tn = telnetlib.Telnet("localhost", lab.nodes_inventory()[router.name]["console_port"])
        tn.write(b"\r\n")
        tn.write(b"! Configuring MP-BGP on PE Routers \r\n")
        tn.write(b"end\r\n")
        tn.write(b"conf t \r\n")
        for router2 in listRouter:
            if router2.typeof == "PE":
                tn.write(b"router bgp "
                         + router.asNumber.encode('ascii')
                         + b"\r\n")

                if router.name != router2.name:
                    tn.write(b"neighbor "
                             + str(router2.interfaces["l0"]["ip"]).encode('ascii')
                             + b" remote-as " + router2.asNumber.encode('ascii')
                             + b"\r\n")

                    tn.write(b"neighbor "
                             + str(router2.interfaces["l0"]["ip"]).encode('ascii')
                             + b" update-source lo0 \r\n")

                    tn.write(b"address-family vpnv4 \r\n")

                    tn.write(b"neighbor "
                             + str(router2.interfaces["l0"]["ip"]).encode('ascii')
                             + b" activate \r\n")

                    tn.write(b"neighbor "
                             + str(router2.interfaces["l0"]["ip"]).encode('ascii')
                             + b" next-hop-self \r\n")

                    tn.write(b"neighbor "
                             + str(router2.interfaces["l0"]["ip"]).encode('ascii')
                             + b" send-community both \r\n")
            time.sleep(0.1)


# Project is to setup/automate an entire network with MPLS
# Type of router : CE (Customer Edge), P(Provider), PE(Provider Edge)
if __name__ == '__main__':
    # Open json file
    with open("ConfigIntention.json", "r") as fileObject:
        jsonContent = fileObject.read()
        data = json.loads(jsonContent)

    # Connect to GNS3 API
    gns3_server = gns3fy.Gns3Connector("http://localhost:3080")
    nameProject = ""
    for name in gns3_server.projects_summary(is_print=False):
        if name[4] == "opened":
            nameProject = name[0]
    lab = gns3fy.Project(name=nameProject, connector=gns3_server)
    lab.get()


    listRouter = []
    listReseaux = []

    # Create IP @ of networks
    for i in range(4, 248, 4):
        listReseaux.append(IPv4Address("10.16.1." + str(i)))


    exit()
    # Add object router in list with name and uid
    print("\nStarting list and create router object in listRouteur")
    for node in lab.nodes:
        listRouter.append(Router(node.name, node.node_id, whichTypeOfRouterFromName(node.name)))

    # Add interface in router object
    for i in range(len(listRouter)):
        for port in lab.nodes[i].ports:
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
        print("    " + firstRouterConnected + link.nodes[0]['label']['text']
              + " is connected to "
              + secondRouterConnected
              + link.nodes[1]['label']['text'])
        networkIp = listReseaux[0]
        firstRouterIp = listReseaux[0] + 1
        secondRouterIp = listReseaux[0] + 2
        listReseaux.remove(listReseaux[0])

        for router in listRouter:
            if router.name == firstRouterConnected:
                for interfaceName in router.interfaces:
                    if interfaceName == link.nodes[0]['label']['text']:
                        router.interfaces[interfaceName]['isConnected'] = "true"
                        router.interfaces[interfaceName]['routerConnectedName'] = secondRouterConnected
                        router.interfaces[interfaceName]['routerConnectedInterfaceName'] = link.nodes[1]['label']['text']
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
                        router.interfaces[interfaceName]['routerConnectedInterfaceName'] = link.nodes[0]['label']['text']
                        router.interfaces[interfaceName]['RouterConnectedAsnumber'] = firstRouterAsnumber
                        router.interfaces[interfaceName]['RouterConnectedIp'] = firstRouterIp
                        router.interfaces[interfaceName]['RouterConnectedTypeof'] = whichTypeOfRouterFromName(
                            firstRouterConnected)
                        router.interfaces[interfaceName]['ipNetwork'] = networkIp
                        router.interfaces[interfaceName]['ip'] = secondRouterIp


def autoAddConfigOnRouter(router):
    # To do :
    # IP attribution for new router not working after first iteration
    #

    activateMplsOnPeAndPRouters(router)
    iBgpConfigurationOnPe(router)
    for interfaceName in router.interfaces:
        if router.interfaces[interfaceName]["isConnected"] == "true" and interfaceName != "l0":
            addIpAddressOnConnectedInterfaces(router, interfaceName)
            enableMplsOnPeAndPRouters(router, interfaceName)
            addVrfOnPe(router, interfaceName)
            eBgpConfigurationOnCe(router, interfaceName)
            eBgpConfigurationOnPe(router, interfaceName)


def autoRemoveConfigOnRouter(router):
    pass
    # To do :
    # If PE : erase config for all CE that attached to him
    # If PE : remove i-bgp peer on all other PE
    # If PE : erase his config

    # If CE : delete VRF on his attached PE
    # If CE : delete route target on all PE that implicate this CE
    # If CE : erase his config

    # If P : delete IP on connected router to this P
    # If P : erase his config
    # If P : ? if the P is connected to a PE, what to do ? erase all config on the PE and CE ? or nothing else than previous.


def removeCeRouter(router):

    ListConnectedRouter = []
    for interfaceName in router.interfaces:
        if router.interfaces[interfaceName]["isConnected"] == "true" and interfaceName != "l0":
            ListConnectedRouter.append(router.interfaces[interfaceName]["routerConnectedName"])

    # delete VRF on his attached PE and default interface
    for connectedRouter in ListConnectedRouter :
        for router2 in listRouter:
            if router2.name == connectedRouter:
                for interfaceName in router2.interfaces:
                    if router2.interfaces[interfaceName]["isConnected"] == "true" and "routerConnectedName" in router2.interfaces[interfaceName]:
                        if router2.interfaces[interfaceName]["routerConnectedName"] == router.name :
                            tn = telnetlib.Telnet("localhost", lab.nodes_inventory()[router2.name]["console_port"])
                            tn.write(b"\r\n")
                            tn.write(b"! removeCeRouter " + router2.name.encode('ascii') + b" VRF & interface \r\n")
                            tn.write(b"end\r\n")
                            tn.write(b"conf t \r\n")
                            tn.write(b"no ip vrf " + router.name.encode('ascii') + b" \r\n")
                            tn.write(b"default interface " + interfaceName.encode('ascii') + b" \r\n")
                    time.sleep(0.1)

            # delete RT if the CE have vpn route with other CE
            elif router2.typeof == "PE":
                for interfaceName in router2.interfaces:
                    if "routerConnectedName" in router2.interfaces[interfaceName]:
                        if router2.interfaces[interfaceName]["RouterConnectedTypeof"] == "CE":
                            tn = telnetlib.Telnet("localhost", lab.nodes_inventory()[router2.name]["console_port"])
                            tn.write(b"\r\n")
                            tn.write(b"! removeCeRouter " + router2.name.encode('ascii') + b" RT \r\n")
                            tn.write(b"end\r\n")
                            tn.write(b"conf t \r\n")
                            tn.write(b"ip vrf "
                                     + str(router2.interfaces[interfaceName]["routerConnectedName"]).encode('ascii')
                                     + b" \r\n")
                            for rt in wichRtFromRouterName(router.name):
                                tn.write(b"no route-target import "
                                         + str(rt).encode('ascii')
                                         + b" \r\n")
                                tn.write(b"no route-target export "
                                         + str(rt).encode('ascii')
                                         + b" \r\n")
                    time.sleep(0.1)

    # erase config
    tn = telnetlib.Telnet("localhost", lab.nodes_inventory()[router.name]["console_port"])
    tn.write(b"\r\n")
    tn.write(b"! removeCeRouter " + router.name.encode('ascii') + b" RT \r\n")
    tn.write(b"end\r\n")
    tn.write(b"conf t \r\n")
    tn.write(b"config-register 0x2142 \r\n")
    tn.write(b"end \r\n")
    tn.write(b"reload \r\n")
    time.sleep(0.25)
    tn.write(b"y \r\n")
    tn.write(b" \r\n")


# Configuring router via telnet
for router in listRouter:
    autoAddConfigOnRouter(router)

# for router in listRouter:
#     if router.name == "CER3":
#         removeCeRouter(router)

for router in listRouter:
     router.showInfos()
# listRouter[0].showInfos()


def autoAddConfigOnRouterCE(routerCE):
    if routerCE.name == "CER6":
        for interfaceNameCE in routerCE.interfaces:
            if interfaceNameCE["isConnected"] == "true":
                addIpAddressOnConnectedInterfaces(routerCE, interfaceNameCE)
                if interfaceNameCE["RouterConnectedTypeof"] == "PE":
                    routerPER = interfaceNameCE["RouterConnectedName"]
                    for searchrouter in listRouter:
                        if searchrouter == routerPER:
                            for interfaceNamePER in searchrouter.interfaces:
                                if interfaceNamePER["RouterConnectedName"] == "CER6":
                                    addIpAddressOnConnectedInterfaces(searchrouter, interfaceNamePER)
                                    addVrfOnPe(searchrouter, interfaceNamePER)
                                    eBgpConfigurationOnPe(searchrouter, interfaceNamePER)
                                    eBgpConfigurationOnCe(routerCE, interfaceNameCE)
                                    iBgpConfigurationOnPe(searchrouter)
                    

print('Hello World')




def removePErouter(router):

    ListConnectedRouter = []
    for interfaceName in router.interfaces:
        if router.interfaces[interfaceName]["isConnected"] == "true" and interfaceName != "l0":
            ListConnectedRouter.append(router.interfaces[interfaceName]["routerConnectedName"])

    for router2 in listRouter:
        if router2.typeof == "PE":
            for interfaceName in router2.interfaces:
                if "routerConnectedName" in router2.interfaces[interfaceName]:
                    if router2.interfaces[interfaceName]["RouterConnectedTypeof"] == "CE":
                        tn = telnetlib.Telnet("localhost", lab.nodes_inventory()[router2.name]["console_port"])
                        tn.write(b"\r\n")
                        tn.write(b"! removeCeRouter " + router2.name.encode('ascii') + b" RT \r\n")
                        tn.write(b"end\r\n")
                        tn.write(b"conf t \r\n")
                        tn.write(b"ip vrf "
                                + str(router2.interfaces[interfaceName]["routerConnectedName"]).encode('ascii')
                                + b" \r\n")
                        for rt in wichRtFromRouterName(router.name):
                            tn.write(b"no route-target import "
                                    + str(rt).encode('ascii')
                                    + b" \r\n")
                            tn.write(b"no route-target export "
                                    + str(rt).encode('ascii')
                                    + b" \r\n")
                time.sleep(0.1)

    for router3 in ListConnectedRouter:
        if whichTypeOfRouterFromName(router.name) == "CE":
            removeCeRouter(router3)
        elif whichTypeOfRouterFromName(router.name) == "PE" or "P":
            for router2 in listRouter:
                if router2.name == ListConnectedRouter:
                    for interfaceName in router2.interfaces:
                        if router2.interfaces[interfaceName]["isConnected"] == "true" and "routerConnectedName" in router2.interfaces[interfaceName]:
                            if router2.interfaces[interfaceName]["routerConnectedName"] == router.name :
                                tn = telnetlib.Telnet("localhost", lab.nodes_inventory()[router2.name]["console_port"])
                                tn.write(b"\r\n")
                                tn.write(b"! removePRouter " + router2.name.encode('ascii') + b" \r\n")
                                tn.write(b"end\r\n")
                                tn.write(b"conf t \r\n")
                    
                                tn.write(b"default interface " + interfaceName.encode('ascii') + b" \r\n")
                        time.sleep(0.1)
 




    # erase config
    tn = telnetlib.Telnet("localhost", lab.nodes_inventory()[router.name]["console_port"])
    tn.write(b"\r\n")
    tn.write(b"! removeCeRouter " + router.name.encode('ascii') + b" RT \r\n")
    tn.write(b"end\r\n")
    tn.write(b"conf t \r\n")
    tn.write(b"config-register 0x2142 \r\n")
    tn.write(b"end \r\n")
    tn.write(b"reload \r\n")
    time.sleep(0.25)
    tn.write(b"y \r\n")
    tn.write(b" \r\n")

    
def remove(router):
    if whichTypeOfRouterFromName(router.name) == "CE":
        removeCeRouter(router)
    elif whichAsFromRouterName(router.name) == "PE":
        removePErouter(router)
    elif whichTypeOfRouterFromName(router.name) == "P":
        removePRouter(router)



def addPErouter(router):
    AddLoopbackAddressOnRouter(router)
    activateMplsOnPeAndPRouters(router)

    for interfaceName in router.interfaces:
        if router.interfaces[interfaceName]["isConnected"] == "true" and interfaceName != "l0":
            if whichTypeOfRouterFromName(router.interfaces[interfaceName]['routerConnectedName']) == "P":
                addIpAddressOnConnectedInterfaces(router, interfaceName)
                addOspfOnPeAndPRouters(router, interfaceName)
                enableMplsOnPeAndPRouters(router, interfaceName)
                eBgpConfigurationOnPe(router, interfaceName)

    
    iBgpConfigurationOnPe(router)


