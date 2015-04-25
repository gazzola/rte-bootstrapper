# -*- coding: utf-8 -*-


import os
from collections import OrderedDict
import nltk

import utils

class CorpusManager(object):
    '''
    Class to manage huge corpora. It iterates over the documents in a directory. 
    '''
    
    def __init__(self, directory, recursive=True):
        '''
        Constructor. By default, iterating over the corpus returns the tokens, 
        not their id's. Use `set_yield_ids` to change this behavior.
        cm.
        
        :param directory: the path to the directory containing the corpus
        :param recursive: whether subdirectories should be accessed
        '''
        # use unicode to make functions from os module return unicode objects
        # this is important to get the correct filenames
        self.directory = unicode(directory)
        self.recursive = recursive
        self.yield_tokens = True
        self.files = os.listdir(self.directory)
    
    def set_yield_tokens(self):
        '''
        Call this function in order to set the corpus manager to yield lists
        of tokens (instead of their id's).
        '''
        self.yield_tokens = True
    
    def set_yield_ids(self, dictionary):
        '''
        Call this function in order to set the corpus manager to yield the token
        id's (instead of the tokens themselves).
        '''
        self.yield_tokens = False
        self.dictionary = dictionary
    
    def __len__(self):
        '''
        Return the number of documents this corpus manager deals with.
        '''
        return len(self.files)
    
    def __getitem__(self, index):
        '''
        Overload the [] operator. Return the i-th file in the observed directory.
        Note that this is read only.
        '''
        return self.files[index]
    
    def get_text_from_file(self, path):
        '''
        Return the text content from the given path
        '''
        with open(path, 'rb') as f:
            text = f.read().decode('utf-8')
        
        return text        
    
    def get_sentences_from_file(self, path):
        '''
        Return a list of sentences contained in the document, without any preprocessing
        or tokenization.
        '''
        text = self.get_text_from_file(path)
        
        # we assume that lines contain whole paragraphs. In this case, we can split
        # on line breaks, because no sentence will have a line break within it.
        # also, it helps to properly separate titles without a full stop
        paragraphs = text.split('\n')
        sentences = []
        sent_tokenizer = nltk.data.load('tokenizers/punkt/portuguese.pickle')
        
        for paragraph in paragraphs:
            # don't change to lower case yet in order not to mess with the
            # sentence splitter
            par_sentences = sent_tokenizer.tokenize(paragraph, 'pt')
            sentences.extend(par_sentences)
        
        return sentences        
        
    def get_tokens_from_file(self, path): 
        '''
        Tokenize and preprocesses the given text.
        Preprocessing includes lower case and conversion of digits to 9.
        '''
        sentences = self.get_sentences_from_file(path)
        
        all_tokens = [token
                      for sent in sentences
                      for token in utils.tokenize_sentence(sent, True)]
        
        return all_tokens
    
    def _iterate_on_dir(self, path):
        '''
        Internal helper recursive function.
        '''
        for filename in os.listdir(path):
            full_path = os.path.join(path, filename)
            if os.path.isdir(full_path):
                if not self.recursive:
                    continue
                
                for item in self._iterate_on_dir(full_path):
                    yield item
            else:
                # this is a file
                tokens = self.get_tokens_from_file(full_path)
                
                if self.yield_tokens:
                    yield tokens
                else:
                    yield self.dictionary.doc2bow(tokens)

    def __iter__(self):
        '''
        Yield the text from a document inside the corpus directory.
        Stopwords are filtered out.
        '''
        return self._iterate_on_dir(self.directory)
                

class SentenceCorpusManager(CorpusManager):
    '''
    This class manages corpus access, and provides one sentence at a time.
    It also supports indexing the n-th sentence of the m-th document.
    
    This class stores all corpus content in memory, so it should only be used with small 
    corpora.
    '''
    def __init__(self, directory):
        CorpusManager.__init__(self, directory)
        self._file_num = 0
        self._sent_num = None
        self._load_corpus()
        
    def _load_corpus(self):
        '''
        Load the corpus to memory. Exactly repeated sentences are removed.
        '''
        file_num_range = range(len(self.files))
        
        # use a set to avoid repeated sentences
        corpus_sentences = set()
        
        for i in file_num_range:
            file_sentences = self.get_sentences_from_file(i)
            corpus_sentences.update(file_sentences)
        
        self.sentences = list(corpus_sentences)
    
    def __getitem__(self, index):
        return self.sentences[index]
    
    def __len__(self):
        return len(self.sentences)
    
    def __iter__(self):
        '''
        Yield sentences.
        '''
        for sent in self.sentences:
            
            tokens = utils.tokenize_sentence(sent)
            if self.yield_tokens:
                yield tokens
            else:
                yield self.dictionary.doc2bow(tokens)
        
        self._file_num = 0
        self._sent_num = None
    
#     def get_current_file(self):
#         '''
#         Return the number of the file currently being iterated over.
#         '''
#         return self._file_num
#     
#     def get_current_sentence(self):
#         '''
#         Return the number of the last sentence iterated over (within
#         the current file), or None if the iteration hasn't started. 
#         '''
#         return self._sent_num
    
    def get_sentence(self, doc_num, sent_num):
        '''
        Return the n-th sentence from the m-th document, without
        any pre-processing.
        '''
        doc_sents = self.get_sentences_from_file(doc_num)
        return doc_sents[sent_num]
