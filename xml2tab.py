#!/usr/bin/python
""" Parse XML documents returned by Eutilities

Convert XML file to a tabular formatted file, e.g. Efetch (data record
downloads), or ESummary (document summary downloads).

The program/function produces rows by iterating over elements in the XML
file while collecting attributes and text material. Relations between
sub-sections are lost while migrating away from the XML structure. To try
to retain that information in the new document, this one contains a
field named "stack" that for each row shows stacked indices. The length
of the stack corresponds to the depth in the XML data structure at which
we are parsing, while the value corresponds to the index of the element
being parsed at that very level. In addition there is a field named "lvl"
that shows the level, or depth that were parsing, and a field named "idx",
showing the index of the child of the root element beeing worked at. This
value is the same as that at index position 1 in the stack. Indexing is 
zero-based by the way. The advantage of using a tabular format is that 
it might be easier to extract information, for instance using (Microsoft) 
Excel or LibreOffice Calc. Other than those fields, the new document contains
a "text" field for texts and keywords from the attributes in each element.



From the Command-line: Use "-h/--help" for info on execution

"""

__author__ = "Johansson, O."
__email__ = "oscarpeterjohansson@outlook.com"
__contributors__ = ""
__version__ = "2.0"
__licence__ = "GPL-3"


import argparse
import sys
import traceback
import xml.etree.ElementTree as ET

DICT = {}
FIELDS = []
DTA = []


def tracker():
    """ traceback """
    t,v,tb = sys.exc_info()
    traceback.print_exception(t,v,tb,file=sys.stdout)


def file_parser(inputfile):
    """ Open file, parse xml string, return root """
    s_xml = None
    root = None
    try:
        with open(inputfile, 'r') as fd:
            s_xml = fd.read()
    except (IOError,) as e:
        tracker()
        return None
    try:
        root = ET.fromstring(s_xml)
    except (ET.ParseError,) as e:
        tracker()
        return None
    return root


def set_fields(root):
    """ Find and set fields """
    global DTA, FIELDS
    sf = set()
    sf.update(root.keys())
    # immediate children or root are identical, as child == ID.
    for elt in root: 
        for elt in elt.iter():
            sf.update(elt.keys())
        if "ERROR" not in sf:
            break
    sf.update(["tag","stack","lvl","text","idx"])
    lf = list(sf)
    lf.sort()
    FIELDS = lf
    DTA.append(FIELDS)


def set_dict():
    """ Create dictionary that maps field to index"""
    global DICT, FIELDS
    DICT = dict([(FIELDS[i],i) for i in xrange(len(FIELDS))])


def iterate(elt, stack, lvl):
    """ Recursion - keep track of idx and level with stack """
    global DICT, DTA
    row = ["" for i in xrange(len(FIELDS))]
    for k in elt.keys():
        if k in DICT.keys():
            row[DICT.get(k)] = elt.get(k)
    if elt.text != None:
        row[DICT.get("text")] = elt.text
    row[DICT.get("tag")] = elt.tag
    row[DICT.get("lvl")] = lvl
    try:
        row[DICT.get("idx")] = stack[1] # child of root element
    except (IndexError,) as e:
        row[DICT.get("idx")] = "root"
    row[DICT.get("stack")] = ';'.join([str(i) for i in stack])
    row = [str(i) for i in row]
    DTA.append(row)
    idx = -1  # cheating a little: idx = 0 
    lvl += 1
    for elt in elt:
        idx += 1
        iterate(elt, stack+[idx], lvl)


def write_file(l_dta, outputfile):
    """ Write dta to file """
    l_dta2 = []
    for row in l_dta:
        s = '\t'.join(row)
        l_dta2.append(s)
    s_dta = "\r\n".join(l_dta2)
    try:
        with open(outputfile, 'w') as fd:
            fd.write(s_dta)
    except (IOError,) as e:
        tracker()
    return None


parser = argparse.ArgumentParser(
    prog = sys.argv[0],
    description = """
    Parse XML documents returned by Eutilities
    
    Convert XML file to a tabular formatted file, e.g. Efetch (data record
    downloads), or ESummary (document summary downloads).

    The program/function produces rows by iterating over elements in the XML
    file while collecting attributes and text material. Relations between
    sub-sections are lost while migrating away from the XML structure. To try
    to retain that information in the new document, this one contains a
    field named "stack" that for each row shows stacked indices. The length
    of the stack corresponds to the depth in the XML data structure at which
    we are parsing, while the value corresponds to the index of the element
    being parsed at that very level. In addition there is a field named "lvl"
    that shows the level, or depth that were parsing at, and a field named
    "idx", showing the index of the child of the root element beeing worked 
    at. This value is the same as that at index position 1 in the stack. 
    Indexing is zero-based by the way. The advantage of using a tabular format
    is that  it might be easier to extract information, for instance using
    (Microsoft) Excel or LibreOffice Calc. Other than those fields, the new 
    document contains a "text" field for texts and keywords from the attributes
    in each element.
    """,
    conflict_handler = "resolve",
    add_help = True
)

parser.add_argument(
    "--input",
    dest = "input",
    required = True,
    help = """
    Name of/Path to inputfile. It's expected that the inputfile to this
    program is the xml-formatted output from the efetch utility program.
    """
)

parser.add_argument(
    "--output",
    dest = "output",
    required = True,
    help = """
    Name of/Path to outputfile. This file will be tabulated.
    """
)


def main(parser, argv):
    """ for Command-line use
    """
    global DTA
    n_argv = parser.parse_args(argv)
    d_argv = vars(n_argv)
    root = file_parser(d_argv.get("input"))
    set_fields(root)
    set_dict()
    iterate(root, [0], 0)
    write_file(DTA, d_argv.get("output"))
    parser.exit(status=0, message=None)


if __name__ == "__main__":
    main(parser, sys.argv[1:])
