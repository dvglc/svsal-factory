from lxml import etree
import re

# NAMESPACES

basic_ns = {'xml': 'http://www.w3.org/XML/1998/namespace',
            'xi':  'http://www.w3.org/2001/XInclude'}
tei_ns = {'tei': 'http://www.tei-c.org/ns/1.0'}
dts_ns = {'dts': 'https://w3id.org/dts/api#'}

combined_ns = {}
combined_ns.update(basic_ns)
combined_ns.update(tei_ns)
# omitting dts as a general namespace
xml_ns = combined_ns

# UTIL FUNCTIONS

def flatten(l):
    for el in l:
        if isinstance(el, list) and not (isinstance(el, etree._Element)):
            yield from flatten(el)
        elif el is None:
            continue
        else:
            yield el


#is_element = etree.XPath('boolean(self::*)') # this throws an error with processing instructions ...
is_comment = etree.XPath('boolean(self::comment())')
is_processing_instruction = etree.XPath('boolean(self::processing-instruction())')


def is_text_node(node): # TODO is ElementStringResult really a simple text node?
    return isinstance(node, etree._ElementStringResult) or \
           isinstance(node, etree._ElementUnicodeResult) or \
           node.xpath('boolean(self::text())')


def is_element(node):
    return isinstance(node, etree._Element) and not (isinstance(node, etree._ProcessingInstruction)
                                                     or isinstance(node, etree._Comment))
    # etree._ProcessingInstruction and etree._Comment are subsubclasses of etree._Element (!)


def exists(elem: etree._Element, xpath_expr: str):
    return elem.xpath('boolean(' + xpath_expr + ')', namespaces=xml_ns)


def is_more_than_whitespace(string):
    return bool(re.match(r'\S', string))


def get_xml_id(node):
    xml_id = node.xpath('@xml:id', namespaces=xml_ns)
    if len(xml_id) == 1:
        return xml_id[0]
    else:
        return ''


def get_list_type(node):
    if exists(node, 'self::tei:list[@type]'):
        return node.get('type')
    elif exists(node, 'ancestor::tei:list[@type]'):
        return node.xpath('ancestor::tei:list[@type][1]/@type', namespaces=xml_ns)[0]
    else:
        return ''


def copy_attributes(from_elem: etree._Element, to_elem: etree._Element):
    for name, value in from_elem.items():
        to_elem.set(name, value)


get_target_node = etree.XPath('ancestor::tei:TEI/tei:text//*[@xml:id = $id]', namespaces=xml_ns)


def safe_xinclude(tree: etree._ElementTree):
    """Tries to prevent problems with the lxml xinclude function, where unexpanded nodes sometimes still stick
    in the tree after xinclusion."""
    tree.xinclude()
    return etree.fromstring(etree.tostring(tree.getroot()))
    # converting to string seems to resolve duplicate/unexpanded nodes


get_node_by_xmlid = etree.XPath('//*[@xml:id = $xmlid]', namespaces=xml_ns)


def wrap_in_dts_fragment(content):
    dts_fragment = etree.Element('{' + dts_ns['dts'] + '}' + 'fragment', nsmap=dts_ns)
    if isinstance(content, etree._Element):
        dts_fragment.append(content)
    elif isinstance(content, str):
        dts_fragment.text = content
    return dts_fragment


def make_dts_fragment_string(content):
    return etree.tostring(wrap_in_dts_fragment(content), encoding='UTF-8')

def normalize_space(text):
    return ' '.join(text.split())
