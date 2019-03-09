import hash_ring

reglist = ['192.168.0.200:5000', '192.168.0.202:5000', '192.168.0.203:5000', '192.168.0.204:5000', '192.168.0.205:5000']

ring = hash_ring.HashRing(reglist)

print ring.get_node('57')
print ring.get_node('63')
print ring.get_node('144')
print ring.get_node('12')
print ring.get_node('99')
