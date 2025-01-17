"""
Lab 4
Language generation algorithm based on language profiles
"""

from typing import Tuple
from lab_4.storage import Storage
from lab_4.language_profile import LanguageProfile


# 4
def tokenize_by_letters(text: str) -> Tuple or int:
    """
    Tokenizes given sequence by letters
    """
    if not isinstance(text, str):
        return -1
    text = "".join(letter for letter in text if letter.isalpha() or letter.isspace())
    text_tuple = tuple(tuple("_"+word+"_") for word in text.lower().strip().split())
    return text_tuple


# 4
class LetterStorage(Storage):
    """
    Stores letters and their ids
    """

    def update(self, elements: tuple) -> int:
        """
        Fills a storage by letters from the tuple
        :param elements: a tuple of tuples of letters
        :return: 0 if succeeds, -1 if not
        """
        if not isinstance(elements, tuple):
            return -1
        for word in elements:
            for letter in word:
                self._put(letter)
        return 0

    def get_letter_count(self) -> int:
        """
        Gets the number of letters in the storage
        """
        if not self.storage:
            return -1
        return len(self.storage)


# 4
def encode_corpus(storage: LetterStorage, corpus: tuple) -> tuple:
    """
    Encodes corpus by replacing letters with their ids
    :param storage: an instance of the LetterStorage class
    :param corpus: a tuple of tuples
    :return: a tuple of the encoded letters
    """
    if not (isinstance(storage, LetterStorage) and isinstance(corpus, tuple)):
        return ()
    storage.update(corpus)
    encoded_sentences = tuple(tuple(storage.get_id(letter)
                                    for letter in word)
                              for word in corpus)
    return encoded_sentences


# 4
def decode_sentence(storage: LetterStorage, sentence: tuple) -> tuple:
    """
    Decodes sentence by replacing letters with their ids
    :param storage: an instance of the LetterStorage class
    :param sentence: a tuple of tuples-encoded words
    :return: a tuple of the decoded sentence
    """
    if not (isinstance(storage, LetterStorage) and isinstance(sentence, tuple)):
        return ()
    decoded_sentences = tuple(tuple(storage.get_element(letter)
                                    for letter in word)
                              for word in sentence)
    return decoded_sentences


# 6
class NGramTextGenerator:
    """
    Language model for basic text generation
    """

    def __init__(self, language_profile: LanguageProfile):
        self.profile = language_profile
        self._used_n_grams = []

    def _generate_letter(self, context: tuple) -> int:
        """
        Generates the next letter.
            Takes the letter from the most
            frequent ngram corresponding to the context given.
        """
        if not isinstance(context, tuple):
            return -1
        if len(context) + 1 not in [trie.size for trie in self.profile.tries]:
            return -1

        letters = {}
        generated_letter = ()
        for trie in self.profile.tries:
            if trie.size == len(context) + 1:
                for key, value in trie.n_gram_frequencies.items():
                    if self._used_n_grams == list(trie.n_gram_frequencies.keys()):
                        self._used_n_grams = []
                    if key[:len(context)] == context and key not in self._used_n_grams:
                        letters[key] = value
                if letters:
                    generated_letter = max(letters.keys(), key=letters.get)
                    self._used_n_grams.append(generated_letter)
                else:
                    generated_letter = max(trie.n_gram_frequencies.keys(),
                                           key=trie.n_gram_frequencies.get)
        return generated_letter[-1]

    def _generate_word(self, context: tuple, word_max_length=15) -> tuple:
        """
        Generates full word for the context given.
        """
        if not isinstance(context, tuple) or not isinstance(word_max_length, int):
            return ()
        generated_word = list(context)
        if word_max_length == 1:
            generated_word.append(self.profile.storage.get_special_token_id())
            return tuple(generated_word)
        while generated_word != word_max_length:
            letter = self._generate_letter(context)
            generated_word.append(letter)
            if letter == self.profile.storage.get_special_token_id():
                break
            context = tuple(generated_word[-len(context):])
        return tuple(generated_word)

    def generate_sentence(self, context: tuple, word_limit: int) -> tuple:
        """
        Generates full sentence with fixed number of words given.
        """
        if not isinstance(context, tuple) or not isinstance(word_limit, int):
            return ()

        generated_sentence = []

        while len(generated_sentence) != word_limit:
            word = self._generate_word(context)
            generated_sentence.append(word)
            context = tuple(word[-1:])

        return tuple(generated_sentence)

    def generate_decoded_sentence(self, context: tuple, word_limit: int) -> str:
        """
        Generates full sentence and decodes it
        """
        if not isinstance(context, tuple) or not isinstance(word_limit, int):
            return ''
        generated_sentence = self.generate_sentence(context, word_limit)
        decoded_sentence = ''
        for word in generated_sentence:
            for letter_id in word:
                letter = self.profile.storage.get_element(letter_id)
                decoded_sentence += letter
        result = decoded_sentence.replace('__', ' ').replace('_', '').capitalize() + '.'
        return result


# 6
def translate_sentence_to_plain_text(decoded_corpus: tuple) -> str:
    """
    Converts decoded sentence into the string sequence
    """
    if not isinstance(decoded_corpus, tuple) or not decoded_corpus:
        return ''
    decoded_sentence = ''
    for element in decoded_corpus:
        for symbol in element:
            decoded_sentence += symbol
    result = decoded_sentence.replace('__', ' ').replace('_', '').capitalize() + '.'
    return result


# 8
class LikelihoodBasedTextGenerator(NGramTextGenerator):
    """
    Language model for likelihood based text generation
    """

    def _calculate_maximum_likelihood(self, letter: int, context: tuple) -> float:
        """
        Calculates maximum likelihood for a given letter
        :param letter: a letter given
        :param context: a context for the letter given
        :return: float number, that indicates maximum likelihood
        """
        if not (isinstance(letter, int) and isinstance(context, tuple) and context):
            return -1

        l_freq = 0
        s_freq = 0

        for trie in self.profile.tries:
            if trie.size == len(context) + 1:
                for n_gram, frequency in trie.n_gram_frequencies.items():
                    if n_gram[:len(context)] == context and n_gram[-1] == letter:
                        l_freq += frequency
                    if n_gram[:len(context)] == context:
                        s_freq += frequency
            if s_freq == 0:
                return 0.0

        return l_freq / s_freq

    def _generate_letter(self, context: tuple) -> int:
        """
        Generates the next letter.
            Takes the letter with highest
            maximum likelihood frequency.
        """
        if not isinstance(context, tuple) or not context:
            return -1
        l_probability = {}
        for instance in self.profile.tries:
            if instance.size - 1 == len(context):
                for key in instance.n_gram_frequencies:
                    if key[:len(context)] == context:
                        l_probability[key] = self._calculate_maximum_likelihood(key[-1], context)
        if not l_probability:
            for instance in self.profile.tries:
                if instance.size == 1:
                    return max(instance.n_gram_frequencies, key=instance.n_gram_frequencies.get)[0]
        return max(l_probability.keys(), key=l_probability.get)[-1]


# 10
class BackOffGenerator(NGramTextGenerator):
    """
    Language model for back-off based text generation
    """

    def _generate_letter(self, context: tuple) -> int:
        """
        Generates the next letter.
            Takes the letter with highest
            available frequency for the corresponding context.
            if no context can be found, reduces the context size by 1.
        """
        pass


# 10
class PublicLanguageProfile(LanguageProfile):
    """
    Language Profile to work with public language profiles
    """

    def open(self, file_name: str) -> int:
        """
        Opens public profile and adapts it.
        :return: o if succeeds, 1 otherwise
        """
        pass
