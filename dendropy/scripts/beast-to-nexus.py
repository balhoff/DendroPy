#! /usr/bin/env python

from dendropy import datasets
import os
import sys
from optparse import OptionGroup
from optparse import OptionParser
from xml.dom import minidom
from StringIO import StringIO
import re

_prog_usage = '%prog [<BEAST-FILEPATH>] [<NEXUS-FILEPATH>]]'
_prog_version = 'BEAST-to-NEXUS Version 1.0'
_prog_description = 'reads a BEAST formatl XML file and writes character data in NEXUS format'
_prog_author = 'Jeet Sukumaran'

def main():
    """
    Main CLI handler.
    """
    
    parser = OptionParser(usage=_prog_usage, 
        add_help_option=True, 
        version=_prog_version, 
        description=_prog_description)            
        
    parser.add_option('-q', '--quiet',
        action='store_true',
        dest='quiet',
        default=False,
        help='run silently except for dest')
        
    parser.add_option('-r', '--replace',
        action='store_true',
        dest='replace',
        default=False,
        help='replace dest file if writing to a file')

    (opts, args) = parser.parse_args()
        
    if len(args) == 0:
        if not opts.quiet:
            sys.stderr.write("(reading from standard input)\n")
        src = sys.stdin
    elif len(args) >= 1:            
        fpath = os.path.expanduser(os.path.expandvars(args[0]))
        if not os.path.exists(fpath):
            sys.stderr.write('File not found: %s\n' % fpath)
            sys.exit(1)
        src = open(fpath, "rU")
        
    if len(args) >= 2:
        fpath = os.path.expanduser(os.path.expandvars(args[1]))
        if os.path.exists(fpath):
            if opts.replace:
                dest = open(fpath, "w")
            else:
                sys.stderr.write('"%s" already exists: Overwrite (y/N)? ' % fpath)
                i = sys.stdin.read(1)
                if i.upper() != "Y":
                    sys.stderr.write("Aborting.\n")
                    sys.exit(1)
                else:
                    dest = open(fpath, "w")
        else:
            dest = open(fpath, "w")
    else:
        dest = sys.stdout
                                
    beast = minidom.parse(src)            
    alignments = beast.getElementsByTagName("alignment")   
    if len(alignments) == 0:
        sys.stderr.write("ERROR: could not find 'alignment' element in file\n")
        sys.exit(1)
    elif len(alignments) > 1:
        sys.stderr.write("ERROR: standard NEXUS cannot represent multiple alignments at this time\n")
        sys.exit(1)
    whitespace = re.compile('( |\t|\r|\n)')
    tax_labels = []
    char_matrix = {}
    for sidx, seq in enumerate(alignments[0].getElementsByTagName("sequence")):
        tax_elements = seq.getElementsByTagName("taxon")
        if len(tax_elements) == 0:
            sys.stderr.write('ERROR: no taxon associated with sequence %d\n' % (sidx))
            sys.exit(1)                    
        tax_label = tax_elements[0].getAttribute("idref")
        tax_labels.append(tax_label)
        for cidx, cnode in enumerate(seq.childNodes):
            chars = StringIO()
            if cnode.nodeType == cnode.TEXT_NODE:
                chars.write(cnode.wholeText)
        chars = whitespace.sub("", chars.getvalue())
        char_matrix[tax_label] = chars
    
    nchar = len(char_matrix.values()[0])
    for t in tax_labels:
        if len(char_matrix[t]) != nchar:
            sys.stderr.write('ERROR: unequal sequence lengths in matrix\n')
            sys.exit(1)
            
    dest.write("#NEXUS\n\n")
        
    dest.write("BEGIN TAXA;\n")
    dest.write("  DIMENSIONS NTAX=%d;\n" % len(char_matrix))
    dest.write("  TAXLABELS\n")
    for tax_label in tax_labels:
        dest.write("    %s\n" % tax_label)
    dest.write("  ;\n")
    dest.write("END;\n\n")
    
    max_tax_label = max([len(t) for t in tax_labels])
    dest.write("BEGIN CHARACTERS;\n")
    dest.write("   DIMENSIONS NCHAR=%d;\n" % nchar)
    dest.write("   FORMAT DATATYPE=DNA MISSING=? GAP=-;\n")
    dest.write("   MATRIX\n")
    for tax_label in tax_labels:
        dest.write("    %s      %s\n" % (tax_label.ljust(max_tax_label), char_matrix[tax_label]))
    dest.write("  ;\n")
    dest.write("END;\n")
    
    if not opts.quiet:
        sys.stderr.write("Converted to NEXUS: %d taxa and %d characters per taxon\n" % (len(char_matrix), nchar))    
    
if __name__ == '__main__':
    main()

    
