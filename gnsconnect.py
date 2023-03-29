import gns3fy
from tabulate import tabulate

class gnsconnect:
    def connect():
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

    