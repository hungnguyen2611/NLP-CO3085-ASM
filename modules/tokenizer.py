from underthesea import word_tokenize


class Tokenizer(object):
    def __init__(self):
        self.tokenizer = word_tokenize

    def tokenize_raw(self, sentence):
        removed_tokens = ['Thời gian', 'các', 'những', 'Hãy', 'mất', 'có', 'Có', 'của']
        for token in removed_tokens:
            sentence = sentence.replace(token, '')
        sentence = sentence.replace('VietJet Air', 'VietJetAir')
        doc = self.tokenizer(sentence)
        tokens = [token.replace(' ', '_') for token in doc]
        if tokens[-2] == 'không':
            tokens.pop(-2)
        return tokens

    @staticmethod
    def _token_combine(tokens, token_a, token_b):
        for idx, token in enumerate(tokens):
            if token.lower() == token_a and idx + 1 < len(tokens) and \
                    tokens[idx + 1].lower() == token_b:
                tokens[idx] = '{}_{}'.format(token_a, token_b)
                tokens.pop(idx + 1)
        return tokens

    def tokenize(self, sentence):
        tokenized_text = self.tokenize_raw(sentence)
        # handle case [..., 'cho', 'biết', ...] -> [..., 'cho_biết', ...]
        tokenized_text = self._token_combine(tokenized_text, 'cho', 'biết')
        # handle case [..., 'mấy', 'giờ', ...] -> [..., 'mấy_giờ', ...]
        tokenized_text = self._token_combine(tokenized_text, 'mấy', 'giờ')
        # handle case [..., '1', 'giờ', ...] -> [..., '1_giờ', ...]
        tokenized_text = self._token_combine(tokenized_text, '1', 'giờ')
        # handle case [..., 'hãng', 'hàng_không', ...] -> [..., 'hãng_hàng_không', ...]
        tokenized_text = self._token_combine(tokenized_text, 'hãng', 'hàng_không')
        if ':' in tokenized_text:
            # handle case: '13:30HR'
            # replace token_a, ':', token_b by 'token_a:token_b'
            idx = tokenized_text.index(':')
            tokenized_text[idx - 1] = tokenized_text[idx - 1] + ':' + tokenized_text[idx + 1]
            tokenized_text.pop(idx)
            tokenized_text.pop(idx)
        return tokenized_text
