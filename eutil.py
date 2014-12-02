#!/usr/bin/python
""" An NCBI e-utility client

The following is an excerpt from 
http://www.ncbi.nlm.nih.gov/books/NBK25497/,
taken 7pm, Nov 6th, 2014


"The Entrez Programming Utilities (E-utilities) are a set of
nine server-side programs that provide a stable interface 
into the Entrez query and database system at the National 
Center for Biotechnology Information (NCBI). The E-utilities 
use a fixed URL syntax that translates a standard set of 
input parameters into the values necessary for various NCBI
software components to search for and retrieve the 
requested data. The E-utilities are therefore the 
structured interface to the Entrez system, which currently 
includes 38 databases covering a variety of biomedical data,
including nucleotide and protein sequences, gene records,
three-dimensional molecular structures, and the biomedical
literature."



With Python Interpreter: Use function "form_url" to format
the URL string and to compose POSTFIELDS, and "http_post" to
send a POST request.

From the Command-line: Use "--help" for info on execution

"""
__author__ = "Johansson, O."
__email__ = "oscarpeterjohansson@outlook.com"
__contributors__ = ""
__version__ = "1.0"
__licence__ = "GPL-3"

import argparse
import os
import pycurl
import re
import sys
import time
import traceback
import urllib

BAS_URL = "http://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
CHOICES = {
    "cmd" : set(["neighbor", "neighbor_score", "neighbor_history", "acheck", "ncheck", "lcheck", "llinks", "llinkslib", "prlinks"]),
    "complexity" : set(['0','1','2','3','4']),
    "db" : set([
        u"pubmed", u"protein", u"nuccore", u"nucleotide", u"nucgss", 
        u"nucest", u"structure", u"genome", u"assembly", u"genomeprj",
        u"bioproject", u"biosample", u"blastdbinfo", u"books", u"cdd",
        u"clinvar", u"clone", u"gap", u"gapplus", u"dbvar", 
        u"epigenomics", u"gene", u"gds", u"geoprofiles", u"homologene", 
        u"medgen", u"journals", u"mesh", u"ncbisearch", u"nlmcatalog", 
        u"omim", u"orgtrack", u"pmc", u"popset", u"probe", 
        u"proteinclusters", u"pcassay", u"biosystems", u"pccompound", 
        u"pcsubstance", u"pubmedhealth", u"seqannot", u"snp", u"sra", 
        u"taxonomy", u"toolkit", u"toolkitall", u"toolkitbook", 
        u"unigene", u"gencoll", u"gtr"
    ]),
    "eutility" : set([
        u"esearch", u"epost", u"esummary", u"elink", u"ecitmatch", 
        u"efetch", u"einfo", u"egquery", u"espell"
    ]),
    "rettype" : set([
        'ipg', 'gp', 'abstract', 'seqid', 'gb', 'fasta', 'uilist',
        'docsum', 'native', 'xml', 'est', 'alignmentscores', 'gpc',
        'chr', 'docset', 'homologene', 'full', 'ft', 'genxml', "json",
        'fasta_cds_na', 'medline', 'rsr', 'acc', 'gss', 'fasta_cds_aa',
        'gene_table', 'gbc', 'flt', 'summary', 'ssexemplar', 'gbwithparts'
    ]),
    "retmode" : set(["xml","text","asn.1"]),
    "strand" : set(['1','2']),
    "usehistory" : set(['y']),
    "version" : set(['2.0'])
}
QUIET = False
    

def tracker():
    """ traceback """
    t,v,tb = sys.exc_info()
    traceback.print_exception(t,v,tb,file=sys.stdout)


