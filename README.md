# cimrdf.py
Generate Python data structures from CIM RDF profiles, parse and serialize CIM-compliant information objects, according to IEC 61970-501 standard.

1. Generate your RDF artifact
2. Convert to Python data structures with :
```
generator.py input_filename.xml output.py
```
***To create CIM RDF instances***
3a. Use the generated classes from output_filename.py to create your instance
```
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
```
4a. Create a new document instance with all objects
```
new = DocumentCIMRDF([ei, t, s, t1, t2, cn])
```
The available functions are:
  * ***new.dump()***: Pretty-Print the document to stdout
  * ***new.pack()***: Get the document's ElementTree (xml.etree.ElementTree) instance
  * ***new.tostring()***: Get the XML stringified version of the document
  * ***new.add_elements( ... )***: Add new elements (one or a list) to the document
  
***To parse CIM RDF instances***
3b. Use proper functions to parse file or string.
```
instances = fromstring(xmlstring)
print(instances)
// [list of instances]
```
The available functions are:
  * ***fromstring(xmlstring)***: Get instances from CIM RDF string
  * ***fromfile(filename)***: Get instances from CIM RDF file
