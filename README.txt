i. esrchsmry.py:

    Parse out relevant information from the XML formatted data
    returned by e-utility Esearch: QueryTranslation, Count, RetMax, 
    RetStart, QueryKey, WebEnv, IdList.



ii. eutil.py:

    Client for NCBI eutilities. No restrictions.



iii. querypipe.py:

    Client that allows multiple queries to be posted with one
    execution. Created for e-utility Esearch (Don't know what 
    happens if another utility is chosen; hence with restrictions). 
    A comma-delimited list of queries (ie. search words, for instance
    drug names, is supplied and a data summary and id-list returned 
    for convenient use with eutil.py. The module depends on
    "eutil.py", and that the latter is located in the same directory
    as this one.



iv. xml2tab.py:

    Convert XML formatted file to tabular file. Quick and dirty.
