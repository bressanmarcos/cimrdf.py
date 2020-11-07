# cimrdf.py - An open source tool to handle CIM RDF (IEC 61970-501) documents in Python
Generate Python data structures from CIM RDF profiles, parse and serialize CIM-compliant information objects, according to IEC 61970-501 standard.

With it, it is possible to convert a CIM RDF document in XML format to a Python module (.py) containing a class structure. This module can be used later to create, serialize, read and export RDF / XML documents that follow the semantics of the original RDFS document used during its generation.

The utility applies the specifications of the IEC 61970-501 standard for the treatment of RDF documents. I tried to develop it in a way that made its use as simple as possible at the time of development.

If you want to contribute to the project (new features, code refactoring, test coverage ...), don't hesitate to open a new pull request.

## Installing

```bash
$ pip install cimrdf.py
```
or
```bash
$ git clone https://github.com/bressanmarcos/cimrdf.py.git
$ cd cimrdf.py
$ python setup.py install 
```

## Using
1. Create your CIM RDF artifact with your preferred utils
2. Convert it into Python data structures with:
```
cimrdfpy input-rdfs.xml output.py
```

## Creating CIM RDF instances
3. Use the generated classes from output.py to create your instances
```python
from output import *

ei = EquivalentInjection()
ei.mRID = 'EquivalentNW243'
t = Terminal()
t.sequenceNumber = 1
# This next command reciprocally associates the `t` Terminal to `ei` EquivalentInjection,
t.ConductingEquipment = ei
# but only if this association is well-defined in the RDFS document (inverseRoleName property).

t1 = Terminal(sequenceNumber=1)
t2 = Terminal()
t2.sequenceNumber = 2
s = Switch(mRID='SW12', normalOpen=True)
# All attributes with multiplicity greater than 1 are represented as lists
s.add_Terminals(t1)
# A special function `add_{attribute_name}` is generated to insert a single item into the list
s.add_Terminals(t2)

cn = ConnectivityNode()
cn.mRID = 'Node23'
# List-type attributes may also be declared in the following way:
cn.Terminals = [t1, t] 
```

4. Create a new document instance with all objects
```python
new_doc = DocumentCIMRDF()
new_doc.add_recursively(ei)
# >> All other linked objects will be automatically inserted into the document
```
The available methods for the `DocumentCIMRDF` class are:
  * **new_doc.dump()**: Pretty-Print the document to stdout. Debug purposes only.
  * **new_doc.pack()**: Generate the document's ElementTree (xml.etree.ElementTree) instance.
  * **new_doc.tostring()**: Get the XML stringified version of the document.
  * **new_doc.tofile()**: Save the XML stringified version of the document to a file.
  * **new_doc.add_recursively( ... )**: (Recommended) Insert one or a list of elements into the document including its linked elements.
  * **new_doc.add_elements( ... )**: (Advanced users only) Insert one or a list of elements into the document.
  
## Parsing CIM RDF instances
5. Use proper functions to parse a file or a string.
```python
new_doc = DocumentCIMRDF()
new_doc.fromstring(rdfstring)
print(new_doc.resources)
# >> [list of instances]
```
The available functions are:
  * **new_doc.fromstring(rdfstring)**: Get list of instances from CIM RDF string.
  * **new_doc.fromfile(filename)**: Get list of instances from CIM RDF file.

After being inserted or parsed from a string/file, the elements are stored and accessible from the `new_doc.resources` attribute.
