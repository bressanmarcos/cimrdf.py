from decimal import Decimal
from functools import cmp_to_key
from xml.etree import ElementTree

__RDF_NS = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
__RDFS_NS = "http://www.w3.org/2000/01/rdf-schema#"
__CIMS_NS = "http://iec.ch/TC57/1999/rdf-schema-extensions-19990926#"
__UML_NS = "http://langdale.com.au/2005/UML#"
__XSD_NS = "http://www.w3.org/2001/XMLSchema#"
__XML_NS = "http://www.w3.org/XML/1998/namespace"

__XML_BASE = '{'+__XML_NS+'}base'
__DESCRIPTION_TAG = '{'+__RDF_NS+'}Description'
__TYPE_TAG = '{'+__RDF_NS+'}type'
__LABEL_TAG = '{'+__RDFS_NS+'}label'
__COMMENT_TAG = '{'+__RDFS_NS+'}comment'
__RESOURCE_ATTRIB = '{'+__RDF_NS+'}resource'
__ABOUT_ATTRIB = '{'+__RDF_NS+'}about'
__ID_ATTRIB = '{'+__RDF_NS+'}ID'
__STEREOTYPE_TAG = '{'+__CIMS_NS+'}stereotype'
# Class
__CLASS_TAG = '{'+__RDFS_NS+'}Class'
__CLASS_URI = __RDFS_NS+'Class'
__SUBCLASSOF_TAG = '{'+__RDFS_NS+'}subClassOf'
# Property
__PROPERTY_TAG = '{'+__RDF_NS+'}Property'
__PROPERTY_URI = __RDF_NS+'Property'
__DOMAIN_TAG = '{'+__RDFS_NS+'}domain'
__RANGE_TAG = '{'+__RDFS_NS+'}range'
__MULTIPLICITY_TAG = '{' + __CIMS_NS + '}multiplicity'
__INVERSEROLE_TAG = '{' + __CIMS_NS + '}inverseRoleName'
__DATATYPE_TAG = '{'+__CIMS_NS+'}dataType'
# Enumeration
__ENUMERATION_URI = __UML_NS+'enumeration'
# cim data type
__CIMDATATYPE_URI = __UML_NS+'cimdatatype'

def is_class(element):
    return element.tag == __CLASS_TAG or \
        element.tag == __DESCRIPTION_TAG and \
        element.find(__TYPE_TAG).attrib[__RESOURCE_ATTRIB] == __CLASS_URI

def is_property(element):
    return element.tag == __PROPERTY_TAG or \
        element.tag == __DESCRIPTION_TAG and \
        element.find(__TYPE_TAG).attrib[__RESOURCE_ATTRIB] == __PROPERTY_URI

def is_enumeration(element):
    return is_class(element) and \
        element.find(__STEREOTYPE_TAG) != None and \
        element.find(__STEREOTYPE_TAG).attrib[__RESOURCE_ATTRIB] == __ENUMERATION_URI


def is_cimdatatype(element):
    return is_class(element) and \
        element.find(__STEREOTYPE_TAG) != None and \
        element.find(__STEREOTYPE_TAG).attrib[__RESOURCE_ATTRIB] == __CIMDATATYPE_URI


#################################
import sys

