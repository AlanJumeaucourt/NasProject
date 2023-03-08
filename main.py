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
    print('Hello World')
    r1 = Routeur("r1", "CE")

    print(r1)
