from decimal import Decimal
from functools import cmp_to_key
from xml.etree import ElementTree

RDF_NS = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
RDFS_NS = "http://www.w3.org/2000/01/rdf-schema#"
CIMS_NS = "http://iec.ch/TC57/1999/rdf-schema-extensions-19990926#"
UML_NS = "http://langdale.com.au/2005/UML#"
XSD_NS = "http://www.w3.org/2001/XMLSchema#"
XML_NS = "http://www.w3.org/XML/1998/namespace"

XML_BASE = '{'+XML_NS+'}base'
DESCRIPTION_TAG = '{'+RDF_NS+'}Description'
TYPE_TAG = '{'+RDF_NS+'}type'
LABEL_TAG = '{'+RDFS_NS+'}label'
COMMENT_TAG = '{'+RDFS_NS+'}comment'
RESOURCE_ATTRIB = '{'+RDF_NS+'}resource'
ABOUT_ATTRIB = '{'+RDF_NS+'}about'
ID_ATTRIB = '{'+RDF_NS+'}ID'
STEREOTYPE_TAG = '{'+CIMS_NS+'}stereotype'
# Class
CLASS_TAG = '{'+RDFS_NS+'}Class'
CLASS_URI = RDFS_NS+'Class'
SUBCLASSOF_TAG = '{'+RDFS_NS+'}subClassOf'
# Property
PROPERTY_TAG = '{'+RDF_NS+'}Property'
PROPERTY_URI = RDF_NS+'Property'
DOMAIN_TAG = '{'+RDFS_NS+'}domain'
RANGE_TAG = '{'+RDFS_NS+'}range'
MULTIPLICITY_TAG = '{' + CIMS_NS + '}multiplicity'
INVERSEROLE_TAG = '{' + CIMS_NS + '}inverseRoleName'
DATATYPE_TAG = '{'+CIMS_NS+'}dataType'
# Enumeration
ENUMERATION_URI = UML_NS+'enumeration'
# cim data type
CIMDATATYPE_URI = UML_NS+'cimdatatype'

def is_class(element):
    return element.tag == CLASS_TAG or \
        element.tag == DESCRIPTION_TAG and \
        element.find(TYPE_TAG).attrib[RESOURCE_ATTRIB] == CLASS_URI

def is_property(element):
    return element.tag == PROPERTY_TAG or \
        element.tag == DESCRIPTION_TAG and \
        element.find(TYPE_TAG).attrib[RESOURCE_ATTRIB] == PROPERTY_URI

def is_enumeration(element):
    return is_class(element) and \
        element.find(STEREOTYPE_TAG) != None and \
        element.find(STEREOTYPE_TAG).attrib[RESOURCE_ATTRIB] == ENUMERATION_URI


def is_cimdatatype(element):
    return is_class(element) and \
        element.find(STEREOTYPE_TAG) != None and \
        element.find(STEREOTYPE_TAG).attrib[RESOURCE_ATTRIB] == CIMDATATYPE_URI


#################################
import sys