def main():
    input_file, output_file = sys.argv[1:3]

    xmldoc = ElementTree.parse(input_file)
    root = xmldoc.getroot()
    __BASE_NS = root.attrib[__XML_BASE].replace('#', '') + '#'

    datatype = {
        'float': 'Decimal',
        'string': 'str',
        'integer': 'int',
        'boolean': 'bool'
    }

    def get_type(element):
        if element.tag == __DESCRIPTION_TAG:
            return element.find(__TYPE_TAG).attrib[__RESOURCE_ATTRIB].split('#')[1]
        return element.tag.split('}')[1]

    def get_resource_label(element):
        return element.find(__LABEL_TAG).text
        
    def get_resource_id(element):
        if __ID_ATTRIB in element.attrib:
            return element.attrib[__ID_ATTRIB]
        if __ABOUT_ATTRIB in element.attrib:
            return element.attrib[__ABOUT_ATTRIB].split('#')[1]

    def get_resources_by_type(type):
        return filter(lambda resource: get_type(resource) == type, root)
        
    def get_properties_by_domain(domain):
        filt = filter(lambda resource: is_property(resource), root)
        filt = filter(lambda resource: resource.find(__DOMAIN_TAG) != None, filt)
        filt = filter(lambda resource: resource.find(__DOMAIN_TAG).attrib[__RESOURCE_ATTRIB].split('#')[1] == domain, filt)
        return filt

    def get_property_multiplicity(element):
        return prop.find(__MULTIPLICITY_TAG).attrib[__RESOURCE_ATTRIB].split('#M:')[1]

    def get_superclass(element):
        superclass_tag = element.find(__SUBCLASSOF_TAG)
        if superclass_tag != None:
            return superclass_tag.attrib[__RESOURCE_ATTRIB].split('#')[1]
        return ''
        
    def get_property_inverse_role_name(prop):
        return prop.find(__INVERSEROLE_TAG).attrib[__RESOURCE_ATTRIB].split('#')[1] if prop.find(__INVERSEROLE_TAG) != None else None

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
                if prop.find(__RANGE_TAG) != None:
                    prop_obj['type'] = prop.find(__RANGE_TAG).attrib[__RESOURCE_ATTRIB].split('#')[1]
                elif prop.find(__DATATYPE_TAG) != None:
                    prop_obj['type'] = prop.find(__DATATYPE_TAG).attrib[__RESOURCE_ATTRIB].split('#')[1]
                classes[label]['properties'][prop_id] = prop_obj
    
    # Define all super properties
    for class_name, class_detail in classes.items():
        classes[class_name]['superproperties'] = {}
        current_node = class_name
        while current_node != '':
            classes[class_name]['superproperties'].update(classes[current_node]['properties'])
            current_node = classes[current_node]['super']
    
    TEXT = '''from decimal import Decimal
from typing import List, Union
from uuid import uuid4 as uuid
from xml.etree import ElementTree as ET
from xml.dom.minidom import parseString

__RDF_NS = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
__RDFS_NS = "http://www.w3.org/2000/01/rdf-schema#"
__CIMS_NS = "http://iec.ch/TC57/1999/rdf-schema-extensions-19990926#"
__UML_NS = "http://langdale.com.au/2005/UML#"
__XSD_NS = "http://www.w3.org/2001/XMLSchema#"
__XML_NS = "http://www.w3.org/XML/1998/namespace"

__XML_BASE = '{'+__XML_NS+'}base'
__DESCRIPTION_TAG = '{'+__RDF_NS+'}Description'
__TYPE_TAG = '{'+__RDF_NS+'}type'
__LABEL_TAG = '{'+__RDFS_NS+'}label'
__COMMENT_TAG = '{'+__RDFS_NS+'}comment'
__RESOURCE_ATTRIB = '{'+__RDF_NS+'}resource'
__ABOUT_ATTRIB = '{'+__RDF_NS+'}about'
__ID_ATTRIB = '{'+__RDF_NS+'}ID'
__STEREOTYPE_TAG = '{'+__CIMS_NS+'}stereotype'
# Class
__CLASS_TAG = '{'+__RDFS_NS+'}Class'
__CLASS_URI = __RDFS_NS+'Class'
__SUBCLASSOF_TAG = '{'+__RDFS_NS+'}subClassOf'
# Property
__PROPERTY_TAG = '{'+__RDF_NS+'}Property'
__PROPERTY_URI = __RDF_NS+'Property'
__DOMAIN_TAG = '{'+__RDFS_NS+'}domain'
__RANGE_TAG = '{'+__RDFS_NS+'}range'
__MULTIPLICITY_TAG = '{' + __CIMS_NS + '}multiplicity'
__INVERSEROLE_TAG = '{' + __CIMS_NS + '}inverseRoleName'
__DATATYPE_TAG = '{'+__CIMS_NS+'}dataType'
# Enumeration
__ENUMERATION_URI = __UML_NS+'enumeration'
# cim data type
__CIMDATATYPE_URI = __UML_NS+'cimdatatype'
'''
    TEXT += f"__BASE_NS = '{__BASE_NS}'"
    TEXT += '''

def _import(etree):
    def get_type(element):
        if element.tag == __DESCRIPTION_TAG:
            return element.find(__TYPE_TAG).attrib[__RESOURCE_ATTRIB].split('#')[1]
        return element.tag.split('}')[1]
    def get_element_URI(element):
        try:
            return __BASE_NS.replace('#','') + '#' + element.attrib[__ID_ATTRIB]
        except:
            return __BASE_NS.replace('#','') + element.attrib[__ABOUT_ATTRIB]

    root = etree
    classes = {}

    try:
        __BASE_NS = root.attrib[__XML_BASE].replace('#', '') + '#'
    except:
        __BASE_NS = ''

    for child in root:
        new_class = get_type(child)
        uri = '#' + get_element_URI(child).split('#')[1]
        classes[uri] = eval(new_class + '()')
        classes[uri].URI = uri

    for child in root:
        uri = '#' + get_element_URI(child).split('#')[1]
        element = classes[uri]
        for attribute in child:
            dtype = get_type(attribute).replace('.', '_')
            if __RESOURCE_ATTRIB in attribute.attrib:
                resource_uri = attribute.attrib[__RESOURCE_ATTRIB]
                exec(f"""
if isinstance(element.{dtype}, list):
   element.add_{dtype}(classes[resource_uri])
else:
   element.{dtype} = classes[resource_uri]
""")
            else:
                value = attribute.text
                exec(f"""
if isinstance(element.{dtype}, list):
    element.add_{dtype}(value)
else:
    element.{dtype} = value
""")

    return classes'''      
    TEXT += f'''

class DocumentCIMRDF():
    PRIMITIVES = ({''.join(primitive+', ' for primitive in datatype.values())})

    def __init__(self, resources = []):
        self.resources = []
        for resource in resources:
            self.resources.append(resource)

    def add_elements(self, elements: Union[ET.Element, List[ET.Element]]):
        elements = elements if isinstance(elements, list) else [elements]
        for element in elements:
            if element not in self.resources:
                self.resources.append(element)

    def add_recursively(self, elements: Union[ET.Element, List[ET.Element]]):
        elements = elements if isinstance(elements, list) else [elements]
        for element in elements:
            if element not in self.resources and element != None and all(not isinstance(element, primitive) for primitive in DocumentCIMRDF.PRIMITIVES) and not isinstance(element, Enumeration):
                self.resources.append(element)
                for intern_element in element.__dict__.values():
                    self.add_recursively(intern_element)

    def dump(self):
        etree = self.pack()
        rough_string = ET.tostring(etree, 'utf-8')
        reparsed = parseString(rough_string)
        print(reparsed.toprettyxml(indent=' '*4))
    
    def pack(self):
        root = ET.Element('{'{'+__RDF_NS+'}'}RDF', attrib={"{'"+__XML_BASE+"': '"+__BASE_NS.replace('#','')+"/new_resource#'}"})
        for element in self.resources:
            root.append(element.serialize())
        return root

    def tostring(self):
        return ET.tostring(self.pack())

    def fromstring(self, xml):
        etree = ET.fromstring(xml)
        self.resources = list(_import(etree).values())

    def fromfile(self, filename):
        etree = ET.parse(filename)
        self.resources = list(_import(etree).values())

class Enumeration:
    def __init__(self, value, allowed):
        if value not in allowed:
            raise ValueError(f'{'{'+'value'+'}'} is not in the Enumeration set')
        self.__value = value
    def __str__(self):
        return self.__value
    def __eq__(self, other):
        return self.__value == str(other)
'''

    for enum_name, enum_set in enumerations.items():
        TEXT += f'''
class {enum_name}(Enumeration):'''
        for enum_value in enum_set:
            TEXT += f'''
    {enum_value.upper()} = '{enum_value}' '''
        TEXT += f'''
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
            new_property = properties[prop_name]
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
        # Class __init_
        TEXT += f''' 
