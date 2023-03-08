import gns3fy
from tabulate import tabulate


class Routeur:
    def __init__(self, name, uid, typeof):
        self.name = name
        self.typeof = typeof
        self.interfaces = {}
        self.uid = uid

    def __str__(self):
        return f"""Name: {self.name} 
Uid : {self.uid}
typeof: {self.typeof}
Interfaces : {self.interfaces}
"""


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
    for node in lab.nodes:
        listRouteur.append(Routeur(node.name, node.node_id, "Pe"))

    for i in range(len(listRouteur)):
        for port in lab.nodes[i].ports:
            listRouteur[i].interfaces[port['name']] = "Not Connected"

    print(listRouteur[0])
    # for router in listRouteur:
    #     router.interfaces[lab.nodes.ports] = "test"

    print("interface de la premiere connection : " + lab.links[0].nodes[0]['label']['text'])
    print("interface de la deuxieme connection : " + lab.links[0].nodes[1]['label']['text'])
    print(lab.links[0].nodes[0]['node_id'])
    firstRouterConnected = ""
    secondRouterConnected = ""
    for routeur in listRouteur:
        if routeur.uid == lab.links[0].nodes[0]['node_id']:
            firstRouterConnected = routeur.name
        elif routeur.uid == lab.links[0].nodes[1]['node_id']:
            secondRouterConnected = routeur.name
    print(firstRouterConnected + " is connected to " + secondRouterConnected)


    print('Hello World')