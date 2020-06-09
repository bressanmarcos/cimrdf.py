from output import *

ei = EquivalentInjection()
ei.IdentifiedObject_mRID = 'EquivalentNW243'
t = Terminal()
t.Terminal_sequenceNumber = 1
t.Terminal_ConductingEquipment = ei

s = Switch()
s.Switch_normalOpen = True
s.IdentifiedObject_mRID = 'SW12'
t1 = Terminal()
t1.Terminal_sequenceNumber = 1
t1.Terminal_ConductingEquipment = s
t2 = Terminal()
t2.Terminal_sequenceNumber = 2
t2.Terminal_ConductingEquipment = s

cn = ConnectivityNode()
cn.IdentifiedObject_mRID = 'Node23'
cn.ConnectivityNode_Terminals = [t1, t]

new = DocumentCIMRDF([ei, t, s, t1, t2, cn])

# Print to stdout
new.dump()

###################################################
# Convert to string
string = new.tostring()

###################################################

# Read the string to recover instances
instances = fromstring(string)
print(instances)

renew = DocumentCIMRDF()
renew.add_elements(list(instances.values()))

# Print to stdout again for comparison
renew.dump()