from decimal import Decimal
from functools import cmp_to_key
from xml.etree import ElementTree
from itertools import chain

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

    def get_property_multiplicity(prop):
        multiplicity_tag = prop.find(__MULTIPLICITY_TAG)
        if multiplicity_tag != None:
            return multiplicity_tag.attrib[__RESOURCE_ATTRIB].split('#M:')[1]
        return '1..1'

    def get_superclass(element):
        superclass_tag = element.find(__SUBCLASSOF_TAG)
        if superclass_tag != None:
            return superclass_tag.attrib[__RESOURCE_ATTRIB].split('#')[1]
        return ''

    def get_comments(element):
        comment_tag = element.find(__COMMENT_TAG)
        if comment_tag != None:
            return comment_tag.text
        return ''
        
    def get_property_inverse_role_name(prop):
        return prop.find(__INVERSEROLE_TAG).attrib[__RESOURCE_ATTRIB].split('#')[1] if prop.find(__INVERSEROLE_TAG) != None else None

    enumerations = {}
    classes = {}

    for entry in root:
        if is_enumeration(entry):
            label = get_resource_label(entry)
            enumerations[label] = {}
            # capture resources that are of this type
            resources = get_resources_by_type(label)
            enumeration_set = map(lambda resource: (get_resource_label(resource), get_comments(resource)), resources)
            enumerations[label]['set'] = {value: {'comments': comments.replace('\n', ' ').replace('\r', '')} for (value, comments) in enumeration_set}
            enumerations[label]['comments'] = get_comments(entry)
        elif is_class(entry):
            label = get_resource_label(entry)
            classes[label] = {}
            classes[label]['super'] = get_superclass(entry) 
            classes[label]['comments'] = get_comments(entry)
            classes[label]['properties'] = {}
            properties = get_properties_by_domain(label)
            for prop in properties:
                prop_id = get_resource_id(prop)
                classes[label]['properties'][prop_id] = {}
                prop_obj = classes[label]['properties'][prop_id]
                prop_obj['comments'] = get_comments(prop)
                prop_obj['multiplicity'] = get_property_multiplicity(prop)
                prop_obj['inverseRoleName'] = get_property_inverse_role_name(prop)
                if prop.find(__RANGE_TAG) != None:
                    prop_obj['type'] = prop.find(__RANGE_TAG).attrib[__RESOURCE_ATTRIB].split('#')[1]
                elif prop.find(__DATATYPE_TAG) != None:
                    prop_obj['type'] = prop.find(__DATATYPE_TAG).attrib[__RESOURCE_ATTRIB].split('#')[1]
    
    # Define all super properties (all class' and its parents' properties)
    for class_name, class_detail in classes.items():
        classes[class_name]['superproperties'] = {}
        current_node = class_name
        while current_node != '':
            classes[class_name]['superproperties'].update(classes[current_node]['properties'])
            current_node = classes[current_node]['super']
    
    def class_iterator(classes):
        def tree_sort(classes):
            names = []
            while len(names) != len(classes):
                for _class in classes:
                    if _class not in names and (classes[_class]['super'] == '' or classes[_class]['super'] in names):
                        names.append(_class)
            return names
        sorted_classes = tree_sort(classes)
        return [(class_name, classes[class_name]) for class_name in sorted_classes]

    def property_iterator(properties):
        for prop_name in properties:
            new_property = properties[prop_name]
            dtype = new_property['type'] if new_property['type'] not in datatype else datatype[new_property['type']]
            comments = new_property['comments']
            inverseRoleName = new_property['inverseRoleName']
            if '..' in new_property['multiplicity']:
                minBound, maxBound = new_property['multiplicity'].split('..')
                minBound = int(minBound)
                maxBound = float('Inf') if maxBound == 'n' else int(maxBound)
            elif new_property['multiplicity'] == 'n':
                minBound, maxBound = 0, float('Inf')
            else:
                minBound, maxBound = 2 * [int(new_property['multiplicity'])]
            yield (prop_name.split(".")[1], dtype, inverseRoleName and inverseRoleName.split(".")[1], minBound, maxBound, comments.replace("\n", " "))

    TEXT = '''from decimal import Decimal
from enum import Enum
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

def _import(root):
    def get_type(element):
        if element.tag == __DESCRIPTION_TAG:
            return element.find(__TYPE_TAG).attrib[__RESOURCE_ATTRIB].split('#')[1]
        return element.tag.split('}')[1]
    def get_element_URI(element):
        try:
            return __BASE_NS.replace('#','') + '#' + element.attrib[__ID_ATTRIB]
        except:
            return __BASE_NS.replace('#','') + element.attrib[__ABOUT_ATTRIB]

    instances_dict = {}

    try:
        __BASE_NS = root.attrib[__XML_BASE].replace('#', '') + '#'
    except:
        __BASE_NS = ''

    # Instance resouces and set URI
    for child in root:
        resource_type = get_type(child)
        uri = '#' + get_element_URI(child).split('#')[1]
        instances_dict[uri] = eval(f'{resource_type}()')
        instances_dict[uri].URI = uri

    # Set resources attributes
    for child in root:
        uri = '#' + get_element_URI(child).split('#')[1]
        instance = instances_dict[uri]
        for resource_item in child:
            dtype = get_type(resource_item).split('.')[1]
            instance_attribute = getattr(instance, dtype)
            if __RESOURCE_ATTRIB in resource_item.attrib:
                referenced_resource_uri = resource_item.attrib[__RESOURCE_ATTRIB]
                value = instances_dict[referenced_resource_uri]
            else:
                value = resource_item.text
            if isinstance(instance_attribute, list):
                add_method = getattr(instance, f'add_{dtype}')
                add_method(value)
            else:
                setattr(instance, dtype, value)

    return instances_dict
'''      
    TEXT += f'''
class DocumentCIMRDF():
    PRIMITIVES = ({', '.join(primitive for primitive in datatype.values())})

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
            if element not in self.resources and element != None and all(not isinstance(element, primitive) for primitive in DocumentCIMRDF.PRIMITIVES) and not isinstance(element, Enum):
                self.resources.append(element)
                for intern_element in element.__dict__.values():
                    self.add_recursively(intern_element)

    def dump(self):
        rough_string = self.tostring()
        reparsed = parseString(rough_string)
        print(reparsed.toprettyxml(indent=' '*4))
    
    def pack(self):
        root = ET.Element('{'{'+__RDF_NS+'}'}RDF', attrib={"{'"+__XML_BASE+"': '"+__BASE_NS.replace('#','')+"/new_resource#'}"})
        for element in self.resources:
            root.append(element.serialize())
        return ET.ElementTree(root)

    def tostring(self):
        root = self.pack().getroot()
        return ET.tostring(root)

    def fromstring(self, xml):
        root = ET.fromstring(xml)
        self.resources = list(_import(root).values())

    def tofile(self, filename):
        etree = self.pack()
        etree.write(filename)

    def fromfile(self, filename):
        root = ET.parse(filename).getroot()
        self.resources = list(_import(root).values())

'''

    for enum in enumerations:
        TEXT += f'''
class {enum}(str, Enum):
    """{enumerations[enum]['comments']}"""'''
        for enum_value in enumerations[enum]['set']:
            TEXT += f'''
    {enum_value} = '{enum_value}' # {enumerations[enum]['set'][enum_value]['comments']} '''
        TEXT += '\n'

    class_iter = class_iterator(classes)

    for class_name, class_detail in class_iter:
        property_iter = list(property_iterator(class_detail['properties']))
        superproperty_iter = list(property_iterator(class_detail['superproperties']))

        # Class __init__
        TEXT += f''' 
class {class_name}({class_detail['super']}):
    """{class_detail['comments']}"""
    def __init__(self'''

        # Constructor attributes
        for prop_name, dtype, inverseRoleName, minBound, maxBound, comments in superproperty_iter:
            if maxBound < 2:
                TEXT += f''', {prop_name}: {dtype if dtype in datatype.values() else f"'{dtype}'"} = None'''
            elif maxBound >= 2:
                TEXT += f''', {prop_name}: List[{dtype if dtype in datatype.values() else f"'{dtype}'"}] = None'''
        TEXT += '):'

        # Super class
        if class_detail['super']:
            TEXT += f'''
        super().__init__('''

            # Super call attributes
            TEXT += ', '.join(f'{prop_name}={prop_name}' for prop_name, dtype, inverseRoleName, minBound, maxBound, comments in property_iterator(classes[class_detail['super']]['superproperties']))
            TEXT += ')'

        # URI generate URI
        if not class_detail['super']:
            TEXT += f'''
        self.URI = '#' + str(uuid())'''

        # List instance attributes
        for prop_name, dtype, inverseRoleName, minBound, maxBound, comments in property_iter:

            TEXT += f'''
        # {comments} ''' if comments else ''
            TEXT += f'''
        self.{prop_name} = {prop_name}'''

        # Define Properties
        for prop_name, dtype, inverseRoleName, minBound, maxBound, comments in property_iter:

            # For non list properties
            if maxBound < 2:
                TEXT += f'''
    @property
    def {prop_name}(self) -> {dtype if dtype in datatype.values() else f"'{dtype}'"}:
        return self.__{prop_name}
    @{prop_name}.setter
    def {prop_name}(self, value: {dtype if dtype in datatype.values() else f"'{dtype}'"}):
        if value == None:
            self.__{prop_name} = None
        elif not hasattr(self, '{prop_name}') or self.{prop_name} is not value:'''

                # Boolean type
                if dtype == 'bool':
                    TEXT += f'''
            self.__{prop_name} = str(value).lower() == 'true' '''
                # Other primitives
                elif dtype in datatype.values():
                    TEXT += f'''
            self.__{prop_name} = {dtype}(value)'''
                # Enumerations
                elif dtype in enumerations:
                    TEXT += f'''
            self.__{prop_name} = {dtype}(value)'''
                # Complex values
                else:
                    TEXT += f'''
            self.__{prop_name} = value'''
                
                # Set inverse attribute if it exists
                if inverseRoleName:
                    TEXT += f'''
            if isinstance(value.{inverseRoleName}, list):
                value.add_{inverseRoleName}(self)
            else:
                value.{inverseRoleName} = self'''

            # For lists
            elif maxBound >= 2:
                TEXT += f'''
    def add_{prop_name}(self, value: {dtype if dtype in datatype.values() else f"'{dtype}'"}):
        if not hasattr(self, '{prop_name}'):
            self.__{prop_name} = []
        if value not in self.__{prop_name}:'''

                # Boolean type
                if dtype == 'bool':
                    TEXT += f'''
            self.__{prop_name}.append(str(value).lower() == 'true')'''
                # Other primitives
                elif dtype in datatype.values():
                    TEXT += f'''
            self.__{prop_name}.append({dtype}(value))'''
                # Enumerations
                elif dtype in enumerations:
                    TEXT += f'''
            self.__{prop_name}.append({dtype}(value))'''
                # Complex values
                else:
                    TEXT += f'''
            self.__{prop_name}.append(value)'''

                # Set inverse attribute if it exists
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
            return
        for obj in list_objs:
            self.add_{prop_name}(obj)'''

                # Set inverse attribute if it exists
                if inverseRoleName:
                    TEXT += f'''
        if len(list_objs):
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
        
        
        for prop_name, dtype, inverseRoleName, minBound, maxBound, comments in property_iter:

            if maxBound < 2:  # If it is a unique object

                TEXT += f'''
        if self.{prop_name} != None:'''

                if dtype == 'bool': # If it is a boolean value
                    TEXT += f'''
            prop = ET.SubElement(root, '{'{'+__BASE_NS+'}'}{f'{class_name}.{prop_name}'}')
            prop.text = {f'str(self.{prop_name}).lower()'}'''

                elif dtype in datatype.values(): # If it is another primitive
                    TEXT += f'''
            prop = ET.SubElement(root, '{'{'+__BASE_NS+'}'}{f'{class_name}.{prop_name}'}')
            prop.text = {f'str(self.{prop_name})'}'''

                elif dtype in enumerations: # If it is an enumeration
                    TEXT += f'''
            prop = ET.SubElement(root, '{'{'+__BASE_NS+'}'}{f'{class_name}.{prop_name}'}')
            prop.text = {f'self.{prop_name}.value'}'''

                else: # if it is a complex type
                    TEXT += f'''
            ET.SubElement(root, '{'{'+__BASE_NS+'}'}{f'{class_name}.{prop_name}'}', attrib={"{'{" +__RDF_NS+"}"}resource': self.__{prop_name+'.URI}'})'''
            

            elif maxBound >= 2:  # If it is a list of objects

                TEXT += f'''
        if self.{prop_name} != []:
            for item in self.{prop_name}:'''

                if dtype == 'bool': # If they are primitives
                    TEXT += f'''
                prop = ET.SubElement(root, '{'{'+__BASE_NS+'}'}{f'{class_name}.{prop_name}'}')
                prop.text = {f'str(item).lower()'}'''
            
                elif dtype in datatype.values(): # If they are other primitives
                    TEXT += f'''
                prop = ET.SubElement(root, '{'{'+__BASE_NS+'}'}{f'{class_name}.{prop_name}'}')
                prop.text = str(item)'''
                
                elif dtype in enumerations: # If they are enumerations
                    TEXT += f'''
                prop = ET.SubElement(root, '{'{'+__BASE_NS+'}'}{f'{class_name}.{prop_name}'}')
                prop.text = item.value'''

                else: # if it is a complex type
                    TEXT += f'''
                ET.SubElement(root, '{'{'+__BASE_NS+'}'}{f'{class_name}.{prop_name}'}', attrib={"{'{" +__RDF_NS+"}"}resource': item.URI{'}'})'''
        TEXT += '''
        return root'''
    

        # VALIDATION

        TEXT += '''
    def validate(self):'''
        TEXT += '''
        super().validate()''' if class_detail['super'] else ''
        
        for prop_name, dtype, inverseRoleName, minBound, maxBound, comments in property_iter:

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

        # If no property, it only passes
        if not class_detail['super'] and not len(property_iter):
            TEXT += '''
        pass'''
        TEXT += '\n'

    TEXT += '''
__all__ = [
    'DocumentCIMRDF',
    '''
    TEXT += ',\n    '.join(f"'{e}'" for e in sorted(chain(enumerations, classes)))
    TEXT += '\n]'
    TEXT += '\n'

    with open(output_file, 'w') as file:
        file.write(TEXT)

if __name__ == "__main__":
    main()