def form_url(**params):
    """ Format URL string

    There is no required order for the URL parameters in an 
    E-utility URL, and null values or inappropriate parameters 
    are generally ignored.
    """
    URL = ""
    URL += BAS_URL
    post_data = {}
    eutility = None
    sfx = None
    if "eutility" not in params.keys():
        message = "\r\"eutility\" not in params.keys(f\r\n)"
        sys.stdout.write(message)
        return None
    else:
        eutility = params.pop("eutility")
    if eutility == "ecitmatch":
        sfx = ".cgi?"
    else:
        sfx = ".fcgi?"
    URL += eutility
    URL += sfx
    if "term" in params.keys():
        post_data["term"] = params.pop("term")
    if "id" in params.keys():
        post_data["id"] = params.pop("id")
    postfields = urllib.urlencode(post_data)
    URL += urllib.urlencode(params)
    return (postfields, URL)


def progress(download_t, download_d, upload_t, upload_d):
    """ Progress

    Print progress of download/upload -> For use with pycurl
    """
    stat = """
    \rTotal to download %d, Total downloaded %d, Total to 
    upload %d, Total uploaded %d
    """ % (download_t, download_d, upload_t, upload_d)
    stat = re.sub("[\n]","",stat)
    sys.stdout.write(stat) 
    sys.stdout.flush()


def http_post(outputfile, postfields, URL):
    """ POST Request To The Entrez System
    """
    fd = None
    try:
        with open(outputfile,'w') as fd:
            c = pycurl.Curl()
            c.setopt(pycurl.URL, URL)
            c.setopt(pycurl.POST, 1)
            c.setopt(pycurl.HTTPHEADER, ["Content-type: application/x-www-form-urlencoded"])
            c.setopt(pycurl.FOLLOWLOCATION, 1)
            c.setopt(pycurl.USERAGENT, "Mozilla/5.0")
            c.setopt(pycurl.PROGRESSFUNCTION, progress)
            c.setopt(pycurl.POSTFIELDS, postfields)
            c.setopt(pycurl.WRITEFUNCTION, fd.write)
            c.perform()
            c.close()
            if not QUIET:
                message = "\rURL\r\n%s\r\nPOSTFIELDS\r\n%s\r\n" % (URL, postfields)
                sys.stdout.write(message)
    except (AttributeError, IOError, pycurl.error) as e:
        tracker()
    return None
        

def arg_from_file(d, arg):
    """ Set argument from file, if appropriate
    """
    if d.has_key(arg):
        value = d.get(arg,None)
        if value == None:
            return d
        if os.path.isfile(value):
            tmp = ""
            try:
                with open(value,'r') as fd:
                    t = fd.read()
                    # remove any whitespace, "\s" == "[ \t\n\r\f\v]", 
                    # but not space
                    tmp = re.sub("[\t\n\r\f\v]","",t)
            except (IOError,) as e:
                tracker()
                message = """
                \rReading file name contained in the "%s" option 
                argument\r\n%s\r\nfailed\r\n
                """ % (arg,value)
                sys.stdout.write(message)
            # if an exception (a file name), replace as well
            d[arg] = tmp 
    return d


