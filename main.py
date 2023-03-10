import time

import gns3fy
from tabulate import tabulate
from ipaddress import IPv4Address
import telnetlib


class Routeur:
    def __init__(self, name, uid, typeof):
        self.name = name
        self.typeof = typeof
        self.interfaces = {}
        self.uid = uid

    def __str__(self):
        return f"""
Name: {self.name} 
Uid : {self.uid}
typeof: {self.typeof}
interfaces : {self.interfaces}
"""
    def showInfos(self):
        print("")
        print(f"--------------------------------Name: {self.name}--------------------------------")
        print(f"Uid: {self.uid}")
        print(f"typeof: {self.typeof}")
        for interfaceName in self.interfaces:
            print(f"interfaces : {interfaceName}")
            for key in self.interfaces[interfaceName]:
                print(f"    {key} : {self.interfaces[interfaceName][key]}")


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

    listRouteur = []
    setReseaux = {}

    for i in range(4, 248, 4):
        setReseaux[int((i/4)-1)] = IPv4Address("10.16.1." + str(i))

    # Default.rdp is actually the name of the project in GNS3
    lab = gns3fy.Project(name="Default.rdp", connector=gns3_server)
    lab.get()

    # Add object router in list with name and uid
    print("\n    Starting list and create router object in listRouteur")
    for node in lab.nodes:
        typeof = ""
        if node.name.startswith("PE"):
            typeof = "PE"
        elif node.name.startswith("P"):
            typeof = "P"
        elif node.name.startswith("CE"):
            typeof = "CE"
        print(typeof)
        listRouteur.append(Routeur(node.name, node.node_id, typeof))

    # Add interface of router
    for i in range(len(listRouteur)):
        for port in lab.nodes[i].ports:
            # Commented because no need for long name, maybe will be usefull later in project
            # listRouteur[i].interfaces[port['name']] = {}
            # listRouteur[i].interfaces[port['name']]['isConnected'] = "false"
            # listRouteur[i].interfaces[port['name']]['shortName'] = port['short_name']
            listRouteur[i].interfaces[port['short_name']] = {}
            listRouteur[i].interfaces[port['short_name']]['isConnected'] = "false"

    print(listRouteur[0])

    # finding the link between routers
    print("\n    Starting finding the link between routers")
    for i, link in enumerate(lab.links):
        firstRouterConnected = ""
        secondRouterConnected = ""
        firstRouterInterface = ""
        networkIp = ""
        firstRouterIp = ""
        SecondRouterIp = ""
        for routeur in listRouteur:
            if routeur.uid == link.nodes[0]['node_id']:
                firstRouterConnected = routeur.name
            elif routeur.uid == link.nodes[1]['node_id']:
                secondRouterConnected = routeur.name
        print(firstRouterConnected + link.nodes[0]['label']['text'] + " is connected to " + secondRouterConnected +
              link.nodes[1]['label']['text'])
        networkIp = setReseaux[i]
        firstRouterIp = setReseaux[i]+1
        SecondRouterIp = setReseaux[i]+2

        for routeur in listRouteur:
            if routeur.name == firstRouterConnected:
                for interfaceName in routeur.interfaces:
                    if interfaceName == link.nodes[0]['label']['text']:
                        routeur.interfaces[interfaceName]['isConnected'] = "true"
                        routeur.interfaces[interfaceName]['routerConnectedName'] = secondRouterConnected
                        routeur.interfaces[interfaceName]['routerConnectedInterfaceName'] = link.nodes[1]['label'][
                            'text']
                        routeur.interfaces[interfaceName]['RouterConnectedIp'] = SecondRouterIp
                        routeur.interfaces[interfaceName]['ipNetwork'] = networkIp
                        routeur.interfaces[interfaceName]['ip'] = firstRouterIp

            elif routeur.name == secondRouterConnected:
                for interfaceName in routeur.interfaces:
                    if interfaceName == link.nodes[1]['label']['text']:
                        routeur.interfaces[interfaceName]['isConnected'] = "true"
                        routeur.interfaces[interfaceName]['routerConnectedName'] = firstRouterConnected
                        routeur.interfaces[interfaceName]['routerConnectedInterfaceName'] = link.nodes[0]['label'][
                            'text']
                        routeur.interfaces[interfaceName]['RouterConnectedIp'] = firstRouterIp
                        routeur.interfaces[interfaceName]['ipNetwork'] = networkIp
                        routeur.interfaces[interfaceName]['ip'] = SecondRouterIp

    for routeur in listRouteur:
        routeur.showInfos()
    print('Hello World')


    # Telnet things

    tn = telnetlib.Telnet("localhost",5000)
    tn.write(b"\r\n")
    tn.write(b"end\r\n")
    tn.write(b"conf t \r")
    tn.write(b"interface fa0/0\r")
    tn.write(b"ip address 10.181.23.1 255.255.255.0\r")
    tn.write(b"no shutdown\r")
    tn.write(b"\r\n")


    for routeur in listRouteur:
        tn = telnetlib.Telnet("localhost", lab.nodes_inventory()[routeur.name]["console_port"])
        tn.write(b"\r\n")
        tn.write(b"end\r\n")
        tn.write(b"conf t \r")

        print(routeur.name)
        for interfaceName in routeur.interfaces:
            if routeur.interfaces[interfaceName]["isConnected"] == "true":
                tn.write(b"interface " + interfaceName.encode('ascii') + b"\r\n")
                tn.write(b"no shutdown \r\n")
                tn.write(b"ip address " + str(routeur.interfaces[interfaceName]["ip"]).encode('ascii') + b" 255.255.255.252" + b"\r\n")
                time.sleep(0.1)



    print(lab.nodes_inventory()["CER1"]["console_port"])
