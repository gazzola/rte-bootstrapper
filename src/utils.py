# -*- coding: utf-8 -*-

'''
Utility functions.
'''

import re
from xml.etree import cElementTree as ET
from xml.dom import minidom
from nltk.tokenize.regexp import RegexpTokenizer

def generate_filter(ending_without_punctuation=False, starting_with=None):
    '''
    Generate and return a filter function with the provided requirements.
    
    :param ending_without_punctuation: boolean indicating to discard sentences
        without trailing ".", "?" or "!"
    :param starting_with: list of strings. Sentences starting with any of those
        are discarded.
    '''
#     if without_verb:
#         tagger = nlpnet.POSTagger(config.nlpnet_model, 'pt')
    
    def filter_out(sentence):
        if sentence == '':
            return True
        
        if ending_without_punctuation and sentence[-1] != '.':
            return True
        
        if starting_with is not None:
            for substring in starting_with:
                if sentence.startswith(substring):
                    return True
        
#         if without_verb:
#             tagged = tagger.tag(sentence)
#             has_verb = any((tag == 'V' or tag == 'PCP')
#                            for _, tag in tagged)
#             if not has_verb:
#                 return True            
        
        return False
    
    return filter_out

def read_lines(filename):
    '''
    Read the file with the given name and return a list containing all lines in it.
    '''
    if filename is None:
        return None
    
    with open(filename, 'rb') as f:
        text = unicode(f.read(), 'utf-8')
    
    return text.splitlines()

def detokenize(tokens):
    '''
    Create a string from the given tokens, using whitespace where needed.
    '''
    s = ' '.join(tokens)
    s = re.sub(' ([.,;:?!()])', r'\1', s)
    return s

def tokenize_sentence(text, preprocess=True):
    '''
    Tokenize the given sentence and applies preprocessing if requested 
    (conversion to lower case and digit substitution).
    '''
    if preprocess:
        text = re.sub(r'\d', '9', text.lower())
    
    tokenizer_regexp = ur'''(?ux)
    ([^\W\d_]\.)+|                # one letter abbreviations, e.g. E.U.A.
    \d{1,3}(\.\d{3})*(,\d+)|      # numbers in format 999.999.999,99999
    \d{1,3}(,\d{3})*(\.\d+)|      # numbers in format 999,999,999.99999
    \d+:\d+|                      # time and proportions
    \d+([-\\/]\d+)*|              # dates. 12/03/2012 12-03-2012
    [DSds][Rr][Aa]?\.|            # common abbreviations such as dr., sr., sra., dra.
    [Mm]\.?[Ss][Cc]\.?|           # M.Sc. with or without capitalization and dots
    [Pp][Hh]\.?[Dd]\.?|           # Same for Ph.D.
    [^\W\d_]{1,2}\$|              # currency
    (?:(?<=\s)|^)[\#@]\w*[A-Za-z_]+\w*|  # Hashtags and twitter user names
    -[^\W\d_]+|                   # clitic pronouns with leading hyphen
    \w+([-']\w+)*|                # words with hyphens or apostrophes, e.g. não-verbal, McDonald's
    -+|                           # any sequence of dashes
    \.{3,}|                       # ellipsis or sequences of dots
    \S                            # any non-space character
    '''
    tokenizer = RegexpTokenizer(tokenizer_regexp)
    
    return tokenizer.tokenize(text)

class XmlWriter(object):
    '''
    Class to generate an XML tree iteratively (i.e., allowing new pairs to be
    added at any time) and to write XML files.
    '''
    def __init__(self, **attribs):
        '''
        Initialize the root element of the XML tree. Any arguments are given
        to the XML root.
        '''
        self.root = ET.Element('entailment-corpus', attribs)
        self.pair_id = 1
    
    def add_pairs(self, pairs, cluster=None):
        '''
        Add the given pairs to the XML tree.
        '''
        for pair in pairs:
            xml_attribs = {'id': str(self.pair_id), 
                           'entailment': 'UNKNOWN'}
            self.pair_id += 1
            
            if cluster is not None:
                xml_attribs['cluster'] = str(cluster)
            
            # add any other attributes present in the pair
            xml_attribs.update(pair.attribs)
            
            xml_pair = ET.SubElement(self.root, 'pair', xml_attribs)
            xml_t = ET.SubElement(xml_pair, 't', pair.t_attribs)
            xml_h = ET.SubElement(xml_pair, 'h', pair.h_attribs)
            xml_t.text = pair.t.strip()
            xml_h.text = pair.h.strip()
    
    def write_file(self, filename, pretty_print=False):
        '''
        Write the actual XML file
        '''
        if pretty_print:
            xml_string = ET.tostring(self.root, 'utf-8')
            reparsed = minidom.parseString(xml_string)
        
            with open(filename, 'wb') as f:
                f.write(reparsed.toprettyxml('    ', '\n', 'utf-8'))
        else:
            tree = ET.ElementTree(self.root)
            tree.write(filename, 'utf-8', True)