parser = argparse.ArgumentParser( # reachable from other modules
    prog = sys.argv[0],
    description = """
    An NCBI e-utility client.
    It has been designed to give some direction as to what 
    databases, eutilities, and arguments can be used with the
    service, but apart from that, to give the User freedom of
    choosing how to make his/her search. This also means that
    the client won\'t successfully retrieve data unless the User
    supplies input of the appropriate format, and appropriately
    combines option arguments.
    """,
    # to be able to override any older arguments ...
    # if this parser is used as a parent
    conflict_handler = "resolve", 
    prefix_chars = "-",
    add_help = True
)
ch = list(CHOICES.get("db"))
ch.sort()
parser.add_argument(
    "--db",
    dest = "db",
    required = True,
    choices = ch,
    help = """
    Database containing the UIDs in the input list. The value
    must be a valid Entrez database name (default = pubmed). 
    """
)
ch = list(CHOICES.get("eutility"))
ch.sort()
parser.add_argument(
    "--eutility", 
    dest = "eutility",
    required = True,
    choices = ch,
    help = """
    One of "esearch": text searches; "epost": UID uploads;
    "esummary": document summary uploads; " elink": entrez
    links; "ecitmatch": batch citation searching in PubMed;
    "efetch": data record downloads; "einfo": database 
    statistics; "egquery": global query; "espell": spelling 
    suggestions
    """
)
parser.add_argument(
    "--bdata",
    dest = "bdata",
    required = False,
    help = """
    Citation strings. Each input citation must be 
    represented by a citation string in the following format:
    journal_title|year|volume|first_page|author_name|your_key|
    Multiple citation strings may be provided by separating 
    the strings with a carriage return character
    ([percent sign]0D). The your_key value is an arbitrary 
    label provided by the user that may serve as a local 
    identifier for the citation, and it will be included in 
    the output. Be aware that all spaces must be replaced by
    '+' symbols and that citation strings should end with a 
    final vertical bar '|'. 
    """
)
ch = list(CHOICES.get("cmd"))
ch.sort()
parser.add_argument(
    "--cmd",
    dest = "cmd",
    required = False,
    choices = ch,
    help = """Command used with "elink" """
)
parser.add_argument(
    "--complexity",
    dest = "complexity",
    required = False,
    help = """
    Data content to return. Many sequence records are part
    of a larger data structure or "blob", and the complexity
    parameter determines how much of that blob to return. For
    example, an mRNA may be stored together with its protein 
    product. The available values are as follows:
    0 (entire blob), 1 (bioseq), 2 (minimal bioseq-set), 3 
    (minimal nuc-prot), 4 (minimal pub-set)
    """,
    choices = list(CHOICES.get("complexity"))
)
parser.add_argument(
    "--datetype",
    dest = "datetype",
    required = False,
    help = """
    Type of date used to limit a search. The allowed values 
    vary between Entrez databases, but common values are 'mdat'
    (modification date), 'pdat' (publication date) and 'edat' 
    (Entrez date). Generally an Entrez database will have only 
    two allowed values for datetype.
    """
)
parser.add_argument(
    "--email",
    dest = "email",
    required = True,
    help = """
    E-mail address of the E-utility user. Value must be a string
    with no internal spaces, and should  be a valid e-mail address.
    """
)
parser.add_argument(
    "--field",
    dest = "field",
    required = False,
    help = """
    Search field. If used, the entire search term will be limited
    to the specified Entrez field.
    """
)
parser.add_argument(
    "--fromdb",
    dest = "fromdb",
    required = False,
    help = """
    Used together with "elink" to link UIDs from one database to
    another, ie. "fromdb" (source) to "db" (destination)
    """
)
parser.add_argument(
    "--holding",
    dest = "holding",
    required = False,
    help = """ 
    Used with "elink".Name of LinkOut provider. Only URLs for the
    LinkOut provider specified by holding will be returned. 
    """
)
parser.add_argument(
    "--id",
    dest = "id",
    required = False,
    help = """
    UID list.
    Either a single UID or a comma-delimited list of UIDs may be
    provided. All of the UIDs must be from the database specified 
    by db. There is no set maximum for the number of UIDs that can 
    be passed to ESummary, but if more than about 200 UIDs are to
    be provided, the request should be made using the HTTP POST 
    method. If the argument is a path to a file, then that file is
    expected to contain the UID list. If the argument is not a path
    to a file, then it is expected to be the "UID list".
    """
)
parser.add_argument(
    "--linkname",
    dest = "linkname",
    required = False,
    help = """ 
    Name of the Entrez link to retrieve. Every link in Entrez is
    given a name of the form "dbfrom_db_subset". The values of
    subset vary depending on the values of dbfrom and db. Many 
    dbfrom/db combinations have no subset values. The linkname 
    parameter only functions when cmd is set to neighbor or 
    neighbor_history.
    """
)
parser.add_argument(
    "--maxdate",
    dest = "maxdate",
    required = False,
    help = """
    Date range used to limit a search result by the date specified
    by datetype. These two parameters (mindate, maxdate) must be
    used together to specify an arbitrary date range. The general
    date format is YYYY/MM/DD, and these variants are also allowed:
    YYYY, YYYY/MM.
    """
)
parser.add_argument(
    "--mindate",
    dest = "mindate",
    required = False,
    help = """
    Date range used to limit a search result by the date specified
    by datetype. These two parameters (mindate, maxdate) must be used 
    together to specify an arbitrary date range. The general date 
    format is YYYY/MM/DD, and these variants are also allowed: YYYY, 
    YYYY/MM.
    """
)
parser.add_argument(
    "--output",
    dest = "output",
    required = True,
    help = """
    path to file for output
    """
)
parser.add_argument(
    "--query_key",
    dest = "query_key",
    required = False,
    help = """
    Query key. This integer specifies  which of the UID lists 
    attached to the given  Web Environment will be used as input to
    ESummary. Query keys are obtained from the output of previous
    ESearch, EPost or ELink calls. The query_key parameter must
    be used in conjunction with WebEnv. Values for query keys may
    also be provided in term if they are preceeded by a '#' 
    ([percent sign]23 in the URL). While only one query_key parameter
    can be provided to ESearch, any number of query keys can be 
    combined in term. Also, if query keys are provided in term, they 
    can be combined with OR or NOT in addition to AND.
    """
)
parser.add_argument(
    "--quiet",
    dest = "quiet",
    required = False,
    choices = ['y','n'],
    help = """
    Refers to this client: If false, then URL and  POSTFIELDS are 
    printed to STDOUT.
    """
)
parser.add_argument(
    "--reldate",
    dest = "reldate",
    required = False,
    help = """
    When reldate is set to an integer n, the search  returns only
    those items that have a date specified by datetype within the 
    last n days.
    """
)
parser.add_argument(
    "--retmax",
    dest = "retmax",
    required = False,
    help = """
    Total number of UIDs from the retrieved set to be shown in the
    XML output (default=20). By default, ESearch only includes the 
    first 20 UIDs retrieved in the XML output. If usehistory is set
    to 'y', the remainder of the retrieved set will be stored on
    the History server; otherwise these UIDs are lost.
    """
)
ch = list(CHOICES.get("retmode"))
ch.sort()
parser.add_argument(
    "--retmode",
    dest = "retmode",
    required = False,
    choices = ch,
    help = """
    Retrieval mode. This parameter specifies the data format of the
    records returned, such as plain text, HMTL or XML. 
    """
)
ch =  list(CHOICES.get("rettype"))
ch.sort()
parser.add_argument(
    "--rettype",
    dest = "rettype",
    required = False,
    choices = ch,
    help = """
    Retrieval mode. This parameter specifies the data format of the
    records returned, such as plain text, HMTL or XML
    """
)
parser.add_argument(
    "--retstart",
    dest = "retstart",
    required = False,
    help = """
    Sequential index of the first UID in the retrieved set to be
    shown in the XML output (default=0, corresponding to the first 
    record of the entire set). This parameter can be used in  
    conjunction with retmax to download an arbitrary subset of UIDs 
    retrieved from a search.
    """
)
parser.add_argument(
    "--seq_start",
    dest = "seq_start",
    required = False,
    help = """ 
    First sequence base to retrieve. The value should be the integer
    coordinate of the first desired base, with "1" representing the 
    first base of the seqence.
    """
)
parser.add_argument(
    "--seq_stop",
    dest = "seq_stop",
    required = False,
    help = """
    Last sequence base to retrieve. The value should be the integer
    coordinate of the last desired base, with "1" representing the 
    first base of the seqence.
    """
)
parser.add_argument(
    "--sort",
    dest = "sort",
    required = False,
    help = """
    Specifies the method used to sort UIDs in the ESearch output. 
    The available values vary by database (db) and may be found in
    the Display Settings menu on an Entrez search results page. If 
    usehistory is set to 'y', the UIDs are loaded onto the History
    Server in the specified sort order and will be retrieved in that
    order by ESummary or EFetch. Example values are 'relevance' and
    'name' for Gene and 'first+author' and 'pub+date' for PubMed. 
    Users should be aware that the default value of sort varies from
    one database to another, and that the default value used by 
    ESearch for a given database may differ from that used on NCBI
    web search pages.
    """
)
parser.add_argument(
    "--strand",
    dest = "strand",
    required = False,
    help = """ 
    Strand of DNA to retrieve. Available  values are "1" for the plus
    strand and "2" for the minus strand.
    """,
    choices = list(CHOICES.get("strand"))
)
parser.add_argument(
    "--term",
    dest = "term",
    required = False,
    help = """ 
    Entrez text query. If the argument is a path to a file, then that
    file is expected to contain term. If the argument is not a path to
    a file, then it is expected to be the "term".
    """
)
parser.add_argument(
    "--tool",
    dest = "tool",
    required = False,
    default = "Mozilla/5.0",
    help = """
    Name of application making the E-utility call. Value must be a 
    string with no internal spaces.
    """
)
parser.add_argument(
    "--usehistory",
    dest = "usehistory",
    choices = list(CHOICES.get("usehistory")),
    required = False,
    help = """
    When usehistory is set to 'y', ESearch will post the UIDs resulting 
    from the search operation onto the History server so that they can
    be used directly in a subsequent E-utility call. Also, usehistory 
    must be set to 'y' for ESearch to interpret query key values 
    included in term or to accept a WebEnv as input.
    """
)
parser.add_argument(
    "--version",
    dest = "version",
    required = False,
    help = """
    Used to specify version 2.0 EInfo XML. The only supported value is
    '2.0'. When present, EInfo will return XML that includes two new 
    fields: <IsTruncatable>  and <IsRangeable>. Fields that are 
    truncatable allow the wildcard character '*' in terms. The wildcard 
    character will expand to match any set of characters up to a limit 
    of 600 unique expansions. Fields that are rangeable allow the range 
    operator ':' to be placed between a lower and upper limit for the 
    desired range (e.g. 2008:2010[pdat]).
    """,
    choices = list(CHOICES.get("version"))
)
parser.add_argument(
    "--WebEnv",
    dest = "WebEnv",
    required = False,
    help = """
    \rWeb Environment. If provided, this parameter specifies the Web 
    Environment that will receive the UID list sent by post. EPost will
    create a new query key associated with that Web Environment. Usually
    this WebEnv value is obtained from the output of a previous ESearch,
    EPost or ELink call. If no WebEnv parameter is provided, EPost will
    create a new Web Environment and post the UID list to query_key 1.
    """
)


