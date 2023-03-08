import gns3fy
from tabulate import tabulate


class Routeur:
    def __init__(self, name, typeof):
        self.name = name
        self.typeof = typeof

    def __str__(self):
        return f"""
Name: {self.name} 
typeof: {self.typeof}
"""


# Project is to setup/automate an entire network with MPLS
# Type of router : CE (Customer Edge), P(Provider), PE(Provider Edge)
if __name__ == '__main__':
    # Define the server object to establish the connection
    gns3_server = gns3fy.Gns3Connector("http://localhost:3080")
    print(gns3_server.projects_summary(is_print=False))

    lab = gns3fy.Project(name="Default.rdp", connector=gns3_server)
    lab.get()
    for node in lab.nodes:
        print(f"Node: {node.name}")
        for port in node.ports:
            print(port)
            print(f"Name: {port['name']}")


    print('Hello World')
    r1 = Routeur("r1", "CE")

    print(r1)
