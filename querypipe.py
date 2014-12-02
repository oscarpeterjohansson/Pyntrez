#!/usr/bin/python
""" An Esearch Pipeline

An NCBI eutilities, esearch pipeline. Although it would be possible
to provide any eutility as argument, it was meant for esearch. In
contrast ot the main program, this one allows the "term" argument
to be a path to a file with several queries/terms in a comma-
delimited list. The User must ensure that these are formatted 
according to specifications by the NCBI, just as with the main
program. This program was makes use of the the "usehistory",
"query_key", and "WebEnv" arguments to minimize the number of 
requests. With the help of this program, a single Efetch or Esummary
request should suffice to retrieve data from all queries.

While only one query_key parameter can be provided to ESearch, any 
number of query keys can be combined in term


With Python Interpreter: Use "params_editing" and "query_posting"
From the Command-line: Use "--help" for info on execution
"""

__author__ = "Johansson, O."
__email__ = "oscarpeterjohansson@outlook.com"
__contributors__ = ""
__version__ = "1.0"
__licence__ = "GPL-3"


import argparse
import os
import re
import sys
# to be able to import eutil.py. when __name__ == "__main__"
# else, "entrez" is a pkg - import entrez and work from there
sys.path.append(os.path.dirname(sys.argv[0]))
import eutil # homebrew
import subprocess
import tempfile
import time
import traceback
import xml.etree.ElementTree as ET


ESPATTERNS = ( # this an appropriate order
    "QueryTranslation",
    "Count",
    "RetMax",
    "RetStart",
    "QueryKey",
    "WebEnv",
    "IdList"
)
# NCBI recommends that users post no more than three URL requests per second.
COUNT = 0
POST_LMT = 3                # posts per T_LMT
T_ACC = [0 for i in range(POST_LMT)] # array: time accumulated, max length POST_LMT
T_LMT = 1.0                 # time limit in sec
WEBENV = None


def tracker():
    """ traceback """
    t,v,tb = sys.exc_info()
    traceback.print_exception(t,v,tb,file=sys.stdout)


def params_editing(params):
    """ 
    A comma-delimited list of queries, to be specified one at a 
    time using the "term" optional argument accepted by the 
    Eutilities service, should be supplied with keyword "term" 
    in params. "path_to_exec" is a path to the executatable file.
    """
    s_dta = None  # file read
    s_term = None # str eutility "term": comma-delimited list in file
    try:
        s_term = params.pop("term")
    except (KeyError,) as e:
        tracker()
        message = """\rKeyError: "term" argument missing\r\n"""
        sys.stdout.write(message)
        return None
    if s_term != None and not os.path.isfile(s_term):
        tracker()
        message = """\ros.path.isfile(term) == False\r\n"""
        sys.stdout.write(message)
        return None
    try:
        with open(s_term, 'r') as fd:
            s_dta = fd.read()
            s_dta = re.sub("[\r\n]","",s_dta)
    except (IOError,) as e:
        tracker()
        message = "\r\nCouldn't open or read <inputfile>. Sorry ...\r\n"
        sys.stdout.write(message)
        return None
    l_term = s_dta.split(',')
    l_term = filter(lambda x: x != "", l_term)
    l_term = [s.strip() for s in l_term] 
    params["rettype"] = "xml"   # force xml formatting
    return (l_term, params)


def params_pfxing(params):
    """
    "Convert" the keywords in the params dictionary to "arguments"
    prefixed with single-dash if of length one, else with '--', 
    double-dashes.
    """
    return dict([('-'+k,v) if len(k)==1 else ("--"+k,v) for k,v in params.iteritems()])
    

def spd_enf(t0):
    """ Speed Limit Enforcement
    NCBI recommends that users post no more than three URL requests
    per second.
    """
    global COUNT, T_ACC
    t1 = time.clock()
    t_inst = sum(T_ACC)
    T_ACC.pop()
    T_ACC.insert(0, t1-t0)
    if COUNT <= POST_LMT:
        COUNT += 1 # initially, array contains zeros
    if t_inst < T_LMT and COUNT > POST_LMT:
        dla = T_LMT-t_inst
        # must add time delayed
        T_ACC[0] += dla
        sys.stdout.write("\rCourtesy delay: %f s\r\n" % (dla,))
        time.sleep(dla)


