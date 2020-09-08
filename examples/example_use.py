from output import *

# Create instances and attributes
ei = EquivalentInjection()
ei.IdentifiedObject_mRID = 'EquivalentNW243'

# `list` type attributes might use `add_` methods to insert elements
t = Terminal(Terminal_sequenceNumber=1)
ei.add_ConductingEquipment_Terminals(t)

# The backward linkage between instances is automatic, e.g., 
# the last command is equivalent to
# t.Terminal_ConductingEquipment = ei
# (The bi-directional link must be explicitly specified
# in the rdf:Property, inside the CIMXML file.)

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

# Create CIMRDF document instance
doc1 = DocumentCIMRDF()

# Add elements individually
doc1.add_elements([ei]) # ...

# Or insert them into the document recursively 
# (including linked instances)
doc1.add_recursively(s)

# Print doc to stdout (for debug purposes)
doc1.dump()

###################################################
# Convert doc into a string
string = doc1.tostring()

# Or an ElementTree
etree = doc1.pack()

# Or to a file
doc1.tofile('example_instance.xml')

###################################################

# Retrieve back elements from string
doc2 = DocumentCIMRDF()
doc2.fromstring(string)

# or from a file
doc3 = DocumentCIMRDF()
doc3.fromfile('example_instance.xml')

# Access instances in `resources` attribute
instances = doc2.resources
print(instances)

# Print doc to stdout again for comparison
doc2.dump()