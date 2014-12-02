#!/usr/bin/python
""" Extract the main elements from the XML Esearch output

The following elements will be parsed out and be written to a new
file in tabular format:

    QueryTranslation
    Count
    RetMax
    RetStart
    QueryKey
    WebEnv
    IdList


From the command-line: use -h/--help for information on execution

"""

__author__ = "Johansson, O."
__email__ = "oscarpeterjohansson@outlook.com"
__contributors__ = ""
__version__ = "1.0"
__licence__ = "GPL-3"


import argparse
import re
import sys


ESPATTERNS = ( # this an appropriate order
    "QueryTranslation",
    "Count",
    "RetMax",
    "RetStart",
    "QueryKey",
    "WebEnv",
    "IdList"
)


def find_text(dta):
    """ Find patterns in xml string  """
    row = []
    for p in ESPATTERNS:
        # ".*?", non-greedy (ie. first match);
        # DOTALL -> . matches all, including newline
        m = re.search("(?P<%s>(?<=<%s>).*?(?=</%s>))" % (p,p,p), dta, re.DOTALL) 
        v = ""
        if m != None:
            v = m.group(p)
            if p == "IdList":
                IdList = re.findall("(?<=<Id>).*(?=</Id>)", v)
                v = ','.join(IdList)
        row.append(v)
    return row


def esrchsmry(inputfile,outputfile):
    """ 
    Extract relevant information from the xml output of the Esearch 
    utils
    """
    try:
        with open(inputfile,'r') as fd1, open(outputfile,'w') as fd2:
            xml = fd1.read()
            t_res = find_text(xml)
            txt = '\r' + '\t'.join(ESPATTERNS) + "\r\n"
            s_res = "\t".join([str(t) for t in t_res]) + "\r\n"
            txt += s_res
            fd2.write(txt)
    except (IOError,) as e:
        ms = "\rIOError: sorry, no output this time\r\n"
        sys.stdout.write(ms)


parser = argparse.ArgumentParser(
    prog = sys.argv[0],
    conflict_handler = "resolve",
    description = """
    Extract the main elements from the XML Esearch output
    utils. The following elements will be parsed out and be written
    to a new file in tabular format:
    QueryTranslation, Count, RetMax, RetStart, QueryKey, WebEnv, 
    IdList
    """,
    add_help = True
)

parser.add_argument(
    "--input",
    dest = "inputfile",
    required = True,
    help = """
    Path to xml file with output returned by the Esearch utils
    """
)

parser.add_argument(
    "--output",
    dest = "outputfile",
    required = True,
    help = """
    Path to file to contain output returned by this program
    """
)


def main(argv):
    """ For command-line use
    """
    n_argv = parser.parse_args(argv)
    d_argv = vars(n_argv)
    esrchsmry(**d_argv)
    parser.exit(status=0, message=None)


if __name__ == "__main__":
    main(sys.argv[1:])