def find_text(dta,iterable):
    """ Find patterns in xml string  """
    row = []
    for p in iterable:
        # ".*?", non-greedy (ie. first match); without "?" would be greedy
        # DOTALL -> "." matches all, including newline
        m = re.search("(?P<%s>(?<=<%s>).*?(?=</%s>))" % (p,p,p), dta, re.DOTALL) 
        v = ""
        if m != None:
            v = m.group(p)
            if p == "IdList":
                IdList = re.findall("(?<=<Id>).*(?=</Id>)", v)
                v = ','.join(IdList)
        row.append(v)
    return tuple(row)


def readtmp(inputfile):
    """ 
    Parse xml file with and return root element on success
    """
    t_max = 10
    elaps = 0
    dla = 2
    s_xml = ""
    while len(s_xml) == 0 and elaps <= t_max:
        try:
            with open(inputfile, 'r') as fd:
                fd.seek(0,0)
                s_xml = fd.read()
        except (IOError,) as e:
            tracker()
            return ""
        if len(s_xml) == 0 and elaps + dla <= t_max:
            time.sleep(dla)
            elaps += dla
            continue
        elif len(s_xml) == 0 and elaps + dla > t_max:
            ms = "\rReached t_max (%s s) in readtmp function\r\n" % (t_max,)
            sys.stdout.write(ms)
            return ""
        else:
            break
        return ""
    return s_xml


def query_posting(l_term, params, path_to_exec):
    """ 
    Post queries, one at a time. XML responses will be written to a 
    temporary file and then parsed. The results from that parsing is
    written to the output file supplied as argument with params. The
    WebEnv obtained from the first query is used for the successive 
    queries, such that UIDs are appended to that and data for all
    queries can be retrieved with one instance of efetch or esummary.

    l_term == list of queries (strings), obtained from other function;
    params == keyword arguments to use with E-utilities service;
    path_to_exec == path to executable
    """
    # for parsed output, avail. after exec.
    op_file = params.get("output")  
    #params["usehistory"] = 'y' # actually required at command-line
    with open(op_file, 'w') as op_fd:
        h = '\t'.join(("Query",)+ESPATTERNS) + "\r\n"
        op_fd.write(h)
        for i in xrange(len(l_term)):
            q = l_term[i]
            t0 = time.clock()
            with tempfile.NamedTemporaryFile(mode="w+t") as tmp_fd:
                args = ["python", path_to_exec]
                # content of tmp file continously replaced with each query
                params["term"] = q
                params["output"] = tmp_fd.name
                global ESPATTRNS, WEBENV
                if WEBENV != None:
                    params["WebEnv"] = WEBENV
                pfx_params = params_pfxing(params)
                for k,v in pfx_params.iteritems():
                    args.extend([k,v])
                retcode = None
                try:
                    sys.stdout.write("\rARGS\r\n%s\r\n" % (" ".join(args),))
                    retcode = subprocess.check_call(args, shell=False)
                except (subprocess.CalledProcessError, OSError, ValueError) as e:
                    tracker()
                    continue
                if retcode != 0:
                    return
                s_xml = readtmp(tmp_fd.name)
                if len(s_xml) == 0:
                    continue
                t = find_text(s_xml, ESPATTERNS) # tuple
                if WEBENV == None:
                    WEBENV = t[5]
                st = '\t'.join((q,)+t) # incl. "raw query"
                st += "\r\n"
                op_fd.write(st)
            if i != (len(l_term)-1): # if items remaining, a delay may be necessary
                spd_enf(t0) # speed limit enforcement (delay), out of courtesy
            message = "\rPercentage completed: %s %%\r\n" %  (str(round(float(i+1)/len(l_term)*100,2)),)
            sys.stdout.write(message)
            sys.stdout.write("\r\n")
    return None


