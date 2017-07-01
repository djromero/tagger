import nltk
import os

from tagger.extras import build_dict_from_nltk


base_dir = os.path.expanduser("~/dict")

build_dict_from_nltk(os.path.join(base_dir, "en"), nltk.corpus.brown, nltk.corpus.stopwords.words('english'), measure='ICF', verbose=True)
build_dict_from_nltk(os.path.join(base_dir, "es"), nltk.corpus.cess_esp, nltk.corpus.stopwords.words('spanish'), measure='ICF', verbose=True)
