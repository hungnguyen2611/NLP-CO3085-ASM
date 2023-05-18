class GrammaticalRelation(object):
    def __init__(self, type, token):
        self.type = type
        self.token = token

    def __str__(self):
        return '{}({})'.format(self.type, self.token.__str__())


class NAME(GrammaticalRelation):
    def __init__(self, token):
        super(NAME, self).__init__('NAME', token)
        self.idx = 1
        self.org_token = token
        self.alias = '{}{} "{}"'.format(token.__str__()[0].lower(), self.idx, self.token)
        self.token = self.alias


class NOUN(GrammaticalRelation):
    def __init__(self, token):
        super(NOUN, self).__init__('NOUN', token)
        self.idx = 1
        self.org_token = token
        self.alias = '{}{} "{}"'.format(token.__str__()[0].lower(), self.idx, self.token)
        self.token = self.alias


class OpRelation(GrammaticalRelation):
    def __init__(self, relations, op):
        super(OpRelation, self).__init__(op, relations)
        self.relations = relations

    def __str__(self):
        return self.type + ''.join([f"({relation.__str__()})" for relation in self.relations])