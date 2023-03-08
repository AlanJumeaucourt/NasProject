import gns3fy
from tabulate import tabulate


class Routeur:
    def __init__(self, name, uid, typeof):
        self.name = name
        self.typeof = typeof
        self.interfacesName = {}
        self.interfacesShortName = {}
        self.uid = uid

    def __str__(self):
        return f"""
Name: {self.name} 
Uid : {self.uid}
typeof: {self.typeof}
Interfaces : {self.interfacesName}
interfacesShortName : {self.interfacesShortName}"""


# Project is to setup/automate an entire network with MPLS
# Type of router : CE (Customer Edge), P(Provider), PE(Provider Edge)
if __name__ == '__main__':
    # Define the server object to establish the connection
    gns3_server = gns3fy.Gns3Connector("http://localhost:3080")
    print(gns3_server.projects_summary(is_print=False))

    listRouteur = []

    lab = gns3fy.Project(name="Default.rdp", connector=gns3_server)
    lab.get()
    print(lab.nodes[0].ports[0]['name'])

    # Add object router in list with name and uid
    print("\n    Starting list and create router object in listRouteur")
    for node in lab.nodes:
        listRouteur.append(Routeur(node.name, node.node_id, "Pe"))
    for i in range(len(listRouteur)):
        for port in lab.nodes[i].ports:
            listRouteur[i].interfacesName[port['name']] = "Not Connected"
            listRouteur[i].interfacesShortName[port['short_name']] = "Not Connected"

    print(listRouteur[0])

    print("\n    Starting finding the link between routers")
    for link in lab.links:
        firstRouterConnected = ""
        secondRouterConnected = ""
        firstRouterInterface = ""
        for routeur in listRouteur:
            if routeur.uid == link.nodes[0]['node_id']:
                firstRouterConnected = routeur.name
            elif routeur.uid == link.nodes[1]['node_id']:
                secondRouterConnected = routeur.name
        print(firstRouterConnected + link.nodes[0]['label']['text'] + " is connected to " + secondRouterConnected + link.nodes[1]['label']['text'])

        for routeur in listRouteur:
            if routeur.name == firstRouterConnected:
                routeur.interfacesShortName[link.nodes[0]['label']['text']] = secondRouterConnected + "|" + link.nodes[1]['label']['text']
            elif routeur.name == secondRouterConnected:
                routeur.interfacesShortName[link.nodes[1]['label']['text']] = firstRouterConnected + "|" + link.nodes[0]['label']['text']


    print(listRouteur[0])
    print(listRouteur[1])

    print('Hello World')
