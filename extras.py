from .tagger import *


class UnicodeReader(Reader):
    '''
    Reader subclass that converts Unicode strings to a close ASCII
    representation
    '''

    def __call__(self, text):
        import unicodedata

        text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore')
        return Reader.__call__(self, text)


class HTMLReader(UnicodeReader):
    '''
    Reader subclass that can parse HTML code from the input
    '''

    def __call__(self, html):
        import lxml.html

        text = lxml.html.fromstring(html).text_content()
        if isinstance(text, str):
            return UnicodeReader.__call__(self, text)
        else:
            return Reader.__call__(self, text)


class SimpleReader(Reader):
    '''
    Reader subclass that doesn't perform any advanced analysis of the text
    '''

    def __call__(self, text):
        text = text.lower()
        text = self.preprocess(text)
        words = self.match_words.findall(text)
        tags = [Tag(w) for w in words]
        return tags


class FastStemmer(Stemmer):
    '''
    Stemmer subclass that uses a much faster, but less correct algorithm
    '''

    def __init__(self):
        from stemming import porter

        Stemmer.__init__(self, porter)


class NaiveRater(Rater):
    '''
    Rater subclass that jusk ranks single-word tags by their frequency and
    weight
    '''

    def __call__(self, tags):
        self.rate_tags(tags)
        # we still get rid of one-character tags and stopwords
        unique_tags = set(t for t in tags
                          if len(t.string) > 1 and t.rating > 0.0)
        return sorted(unique_tags)


def build_dict_from_nltk(output_file, corpus=None, stopwords=None,
                         stemmer=Stemmer(), measure='IDF', verbose=False):
    '''
    @param output_file: the name of the file where the dictionary should be
                        saved
    @param corpus:      the NLTK corpus to use (defaults to nltk.corpus.reuters)
    @param stopwords:   a list of (not stemmed) stopwords (defaults to
                        nltk.corpus.reuters.words('stopwords'))
    @param stemmer:     the L{Stemmer} object to be used
    @param measure:     the measure used to compute the weights ('IDF'
                        i.e. 'inverse document frequency' or 'ICF' i.e.
                        'inverse collection frequency'; defaults to 'IDF')
    @param verbose:     whether information on the progress should be printed
                        on screen
    '''

    from .build_dict import build_dict
    import nltk
    import pickle

    if not (corpus and stopwords):
        nltk.download('reuters')

    corpus = corpus or nltk.corpus.reuters
    stopwords = stopwords or nltk.corpus.reuters.words('stopwords')

    corpus_list = []

    if verbose: print('Processing corpus...')
    for file in corpus.fileids():
        doc = [stemmer(Tag(w.lower())).stem for w in corpus.words(file)
               if w[0].isalpha()]
        corpus_list.append(doc)

    if verbose: print('Processing stopwords...')
    stopwords = [stemmer(Tag(w.lower())).stem for w in stopwords]

    if verbose: print('Building dictionary... ')
    dictionary = build_dict(corpus_list, stopwords, measure)
    with open(output_file, 'wb') as out:
        pickle.dump(dictionary, out, -1, protocol=2)