class {class_name}({class_detail['super']}):
    def __init__(self'''

        # Constructor attributes
        for prop_name, dtype, inverseRoleName, minBound, maxBound in property_iter(class_detail['superproperties']):
            if maxBound < 2:
                TEXT += f''', {prop_name}: {dtype if dtype in datatype.values() else f"'{dtype}'"} = None'''
            else:
                TEXT += f''', {prop_name}: List[{dtype if dtype in datatype.values() else f"'{dtype}'"}] = None'''
        TEXT += '):'

        # Super class
        if class_detail['super']:
            TEXT += f'''
        super().__init__('''

            # Super call attributes
            for prop_name, dtype, inverseRoleName, minBound, maxBound in property_iter(classes[class_detail['super']]['superproperties']):
                TEXT += f'''{prop_name} = {prop_name}, '''
            TEXT += ')'

        # URI generate URI
        else:
            TEXT += f'''
        self.URI = '#' + str(uuid())'''

        # List instance attributes
        for prop_name, dtype, inverseRoleName, minBound, maxBound in property_iter(class_detail['properties']):
            TEXT += f'''
        self.{prop_name} = {prop_name}'''

        # Define Properties
        for prop_name, dtype, inverseRoleName, minBound, maxBound in property_iter(class_detail['properties']):
            if maxBound < 2:
                TEXT += f'''
    @property
    def {prop_name}(self) -> {dtype if dtype in datatype.values() else f"'{dtype}'"}:
        return self.__{prop_name}
    @{prop_name}.setter
    def {prop_name}(self, value: {dtype if dtype in datatype.values() else f"'{dtype}'"}):
        if value == None:
            self.__{prop_name} = None
        elif not hasattr(self, '{prop_name}') or not self.{prop_name} is value:
            self.__{prop_name} = {dtype+'(value)' if dtype in ['str', 'int', 'Decimal'] else ('str(value).lower() == "true"' if dtype in ['bool'] else 'value')}'''
                if inverseRoleName:
                    TEXT += f'''
            if isinstance(value.{inverseRoleName}, list):
                value.add_{inverseRoleName}(self)
            else:
                value.{inverseRoleName} = self'''
            
            elif maxBound >= 2:
                TEXT += f'''
    def add_{prop_name}(self, value: {dtype if dtype in datatype.values() else f"'{dtype}'"}):
        if self.__{prop_name} is None:
            self.__{prop_name} = []
        if value not in self.__{prop_name}:
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
        if list_objs == None:
            self.__{prop_name} = []
        else:
            self.__{prop_name} = list_objs'''
                if inverseRoleName:
                    TEXT += f'''
        if list_objs and len(list_objs):
            if isinstance(list_objs[0].{inverseRoleName}, list):
                for obj in list_objs:
                    obj.add_{inverseRoleName}(self)
            else:
                for obj in list_objs:
                    obj.{inverseRoleName} = self'''

        # SERIALIZATION #####################################################################

        TEXT += f'''
    def serialize(self) -> ET.Element:
        self.validate()'''
        if class_detail['super']:
            TEXT += f'''
        root = super().serialize()
        root.tag = '{'{' + __BASE_NS + '}'}{class_name}' '''
        else:
            TEXT += f'''
        root = ET.Element('{'{'+__BASE_NS+'}'}{class_name}', attrib={"{'{"+__RDF_NS+"}about': self.URI}"})'''
        
        for prop_name, dtype, inverseRoleName, minBound, maxBound in property_iter(class_detail['properties']):
            

            if maxBound < 2:  # If it is an only object
                TEXT += f'''
        if self.__{prop_name} != None:'''
                if dtype in datatype.values() or dtype in enumerations: # If it is a primitive or an enumeration
                    TEXT += f'''
            prop = ET.SubElement(root, '{'{'+__BASE_NS+'}'}{prop_name.replace('_','.')}')
            prop.text = {'str(self.__'+prop_name+').lower()' if dtype == 'bool' else f'str(self.__{prop_name})'}'''

                else: # if it is a complex type
                    TEXT += f'''
            ET.SubElement(root, '{'{'+__BASE_NS+'}'}{prop_name.replace('_','.')}', attrib={"{'{" +__RDF_NS+"}"}resource': self.__{prop_name+'.URI}'})'''
            


            else:  # If it is a list
                TEXT += f'''
        if self.__{prop_name} != []:'''
                TEXT += f'''
            for item in self.__{prop_name}:'''
            
                if dtype in datatype.values() or dtype in enumerations: # If they are primitives
                    TEXT += f'''
                prop = ET.SubElement(root, '{'{'+__BASE_NS+'}'}{prop_name.replace('_','.')}')
                prop.text = str(item)'''
                
                else: # if it is a complex type
                    TEXT += f'''
                ET.SubElement(root, '{'{'+__BASE_NS+'}'}{prop_name.replace('_','.')}', attrib={"{'{" +__RDF_NS+"}"}resource': item.URI{'}'})'''
        
        
        
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
            raise ValueError(f'Incorrect datatype in {prop_name} [{class_name}] (expected {dtype} but encountered {'{self.'+prop_name+'.__class__.__name__}'} instead)')'''
                #<<<<<<<<<<<<<<<<<<<<<<
            else:
                #>>>>>>>>>>>>>>>>>>>>>>
                TEXT += f'''
        minBound, maxBound = {minBound}, {maxBound if type(maxBound) != float else "float('Inf')"}
        if len(self.{prop_name}) < minBound or len(self.{prop_name}) > maxBound:
            raise ValueError('Incorrect multiplicity in {prop_name} [{class_name}]')
        if any(not isinstance(item, {dtype}) for item in self.{prop_name}):
            raise ValueError(f'Incorrect datatype in {prop_name} [{class_name}] (expected {dtype} but encountered {'{self.'+prop_name+'.__class__.__name__}'} instead)')'''
                #<<<<<<<<<<<<<<<<<<<<<<

        TEXT += '\n'

    with open(output_file, 'w') as file:
        file.write(TEXT)

if __name__ == "__main__":
    main()