#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" A tagger for English texts """

from tagger import Tagger, Rater, Reader, Stemmer


class EnglishTagger(Tagger):

    def __init__(self, dictionary_path=None, reader=None, stemmer=None, rater=None):
        super(EnglishTagger, self).__init__(reader, stemmer, rater)

        if self.reader is None:
            self.reader = Reader()

        if self.stemmer is None:
            self.stemmer = Stemmer()

        if self.rater is None and dictionary_path is not None:
            import pickle
            weights = pickle.load(open(dictionary_path, 'rb'))
            self.rater = Rater(weights, multitag_size=1)


if __name__ == "__main__":
    import settings
    import os
    dict_path = os.path.join(settings.env.project, 'attic', 'tagger', 'data/dict.pkl')
    english_tagger = EnglishTagger(dict_path)
    print(english_tagger("Beats X review: Apple's neckbuds for the everyday"))
