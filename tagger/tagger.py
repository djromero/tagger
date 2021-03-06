#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
======
tagger
======

Module for extracting tags from text documents.

Copyright (C) 2011 by Alessandro Presta

Configuration
=============

Dependencies:
python2.7+, nltk, lxml (optional), tkinter (optional)

Usage
=====

Tagging a text document from Python::

    import tagger
    weights = pickle.load(open('data/dict.pkl', 'rb')) # or your own dictionary
    myreader = tagger.Reader() # or your own reader class
    mystemmer = tagger.Stemmer() # or your own stemmer class
    myrater = tagger.Rater(weights) # or your own... (you got the idea)
    mytagger = Tagger(myreader, mystemmer, myrater)
    best_3_tags = mytagger(text_string, 3)

Running the module as a script::

    $ ./tagger.py <text document(s) to tag>

Example::

    $ ./tagger.py tests/*
    Loading dictionary...
    Tags for  tests/bbc1.txt :
    ['bin laden', 'obama', 'pakistan', 'killed', 'raid']
    Tags for  tests/bbc2.txt :
    ['jo yeates', 'bristol', 'vincent tabak', 'murder', 'strangled']
    Tags for  tests/bbc3.txt :
    ['snp', 'party', 'election', 'scottish', 'labour']
    Tags for  tests/guardian1.txt :
    ['bin laden', 'al-qaida', 'killed', 'pakistan', 'al-fawwaz']
    Tags for  tests/guardian2.txt :
    ['clegg', 'tory', 'lib dem', 'party', 'coalition']
    Tags for  tests/post1.txt :
    ['sony', 'stolen', 'playstation network', 'hacker attack', 'lawsuit']
    Tags for  tests/wikipedia1.txt :
    ['universe', 'anthropic principle', 'observed', 'cosmological', 'theory']
    Tags for  tests/wikipedia2.txt :
    ['beetroot', 'beet', 'betaine', 'blood pressure', 'dietary nitrate']
    Tags for  tests/wikipedia3.txt :
    ['the lounge lizards', 'jazz', 'john lurie', 'musical', 'albums']
'''



import collections
import re
from functools import reduce

try:
    from collections import Counter
except ImportError:
    # Python 2.6 lacks the Counter class, so use the back-ported version
    from .counter import Counter


class Tag:
    '''
    General class for tags (small units of text)
    '''

    def __init__(self, string, stem=None, rating=1.0, proper=False,
                 terminal=False):
        '''
        @param string:   the actual representation of the tag
        @param stem:     the internal (usually stemmed) representation;
                         tags with the same stem are regarded as equal
        @param rating:   a measure of the tag's relevance in the interval [0,1]
        @param proper:   whether the tag is a proper noun
        @param terminal: set to True if the tag is at the end of a phrase
                         (or anyway it cannot be logically merged to the
                         following one)

        @returns: a new L{Tag} object
        '''

        self.string  = string
        self.stem = stem or string
        self.rating = rating
        self.proper = proper
        self.terminal = terminal

    def __eq__(self, other):
        return self.stem == other.stem

    def __repr__(self):
        return repr(self.string)

    def __lt__(self, other):
        return self.rating > other.rating

    def __hash__(self):
        return hash(self.stem)


class MultiTag(Tag):
    '''
    Class for aggregates of tags (usually next to each other in the document)
    '''

    def __init__(self, tail, head=None):
        '''
        @param tail: the L{Tag} object to add to the first part (head)
        @param head: the (eventually absent) L{MultiTag} to be extended

        @returns: a new L{MultiTag} object
        '''

        if not head:
            Tag.__init__(self, tail.string, tail.stem, tail.rating,
                         tail.proper, tail.terminal)
            self.size = 1
            self.subratings = [self.rating]
        else:
            self.string = ' '.join([head.string, tail.string])
            self.stem = ' '.join([head.stem, tail.stem])
            self.size = head.size + 1

            self.proper = (head.proper and tail.proper)
            self.terminal = tail.terminal

            self.subratings = head.subratings + [tail.rating]
            self.rating = self.combined_rating()

    def combined_rating(self):
        '''
        Method that computes the multitag's rating from the ratings of unit
        subtags

        (the default implementation uses the geometric mean - with a special
        treatment for proper nouns - but this method can be overridden)

        @returns: the rating of the multitag
        '''

        # by default, the rating of a multitag is the geometric mean of its
        # unit subtags' ratings
        product = reduce(lambda x, y: x * y, self.subratings, 1.0)
        root = self.size

        # but proper nouns shouldn't be penalized by stopwords
        if product == 0.0 and self.proper:
            nonzero = [r for r in self.subratings if r > 0.0]
            if len(nonzero) == 0:
                return 0.0
            product = reduce(lambda x, y: x * y, nonzero, 1.0)
            root = len(nonzero)

        return product ** (1.0 / root)


class Reader:
    '''
    Class for parsing a string of text to obtain tags

    (it just turns the string to lowercase and splits it according to
    whitespaces and punctuation, identifying proper nouns and terminal words;
    different rules and formats other than plain text could be used)
    '''

    match_apostrophes = re.compile(r'`|’')
    match_contractions = re.compile(r'(\w+)\'(m|re|d|ve|s|ll|t)?')
    match_paragraphs = re.compile(r'[\.\?!\t\n\r\f\v]+')
    match_phrases = re.compile(r'[,;:\(\)\[\]\{\}<>]+')
    match_words = re.compile(r'[\w\-\'_/&]+')

    def __call__(self, text):
        '''
        @param text: the string of text to be tagged

        @returns: a list of tags respecting the order in the text
        '''

        text = self.preprocess(text)

        # split by full stops, newlines, question marks...
        paragraphs = self.match_paragraphs.split(text)

        tags = []

        for par in paragraphs:
            # split by commas, colons, parentheses...
            phrases = self.match_phrases.split(par)

            if len(phrases) > 0:
                # first phrase of a paragraph
                words = self.match_words.findall(phrases[0])
                if len(words) > 1:
                    tags.append(Tag(self.clean_word(words[0])))
                    for w in words[1:-1]:
                        tags.append(Tag(self.clean_word(w), proper=w[0].isupper()))
                    tags.append(Tag(self.clean_word(words[-1]),
                                    proper=words[-1][0].isupper(),
                                    terminal=True))
                elif len(words) == 1:
                    tags.append(Tag(self.clean_word(words[0]), terminal=True))

            # following phrases
            for phr in phrases[1:]:
                words = self.match_words.findall(phr)
                if len(words) > 1:
                    for w in words[:-1]:

                        tags.append(Tag(self.clean_word(w), proper=w[0].isupper()))
                if len(words) > 0:
                    tags.append(Tag(self.clean_word(words[-1]),
                                    proper=words[-1][0].isupper(),
                                    terminal=True))

        return tags

    def clean_word(self, word):
        word = word.lower()
        # get rid of contractions and possessive forms
        match = self.match_contractions.match(word)
        if match:
            word = match.group(1)

        return word

    def preprocess(self, text):
        '''
        @param text: a string containing the text document to perform any
                     required transformation before splitting

        @returns:    the processed text
        '''

        text = self.match_apostrophes.sub('\'', text)

        return text


class Stemmer:
    '''
    Class for extracting the stem of a word

    (by default it uses NLTK's implementation of the Snowball (Porter2) stemmer)
    '''

    match_hyphens = re.compile(r'\b[\-_]\b')

    def __init__(self, stemmer=None, language=None):
        '''
        @param stemmer: an object or module with a 'stem' method (defaults to
                        nltk.stem.snowball.SnowballStemmer)

        @param language: language of the text you will be stemming. Only
                         supported if you are using the default SnowballStemmer.
                         Must be one of the following languages: [danish dutch
                         english finnish french german hungarian italian
                         norwegian porter portuguese romanian russian spanish
                         swedish]. Defaults to 'english'.

        @returns: a new L{Stemmer} object
        '''

        if not stemmer:
            from nltk.stem.snowball import SnowballStemmer
            if language:
                stemmer = SnowballStemmer(language)
            else:
                stemmer = SnowballStemmer("english")
        self.stemmer = stemmer

    def __call__(self, tag):
        '''
        @param tag: the tag to be stemmed

        @returns: the stemmed tag
        '''

        string = self.preprocess(tag.string)
        tag.stem = self.stemmer.stem(string)
        return tag

    def preprocess(self, string):
        '''
        @param string: a string to be treated before passing it to the stemmer

        @returns: the processed string
        '''

        # delete hyphens and underscores
        string = self.match_hyphens.sub('', string)

        return string


class Rater:
    '''
    Class for estimating the relevance of tags

    (the default implementation uses TF (term frequency) multiplied by weight,
    but any other reasonable measure is fine; a quite rudimental heuristic
    tries to discard redundant tags)
    '''

    def __init__(self, weights, multitag_size=3):
        '''
        @param weights:       a dictionary of weights normalized in the
                              interval [0,1]
        @param multitag_size: maximum size of tags formed by multiple unit
                              tags

        @returns: a new L{Rater} object
        '''

        self.weights = weights
        self.multitag_size = multitag_size

    def __call__(self, tags):
        '''
        @param tags: a list of (preferably stemmed) tags

        @returns: a list of unique (multi)tags sorted by relevance
        '''

        self.rate_tags(tags)
        multitags = self.create_multitags(tags)

        # keep most frequent version of each tag
        clusters = collections.defaultdict(Counter)
        proper = collections.defaultdict(int)
        ratings = collections.defaultdict(float)

        for t in multitags:
            clusters[t][t.string] += 1
            if t.proper:
                proper[t] += 1
                ratings[t] = max(ratings[t], t.rating)

        term_count = Counter(multitags)

        for t, cnt in term_count.items():
            t.string = clusters[t].most_common(1)[0][0]
            proper_freq = proper[t] / cnt
            if proper_freq >= 0.5:
                t.proper = True
                t.rating = ratings[t]

        # purge duplicates, one-character tags and stopwords
        unique_tags = set(t for t in term_count
                          if len(t.string) > 1 and t.rating > 0.0)

        # remove redundant tags
        for t, cnt in term_count.items():
            words = t.stem.split()
            for l in range(1, len(words)):
                for i in range(len(words) - l + 1):
                    s = Tag(' '.join(words[i:i + l]))
                    relative_freq = cnt / term_count[s]
                    if ((relative_freq == 1.0 and t.proper) or
                        (relative_freq >= 0.5 and t.rating > 0.0)):
                        unique_tags.discard(s)
                    else:
                        unique_tags.discard(t)

        return sorted(unique_tags)

    def rate_tags(self, tags):
        '''
        @param tags: a list of tags to be assigned a rating
        '''

        term_count = Counter(tags)

        for t in tags:
            # rating of a single tag is term frequency * weight
            t.rating = 1.0 * term_count[t] / len(tags) * self.weights.get(t.stem, 1.0)

    def create_multitags(self, tags):
        '''
        @param tags: a list of tags (respecting the order in the text)

        @returns: a list of multitags
        '''

        multitags = []

        for i in range(len(tags)):
            t = MultiTag(tags[i])
            multitags.append(t)
            for j in range(1, self.multitag_size):
                if t.terminal or i + j >= len(tags):
                    break
                else:
                    t = MultiTag(tags[i + j], t)
                    multitags.append(t)

        return multitags


class Tagger:
    '''
    Master class for tagging text documents

    (this is a simple interface that should allow convenient experimentation
    by using different classes as building blocks)
    '''

    def __init__(self, reader, stemmer, rater):
        '''
        @param reader: a L{Reader} object
        @param stemmer: a L{Stemmer} object
        @param rater: a L{Rater} object

        @returns: a new L{Tagger} object
        '''

        self.reader = reader
        self.stemmer = stemmer
        self.rater = rater

    def __call__(self, text, tags_number=5):
        '''
        @param text:        the string of text to be tagged
        @param tags_number: number of best tags to be returned

        Returns: a list of (hopefully) relevant tags
        '''

        tags = self.reader(text)
        tags = list(map(self.stemmer, tags))
        tags = self.rater(tags)

        return tags[:tags_number]



if __name__ == '__main__':

    import glob
    import pickle
    from optparse import OptionParser

    usage = "usage: %prog [options] file1 file2..."
    parser = OptionParser(usage=usage)

    parser.add_option("", "--dict", dest="dictionary", default="data/dict.pkl",
                      action="store", type="string", metavar="DICT",
                      help="pickled dictionary for weights")
    parser.add_option("", "--multitag_size", dest="multitag_size", default=3,
                      action="store", type="int", metavar="TAG_SIZE",
                      help="max words per tag")
    parser.add_option("", "--tags_number", dest="tags_number", default=5,
                      action="store", type="int", metavar="TAGS_NUMBER",
                      help="number of tags to return per document")
    # parser.add_option("-d", "--debug", dest="debug", default=False,
    #                   action="store_true",
    #                   help="debug mode")

    (options, args) = parser.parse_args()

    if not args:
        print('No arguments given, running tests: ')
        documents = glob.glob('tests/*')
    else:
        documents = args

    with open(options.dictionary, 'rb') as fh:
        weights = pickle.load(fh)

    tagger = Tagger(Reader(), Stemmer(), Rater(weights, multitag_size=options.multitag_size))

    for doc in documents:
        with open(doc, 'r') as file:
            print('Tags for ', doc, ':')
            print(tagger(file.read(), tags_number=options.tags_number))

