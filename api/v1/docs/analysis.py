from lxml import etree
from api.v1.xutils import get_xml_id, xml_ns, exists
from api.v1.docs.config import DocConfig
from abc import ABC, abstractmethod


"""
Groups functionality for analyzing node types and making citetrails and other metadata into classes (for each doc type).
"""

class DocAnalysis(ABC):

    @abstractmethod
    def __init__(self, config: DocConfig):
        pass

    # NODE TYPES:
    # in docs, there are generally 2 types of nodes: structural and basic nodes

    @abstractmethod
    def is_structural_node(self, node: etree._Element) -> bool:
        """
        Determines whether a node defines a structural section that contains other structural and/or basic nodes.
        :param node: the node to be determined
        :return: bool indicating whether the node is structural
        """
        pass

    @abstractmethod
    def is_basic_node(self, node: etree._Element) -> bool:
        """
        Determines whether a node defines a basic text unit (such as a paragraph or a heading) that is not to be
        further nested.
        :param node: the node to be determined
        :return: bool indicating whether the node is basic
        """
        pass

    def get_node_type(self, node: etree._Element) -> str:
        """
        Gets the type of the node, expressed as a string. If the node is not relevant for doc indexing, the empty
        string is returned.
        :param node: the node to get the type for
        :return: one of 'basic', 'structural', or the empty string ''
        """
        if self.is_structural_node(node):
            return 'structural'
        elif self.is_basic_node(node):
            return 'basic'
        else:
            return ''

    # TITLE

    @abstractmethod
    def make_title(self, node: etree._Element) -> str:
        """
        Makes the title for a node, based on its metadata (attributes) and/or content nodes (headings, etc.).
        :return: the title
        """
        pass

    # CITETRAILS:

    @abstractmethod
    def make_citetrail(self, node: etree._Element):
        pass

    def get_citetrail_ancestors(self, node: etree._Element):
        return list([anc for anc in node.xpath('ancestor::*') if self.is_structural_node(anc)])[::-1]
        # revert list so that ancestors are positioned relative to current node


class GuidelinesAnalysis(DocAnalysis):

    def __init__(self, config: DocConfig):
        self.config = config

    __structural_node_def = \
        """
        self::tei:div
        and ancestor::tei:text
        """
    __basic_node_def = \
        """
        (
        self::tei:p or
        self::tei:head or
        self::tei:list
        )
        and not(ancestor::*[
            self::tei:p or
            self::tei:head or
            self::tei:list
            ])
        """

    __is_structural_node_xpath = etree.XPath(__structural_node_def, namespaces=xml_ns)
    __is_basic_node_xpath = etree.XPath(__basic_node_def + ' and ancestor::*[' + __structural_node_def + ']',
                                        namespaces=xml_ns)

    def is_structural_node(self, node: etree._Element) -> bool:
        return self.__is_structural_node_xpath(node)

    def is_basic_node(self, node: etree._Element) -> bool:
        return self.__is_basic_node_xpath(node)

    def make_title(self, node: etree._Element) -> str:
        return 'placeholder'  # TODO

    def make_citetrail(self, node: etree._Element):
        node_id = node.get('id')
        citetrail_preceding = [prec for prec in node.xpath('preceding-sibling::*') if self.get_node_type(prec)]
        citetrail_ancestors = [anc for anc in node.xpath('ancestor::*') if self.get_node_type(anc)]
        cite = str(len(citetrail_preceding) + 1)
        citetrail = cite
        if len(citetrail_ancestors):
            citetrail_parent = citetrail_ancestors[::-1][0]  # TODO does this work?
            cp_citetrail = self.config.get_citetrail_mapping(get_xml_id(citetrail_parent))
            citetrail = cp_citetrail + '.' + cite
        return citetrail

    def get_citetrail_ancestors(self, node: etree._Element):
        return list([anc for anc in node.xpath('ancestor::*') if self.is_structural_node(anc)])[::-1]
        # revert list so that ancestors are positioned relative to current node


class ProjectmembersAnalysis(DocAnalysis):

    def __init__(self, config: DocConfig):
        self.config = config

    __structural_node_def = \
        """
            self::tei:listPerson[ancestor::tei:text]
        """
    __basic_node_def = \
        """
            (
            self::tei:head or 
            self::tei:org or 
            self::tei:person
            ) and not(ancestor::*[
                self::tei:head or 
                self::tei:org or 
                self::tei:person
            ])
        """
    __is_structural_node_xpath = etree.XPath(__structural_node_def, namespaces=xml_ns)
    __is_basic_node_xpath = etree.XPath(__basic_node_def + ' and ancestor::*[' + __structural_node_def + ']',
                                        namespaces=xml_ns)

    def is_structural_node(self, node: etree._Element) -> bool:
        return self.__is_structural_node_xpath(node)

    def is_basic_node(self, node: etree._Element) -> bool:
        return self.__is_basic_node_xpath(node)

    def make_title(self, node: etree._Element) -> str:
        return 'placeholder'  # TODO

    def make_citetrail(self, node: etree._Element):
        return 'placeholder' # TODO


class SpecialcharsAnalysis(DocAnalysis):

    def __init__(self, config: DocConfig):
        self.config = config

    __structural_node_def = \
        """
            self::tei:charDecl[ancestor::tei:teiHeader]
        """
    __basic_node_def = \
        """
            self::tei:char
        """
    __is_structural_node_xpath = etree.XPath(__structural_node_def, namespaces=xml_ns)
    __is_basic_node_xpath = etree.XPath(__basic_node_def + ' and ancestor::*[' + __structural_node_def + ']',
                                        namespaces=xml_ns)

    def is_structural_node(self, node: etree._Element) -> bool:
        return self.__is_structural_node_xpath(node)

    def is_basic_node(self, node: etree._Element) -> bool:
        return self.__is_basic_node_xpath(node)

    def make_title(self, node: etree._Element) -> str:
        if exists('self::tei:charDecl'):
            return str(node.xpath('ancestor::tei:teiheader/tei:fileDesc/tei:titleStmt/tei:title[@xml:lang = "en"]',
                                  namespaces=xml_ns)[0]) # TODO i18n
        elif exists('self::tei:char/tei:desc'):
            return str(node.xpath('tei:desc/text()', namespaces=xml_ns)[0])
        else:
            return None

    def make_citetrail(self, node: etree._Element):
        return 'placeholder'  # TODO