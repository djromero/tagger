#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" A tagger for Spanish texts """

from tagger import Tagger, Rater, Reader, Stemmer


class SpanishTagger(Tagger):

    def __init__(self, dictionary_path=None, reader=None, stemmer=None, rater=None):
        super(SpanishTagger, self).__init__(reader, stemmer, rater)

        if self.reader is None:
            self.reader = Reader()

        if self.stemmer is None:
            self.stemmer = Stemmer()

        if self.rater is None and dictionary_path is not None:
            import pickle
            with open(dictionary_path, 'rb') as fh:
                weights = pickle.load(fh)
            self.rater = Rater(weights, multitag_size=1)


if __name__ == "__main__":
    import os

    base_dir = os.path.expanduser("~/dict")
    dict_path = os.path.join(base_dir, 'es.pkl')
    english_tagger = SpanishTagger(dict_path)
    print(spanish_tagger("10 años del iPhone: 5 cosas que el popular teléfono de Apple cambió en el mundo"))
