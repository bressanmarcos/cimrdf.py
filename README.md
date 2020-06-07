# cimrdf.py
Generate Python data structures from CIM RDF profiles, parse and serialize CIM-compliant information objects, according to IEC 61970-501 standard.

1) Generate your RDF artifact
2) Convert to Python data structures with :

generate.py input_filename.xml  output_filename.py

To create RDF instances
3a) Use the generated classes from output_filename.py to create your instance
4a) Create a new document instance with 

new_doc = CIMRDF_document('asd') :