if __name__ == "__main__":
    argv = sys.argv
    input_file = argv[1]
    output_file = argv[2]

    xmldoc = ElementTree.parse(input_file)
    root = xmldoc.getroot()
    BASE_NS = root.attrib[XML_BASE].replace('#', '') + '#'

    datatype = {
        'float': 'Decimal',
        'string': 'str',
        'integer': 'int',
        'boolean': 'bool'
    }

    def get_type(element):
        if element.tag == DESCRIPTION_TAG:
            return element.find(TYPE_TAG).attrib[RESOURCE_ATTRIB].split('#')[1]
        return element.tag.split('}')[1]

    def get_resource_label(element):
        return element.find(LABEL_TAG).text
        
    def get_resource_id(element):
        if ID_ATTRIB in element.attrib:
            return element.attrib[ID_ATTRIB]
        if ABOUT_ATTRIB in element.attrib:
            return element.attrib[ABOUT_ATTRIB].split('#')[1]

    def get_resources_by_type(type):
        return filter(lambda resource: get_type(resource) == type, root)
        
    def get_properties_by_domain(domain):
        filt = filter(lambda resource: is_property(resource), root)
        filt = filter(lambda resource: resource.find(DOMAIN_TAG) != None, filt)
        filt = filter(lambda resource: resource.find(DOMAIN_TAG).attrib[RESOURCE_ATTRIB].split('#')[1] == domain, filt)
        return filt

    def get_property_multiplicity(element):
        return prop.find(MULTIPLICITY_TAG).attrib[RESOURCE_ATTRIB].split('#M:')[1]

    def get_superclass(element):
        superclass_tag = element.find(SUBCLASSOF_TAG)
        if superclass_tag != None:
            return superclass_tag.attrib[RESOURCE_ATTRIB].split('#')[1]
        return ''
        
    def get_property_inverse_role_name(prop):
        return prop.find(INVERSEROLE_TAG).attrib[RESOURCE_ATTRIB].split('#')[1] if prop.find(INVERSEROLE_TAG) != None else None

    class URI:
        def __init__(self, uri):
            self.__ns = ''
            self.__id = ''
            self.uri = uri
        @property
        def uri(self):
            return self.__ns + '#' + self.__id
        @uri.setter
        def uri(self, value):
            if '#' in value:
                _ns, _id = value.split('#')
                self.__ns = _ns if _ns != '' else self.__ns
                self.__id = _id if _id != '' else self.__id
            else:
                self.__id = value
            

    enumerations = {}
    classes = {}

    for entry in root:
        if is_enumeration(entry):
            label = get_resource_label(entry)
            # capture resources that are this type
            resources = get_resources_by_type(label)
            enumeration_set = list(map(lambda resource: get_resource_label(resource), resources))
            enumerations[label] = enumeration_set
        elif is_class(entry):
            label = get_resource_label(entry)
            classes[label] = {}
            classes[label]['super'] = get_superclass(entry) 
            classes[label]['properties'] = {}
            properties = get_properties_by_domain(label)
            for prop in properties:
                prop_id = get_resource_id(prop)
                prop_obj = {}
                prop_obj['multiplicity'] = get_property_multiplicity(prop)
                prop_obj['inverseRoleName'] = get_property_inverse_role_name(prop)
                if prop.find(RANGE_TAG) != None:
                    prop_obj['type'] = prop.find(RANGE_TAG).attrib[RESOURCE_ATTRIB].split('#')[1]
                elif prop.find(DATATYPE_TAG) != None:
                    prop_obj['type'] = prop.find(DATATYPE_TAG).attrib[RESOURCE_ATTRIB].split('#')[1]
                classes[label]['properties'][prop_id] = prop_obj

    TEXT = '''from decimal import Decimal
from typing import List, Optional
from uuid import uuid4
from xml.etree import ElementTree as ET

RDF_NS = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
RDFS_NS = "http://www.w3.org/2000/01/rdf-schema#"
CIMS_NS = "http://iec.ch/TC57/1999/rdf-schema-extensions-19990926#"
UML_NS = "http://langdale.com.au/2005/UML#"
XSD_NS = "http://www.w3.org/2001/XMLSchema#"
XML_NS = "http://www.w3.org/XML/1998/namespace"

XML_BASE = '{'+XML_NS+'}base'
DESCRIPTION_TAG = '{'+RDF_NS+'}Description'
TYPE_TAG = '{'+RDF_NS+'}type'
LABEL_TAG = '{'+RDFS_NS+'}label'
COMMENT_TAG = '{'+RDFS_NS+'}comment'
RESOURCE_ATTRIB = '{'+RDF_NS+'}resource'
ABOUT_ATTRIB = '{'+RDF_NS+'}about'
STEREOTYPE_TAG = '{'+CIMS_NS+'}stereotype'
# Class
CLASS_TAG = '{'+RDFS_NS+'}Class'
CLASS_URI = RDFS_NS+'Class'
SUBCLASSOF_TAG = '{'+RDFS_NS+'}subClassOf'
# Property
PROPERTY_TAG = '{'+RDF_NS+'}Property'
PROPERTY_URI = RDF_NS+'Property'
DOMAIN_TAG = '{'+RDFS_NS+'}domain'
RANGE_TAG = '{'+RDFS_NS+'}range'
MULTIPLICITY_TAG = '{' + CIMS_NS + '}multiplicity'
INVERSEROLE_TAG = '{' + CIMS_NS + '}inverseRoleName'
DATATYPE_TAG = '{'+CIMS_NS+'}dataType'
# Enumeration
ENUMERATION_URI = UML_NS+'enumeration'
# cim data type
CIMDATATYPE_URI = UML_NS+'cimdatatype'

__pointer = None

'''
            
    TEXT += f'''
class CIMRDF_document():
    def __init__(self, _id):
        global __pointer
        self.__id = _id
        __pointer = []

    def pack(self):
        global __pointer
        root = ET.Element('{'{' + RDF_NS + '}'}RDF')
        for element in __pointer:
            root.append(element.serialize())
        return root

def add_element(element):
    __pointer.append(element)
'''

    for enum_name, enum_set in enumerations.items():
        TEXT += f'''
class {enum_name}(Enumeration):
    def __init__(self, value: str):
        self.__ALLOWED = {enum_set}
        super().__init__(value, self.__ALLOWED)
'''

    def class_iter(classes):
        def tree_sort(classes):
            names = []
            while len(names) != len(classes):
                for _class in classes:
                    if _class not in names and (classes[_class]['super'] == '' or classes[_class]['super'] in names):
                        names.append(_class)
            return names
        sorted_classes = tree_sort(classes)
        for class_name in sorted_classes:
            yield class_name, classes[class_name]

    def property_iter(properties):
        for prop_name in properties:
            new_property = class_detail['properties'][prop_name]
            dtype = new_property['type'] if new_property['type'] not in datatype else datatype[new_property['type']]
            inverseRoleName = new_property['inverseRoleName']
            if '..' in new_property['multiplicity']:
                minBound, maxBound = new_property['multiplicity'].split('..')
                minBound = int(minBound)
                maxBound = float('Inf') if maxBound == 'n' else int(maxBound)
            elif new_property['multiplicity'] == 'n':
                minBound, maxBound = 0, float('Inf')
            else:
                minBound, maxBound = 2 * [int(new_property['multiplicity'])]
            yield (prop_name.replace(".", "_"), dtype.replace(".", "_"), inverseRoleName and inverseRoleName.replace(".", "_"), minBound, maxBound)

    for class_name, class_detail in class_iter(classes):
        #>>>>>>>>>>>>>>>>>>>>>>
        TEXT += f''' 
class {class_name}({class_detail['super']}):
    def __init__(self):
        {'super().__init__()' if class_detail['super'] else 'add_element(self)'}
        self.URI = '#' + str(uuid4())'''
        #<<<<<<<<<<<<<<<<<<<<<<

        # List instance attributes
        for prop_name, dtype, inverseRoleName, minBound, maxBound in property_iter(class_detail['properties']):
            if maxBound < 2:
                #>>>>>>>>>>>>>>>>>>>>>>
                TEXT += f'''
        self.__{prop_name}: {dtype if dtype in datatype.values() else f"'{dtype}'"} = None'''
                #<<<<<<<<<<<<<<<<<<<<<<
            else:
                #>>>>>>>>>>>>>>>>>>>>>>
                TEXT += f'''
        self.__{prop_name}: List[{dtype if dtype in datatype.values() else f"'{dtype}'"}] = []'''
                #<<<<<<<<<<<<<<<<<<<<<<

        # Define Properties
        for prop_name, dtype, inverseRoleName, minBound, maxBound in property_iter(class_detail['properties']):
            if maxBound < 2:
                TEXT += f'''
    @property
    def {prop_name}(self) -> {dtype if dtype in datatype.values() else f"'{dtype}'"}:
        return self.__{prop_name}
    @{prop_name}.setter
    def {prop_name}(self, value: {dtype if dtype in datatype.values() else f"'{dtype}'"}):
        if self.__{prop_name} == None:
            self.__{prop_name} = {'str(value).lower() == "true"' if dtype == 'bool' else (dtype+'(value)' if dtype in datatype.values() or dtype in enumerations else 'value')}'''
                if inverseRoleName:
                    TEXT += f'''
            if isinstance(value.{inverseRoleName}, list):
                value.add_{inverseRoleName}(self)
            else:
                value.{inverseRoleName} = self'''
            else:
                TEXT += f'''
    def add_{prop_name}(self, value: {dtype if dtype in datatype.values() else f"'{dtype}'"}):
        self.__{prop_name}.append(value)'''
                if inverseRoleName:
                    TEXT += f'''
        if isinstance(value.{inverseRoleName}, list):
            value.add_{inverseRoleName}(self)
        else:
            value.{inverseRoleName} = self'''
                TEXT += f'''
    @property
    def {prop_name}(self) -> List[{dtype if dtype in datatype.values() else f"'{dtype}'"}]:
        return self.__{prop_name}
    @{prop_name}.setter
    def {prop_name}(self, list_objs: List[{dtype if dtype in datatype.values() else f"'{dtype}'"}]):
        if self.__{prop_name} == []:
            self.__{prop_name} = list_objs'''
                if inverseRoleName:
                    TEXT += f'''
            if isinstance(list_objs[0].{inverseRoleName}, list):
                for obj in list_objs:
                    obj.add_{inverseRoleName}(self)
            else:
                for obj in list_objs:
                    value.{inverseRoleName} = self'''

        # SERIALIZATION #####################################################################

        TEXT += f'''
    def serialize(self) -> ET.Element:
        self.validate()
        root = ET.Element('{'{'+BASE_NS+'}'}{class_name}', attrib={"{'{"+RDF_NS+"}about': self.URI}"})'''
        
        for prop_name, dtype, inverseRoleName, minBound, maxBound in property_iter(class_detail['properties']):
            

            if maxBound < 2:  # If it is an only object
                TEXT += f'''
        if self.__{prop_name} != None:'''
                if dtype in datatype.values() or dtype in enumerations: # If it is a primitive or an enumeration
                    TEXT += f'''
            prop = ET.SubElement(root, '{'{'+BASE_NS+'}'}{prop_name.replace('_','.')}')
            prop.text = str(self.__{prop_name})'''

                else: # if it is a complex type
                    TEXT += f'''
            ET.SubElement(root, '{'{'+BASE_NS+'}'}{prop_name.replace('_','.')}', attrib={"{'{" +RDF_NS+"}"}resource': self.__{prop_name+'.URI}'})'''
            


            else:  # If it is a list
                TEXT += f'''
        if self.__{prop_name} != []:'''
                TEXT += f'''
            for item in self.__{prop_name}:'''
            
                if dtype in datatype.values() or dtype in enumerations: # If they are primitives
                    TEXT += f'''
                prop = ET.SubElement(root, '{'{'+BASE_NS+'}'}{prop_name.replace('_','.')}')
                prop.text = str(item)'''
                
                else: # if it is a complex type
                    TEXT += f'''
                ET.SubElement(root, '{'{'+BASE_NS+'}'}{prop_name.replace('_','.')}', attrib={"{'{" +RDF_NS+"}"}resource': item.URI{'}'})'''
        
        
        
        TEXT += f'''
        return root
    '''
        # VALIDATION
        #>>>>>>>>>>>>>>>>>>>>>>
        TEXT += f'''
    def validate(self):
        {'super().validate()' if class_detail['super'] else ''}'''
        #<<<<<<<<<<<<<<<<<<<<<<
        
        for prop_name, dtype, inverseRoleName, minBound, maxBound in property_iter(class_detail['properties']):

            if maxBound < 2:
                #>>>>>>>>>>>>>>>>>>>>>>
                TEXT += f'''
        if not isinstance(self.{prop_name}, {dtype}){f' and self.{prop_name} != None' if minBound == 0 else ''}:
            raise ValueError('Incorrect datatype in {prop_name}')'''
                #<<<<<<<<<<<<<<<<<<<<<<
            else:
                #>>>>>>>>>>>>>>>>>>>>>>
                TEXT += f'''
        minBound, maxBound = {minBound}, {maxBound if type(maxBound) != float else "float('Inf')"}
        if len(self.{prop_name}) < minBound or len(self.{prop_name}) > maxBound:
            raise ValueError('Incorrect multiplicity in {prop_name}')
        if any(not isinstance(item, {dtype}) for item in self.{prop_name}):
            raise ValueError('Incorrect datatype in {prop_name}')'''
                #<<<<<<<<<<<<<<<<<<<<<<

        TEXT += '\n'

    TEXT += '''
def fromstring(xml):
    etree = ET.fromstring(xml)
    return __import(etree)
def fromfile(filename):
    etree = ET.parse(filename)
    return __import(etree)

def __import(etree):
    def get_type(element):
        if element.tag == DESCRIPTION_TAG:
            return element.find(TYPE_TAG).attrib[RESOURCE_ATTRIB].split('#')[1]
        return element.tag.split('}')[1]
    def get_element_URI(element):
        try:
            return BASE_NS.replace('#','') + '#' + element.attrib[ID_ATTRIB]
        except:
            return BASE_NS.replace('#','') + element.attrib[ABOUT_ATTRIB]

    root = etree.getroot()
    classes = {}

    try:
        BASE_NS = root.attrib[XML_BASE].replace('#', '') + '#'
    except:
        BASE_NS = ''

    for child in root:
        new_class = get_type(child)
        uri = get_element_URI(child)
        classes[uri] = eval(new_class + '()')
        exec(new_class + ".URI = " + "'" + uri + "'")

    for child in root:
        uri = get_element_URI(child)
        element = classes[uri]
        for attribute in child:
            dtype = get_type(attribute).replace('.', '_')
            try:
                resource_uri = attribute.attrib[RESOURCE_ATTRIB]
                exec(f'element.{dtype} = classes[resource_uri]')
            except:
                value = attribute.text
                exec(f'element.{dtype} = value')

    return classes'''

    with open(output_file, 'w') as file:
        file.write(TEXT)