def main(parser,argv):
    """ For command-line use
    """
    t0 = time.clock()

    argv = parser.parse_args(args = argv)
    argvd = vars(argv) # Namespace -> dictionary
    outputfile = argvd.pop("output")
    if os.path.isdir(outputfile):
        message = "\ros.path.isdir(outputfile)\r\n"
        parser.error(message)
    try: # wanna find out if works, that's all
        with open(outputfile,"w") as fd:
            pass
    except (IOError,) as e:
        message = """
        \r<output> == "%s"\r\nMaybe not a valid file path?\r\n
        """ % (outputfile,)
        parser.error(message)
    if argvd.has_key("quiet"):
        quiet = argvd.get("quiet")
        global QUIET
        if quiet == 'y':
            QUIET = True
        else:
            QUIET = False
    #Set argument from file, if appropriate    
    argvd = arg_from_file(argvd, "term")
    argvd = arg_from_file(argvd, "id")
    # filter out None arguments
    argvd = dict([(k,v) for k,v in argvd.iteritems() if v != None])

    postfields,URL = form_url(**argvd)
    http_post(outputfile, postfields, URL)
    t1 = time.clock()
    message = "\rElapsed time: %f s\r\n" % (t1-t0,)
    sys.stdout.write(message)
    parser.exit(status=0, message=None)


if __name__ == "__main__":
    main(parser, sys.argv[1:])