def smry2id(inp,outp):
    """
    Making use of the query_posting output: A convenient function would be 
    one that extracted the UIDs and put them in another file.
    """
    idx = 0
    s_in, s_uid = "",""
    try:
        with open(inp,'r') as fd:
            s_in = fd.read()
    except (IOError,) as e:
        ms = """\rWhoops-a-daisy, couldn\'t open and read the query_posting 
        \routput from the inputfile\r\n"""
        sys.stdout.write(ms)
        return None
    l_tmp = re.split("\r\n|\n",s_in) # try "\r\n" first, then just "\n"
    l_tmp = filter(lambda x: x != "", l_tmp)
    l_dta = [re.split("\t",t) for t in l_tmp]
    try:
        idx = l_dta[0].index("IdList")
    except (ValueError,) as e:
        ms = """\r\"IdList\" is missing in the first line. You might have provided
        \r an inproper file?\r\n"""
        sys.stdout.write(ms)
        return None
    s_uid = ",".join([l_dta[i][idx] for i in xrange(1,len(l_dta))])
    s_uid = re.sub(",+",",",s_uid) # one or more commas
    s_uid = re.sub("[\t\n\r ]","",s_uid) # whitespace away
    try:
        with open(outp,'w') as fd:
            fd.write(s_uid)
    except (IOError,) as e:
        ms = "\rSo sorry, couldn't write output to file ...\r\n"
        sys.stdout.write(ms)
        return None
    return None


def fname_apnd(filename, text):
    """ append text to filename """
    dn = os.path.dirname(filename)
    bn = os.path.basename(filename)
    text = re.sub(" ","_",text)
    l_bn = re.split("[.]",bn)
    p1 = '.'.join(l_bn[:len(l_bn)-1])
    p3 = '.'.join(l_bn[(len(l_bn)-1):])
    s_bn = p1 + text + '.' + p3
    return os.path.join(dn, s_bn)


parser = argparse.ArgumentParser(
    # inherit argument options from "eut"
    parents = [eutil.parser],  
    #update progr
    prog = sys.argv[0], 
    # to be able to override any older arguments ...
    conflict_handler = "resolve",
    #update description
    description = """
    An NCBI eutilities, esearch pipeline. Although it would be possible
    to provide any eutility as argument, it was meant for esearch. In
    contrast to the main program, this one allows the "term" argument
    to be a path to a file with several queries/terms in a comma-
    delimited list. The User must ensure that these are formatted 
    according to specifications by the NCBI, just as with the main 
    program. This program makes use of the the "usehistory", and 
    "WebEnv" arguments to minimize the number of requests. With the
    help of this program, a single Efetch or Esummary request should
    suffice to retrieve data for all queries.
    """ 
)
# eutility option {esearch}
parser.add_argument( 
    "--term",
    dest = "term",
    required = True,
    help = """ 
    Entrez text query. A path to a file containing a commna-delimited 
    list of queries ("term":s). The list of queries are expected to 
    constitute a group. The output will include a WebEnv and query_key
    to retrieve the results from all queries with a single request using
    Efetch or Esummary.
    """ # updated help description
)
parser.add_argument(
    "--usehistory",
    dest = "usehistory",
    choices = list(eutil.CHOICES.get("usehistory")),
    required = True, # updated to "True"
    help = """
    When usehistory is set to 'y', ESearch will post the UIDs resulting 
    from the search operation onto the History server so that they can
    be used directly in a subsequent E-utility call. Also, usehistory 
    must be set to 'y' for ESearch to interpret query key values 
    included in term or to accept a WebEnv as input.
    """
)


def main(parser, argv):
    """ For command-line use
    """
    dn = os.path.dirname(sys.argv[0])
    path_to_exec = os.path.join(dn,"eutil.py")
    argv = parser.parse_args(args = argv)
    argvd = vars(argv) # Namespace -> dictionary
    argvd = dict([(k,v) for k,v in argvd.iteritems() if v != None])
    l_term, argvd = params_editing(argvd)
    op_file = argvd.get("output")
    query_posting(l_term, argvd, path_to_exec)
    # uid-only output-file:
    nn = fname_apnd(op_file, "_IdList")
    smry2id(op_file, nn)
    parser.exit(status=0, message=None)


if __name__ == "__main__":
    main(parser, sys.argv[1:])


