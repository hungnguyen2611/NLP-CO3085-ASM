import re

from .relations import *
from .semantics import *


class Relation(object):
    def __init__(self, relation_type, l, r, action):
        self.relation_type = relation_type
        self.l = l
        self.r = r
        self.action = action

    def __str__(self):
        return f"{self.relation_type}({self.l}, {self.r})"


class DependencyParser(object):
    ROOTS = ['<root>']
    NOUNS = ['máy_bay', 'thành_phố', 'tp', 'tp.', 'mã_hiệu', 'hãng_hàng_không']
    NAMES = ['huế', 'đà_nẵng', 'hà_nội', 'hồ_chí_minh', 'tp.hồ_chí_minh', 'tp._hồ_chí_minh',
             'khánh_hòa', 'hải_phòng', 'vietjetair']
    NAMES_MAPPER = {
        'huế': 'HUE',
        'đà_nẵng': 'ĐN',
        'hà_nội': 'HN',
        'hồ_chí_minh': 'HCMC',
        'tp.hồ_chí_minh': 'HCMC',
        'tp._hồ_chí_minh': 'HCMC',
        'khánh_hòa': 'KH',
        'hải_phòng': 'HP',
        'vietjetair': 'VJ'
    }
    VERBS = ['đến', 'bay', 'hạ_cánh', 'xuất_phát']
    WH_WORDS = ['nào', 'mấy_giờ', 'cho_biết']

    # special cases
    FROM = ['từ']
    TO = ['đến']
    AT = ['lúc']
    IN = ['ở']
    QUERY = ['?']

    # relation rules
    RELATION_RULES = [
        (('NOUNS', 'WH_WORDS'), 'WH_det', 'RA'),
        (('WH_WORDS', 'NOUNS'), 'WH_det', 'LA'),
        (('VERBS', 'WH_WORDS'), 'query_time', 'RA'),
        (('NOUNS', 'VERBS'), 'nsubj', 'LA'),
        (('NOUNS', 'NOUNS'), 'nmod', 'RA'),
        (('ROOTS', 'VERBS'), 'root', 'RA'),
        (('TO', 'NAMES'), 'to_loc', 'LA'),
        (('TO', 'NOUNS'), 'to_loc', 'LA'),
        (('FROM', 'NAMES'), 'from_loc', 'LA'),
        (('FROM', 'NOUNS'), 'from_loc', 'LA'),
        (('NOUNS', 'NAMES'), 'name', 'RA'),
        (('VERBS', 'NAMES'), 'name_loc', 'RA'),
        (('VERBS', 'AT'), 'at_time', 'RA'),
        (('VERBS', 'TIME_DURATION_PATTERNS'), 'run_time', 'RA'),
        (('AT', 'TIMES_PATTERNS'), 'time', 'RA'),
        (('AT', 'WH_WORDS'), 'time', 'LA'),
        (('IN', 'NAMES'), 'in_loc', 'LA'),
        (('VERBS', 'QUERY'), 'query', 'RA'),
        (('NOUNS', 'AIRLINE_PATTERNS'), 'nmod', 'RA')
    ]

    TIMES_PATTERNS = re.compile(r"^([0-9]|1[0-9]|2[0-3]):[0-5][0-9]hr$")
    TIME_DURATION_PATTERNS = re.compile(r"[0-9]_giờ$")
    AIRLINE_PATTERNS = re.compile(r"v[a-z][1-9]")

    MAPPER = {
        'máy_bay': 'FLIGHT',
        'đến': 'DEST',
        'mã_hiệu': 'FLIGHT',
        'thành_phố': 'DEST'
    }

    def _pos_tagging(self, tokens):
        tags = []
        for idx, token in enumerate(tokens):
            token_lower = token.lower()
            if token_lower in self.VERBS:
                if token_lower in self.TO:
                    if 'FROM' in tags or tags[-1] == 'VERBS':
                        tags.append('TO')
                    else:
                        tags.append('VERBS')
                else:
                    tags.append('VERBS')
            elif token_lower in self.NOUNS:
                tags.append('NOUNS')
            elif token_lower in self.NAMES:
                tags.append('NAMES')
            elif token_lower in self.WH_WORDS:
                tags.append('WH_WORDS')
            elif token_lower in self.FROM:
                tags.append('FROM')
            elif token_lower in self.AT:
                tags.append('AT')
            elif token_lower in self.QUERY:
                tags.append('QUERY')
            elif token_lower in self.IN:
                tags.append('IN')
            elif self.TIMES_PATTERNS.match(token_lower):
                tags.append('TIMES_PATTERNS')
            elif self.TIME_DURATION_PATTERNS.match(token_lower):
                tags.append('TIME_DURATION_PATTERNS')
            elif self.AIRLINE_PATTERNS.match(token_lower):
                tags.append('AIRLINE_PATTERNS')
            else:
                tags.append('OTHER')
        return tags

    def parse(self, tokens):
        tags = self._pos_tagging(tokens)
        stack = [('<ROOT>', 'ROOTS')]
        buffer = list(zip(tokens, tags))
        relations = []
        stack.append(buffer.pop(0))
        while buffer:
            top_stack = stack[-1]
            head_buffer = buffer[0]

            relation = self.check_relation(top_stack, head_buffer)
            if relation:
                relations.append(relation)
                if relation.relation_type == 'nmod':
                    stack.append(buffer.pop(0))
                    stack.pop()
                    continue
                if relation.action == 'RA':
                    stack.append(buffer.pop(0))
                elif relation.action == 'LA':
                    stack.pop()
            else:
                # SHIFT and REDUCE case
                if (top_stack[1] not in ['NOUNS', 'VERBS'] and head_buffer[1] == 'VERBS') or \
                        (top_stack[1] in ['NOUNS', 'NAMES'] and head_buffer[1] != 'VERBS') or \
                        (top_stack[1] not in ['VERBS', 'ROOTS']):
                    stack.pop()
                else:
                    stack.append(buffer.pop(0))
        return relations

    def check_relation(self, token_a, token_b):
        token_text_a, token_type_a = token_a
        token_text_b, token_type_b = token_b

        if token_type_a == 'VERBS' and token_text_a == 'đến':
            return Relation('to_loc', token_text_a, token_text_b, 'LA')

        for (a_cond, b_cond), rel_type, action in self.RELATION_RULES:
            a_match = token_type_a == a_cond
            b_match = token_type_b == b_cond

            if a_match and b_match:
                if rel_type == 'nsubj' or token_type_a in ['TO', 'FROM', 'IN'] or \
                        (rel_type == 'WH_det' and token_type_a == 'WH_WORDS'):
                    return Relation(rel_type, token_text_b, token_text_a, action)
                else:
                    return Relation(rel_type, token_text_a, token_text_b, action)

        # REDUCE and SHIFT case
        return None

    def postprocess_grammar(self, grammars):
        to_loc_noun_idx = name_idx = to_loc_name_idx = name_loc_idx = from_loc_idx = in_loc_idx = from_loc_noun_idx = flight_noun_idx = -1
        for idx, grammar in enumerate(grammars):
            if grammar.type == 'TO_LOC' and isinstance(grammar.token, NOUN):
                to_loc_noun_idx = idx
            elif grammar.type == 'FROM_LOC' and isinstance(grammar.token, NOUN):
                from_loc_noun_idx = idx
            elif grammar.type == 'NAME':
                name_idx = idx
            elif grammar.type == 'NAME_LOC':
                name_loc_idx = idx
            elif grammar.type == 'FROM_LOC':
                from_loc_idx = idx
            elif grammar.type == 'IN_LOC':
                in_loc_idx = idx
            elif grammar.type == 'TO_LOC' and isinstance(grammar.token, NAME):
                to_loc_name_idx = idx
            elif grammar.type == 'FLIGHT' and isinstance(grammar.token, NOUN):
                flight_noun_idx = idx

        if flight_noun_idx != -1 and name_idx != -1:
            grammars.append(GrammaticalRelation('FLIGHT', NAME(grammars[name_idx].org_token)))
            grammars[flight_noun_idx] = None
            grammars[name_idx] = None
            grammars = [grammar for grammar in grammars if grammar is not None]
            return grammars

        if from_loc_noun_idx != -1 and name_idx != -1:
            grammars.append(GrammaticalRelation('FROM_LOC', NAME(grammars[name_idx].org_token)))
            grammars[from_loc_noun_idx] = None
            grammars[name_idx] = None
            grammars = [grammar for grammar in grammars if grammar is not None]
            return grammars

        if to_loc_noun_idx != -1 and name_idx != -1:
            grammars.append(GrammaticalRelation('TO_LOC', NAME(grammars[name_idx].org_token)))
            grammars[to_loc_noun_idx] = None
            grammars[name_idx] = None
            grammars = [grammar for grammar in grammars if grammar is not None]
            return grammars

        if name_loc_idx != -1:
            if from_loc_idx != -1:
                grammars.append(
                    GrammaticalRelation('SOURCE', NAME(grammars[from_loc_idx].token.org_token)))
                grammars[from_loc_idx] = None

            if to_loc_name_idx != -1:
                grammars.append(
                    GrammaticalRelation('DEST', NAME(grammars[to_loc_name_idx].token.org_token)))
                grammars[to_loc_name_idx] = None

            if in_loc_idx != -1:
                grammars.append(
                    GrammaticalRelation('DEST', NAME(grammars[in_loc_idx].token.org_token)))
                grammars[in_loc_idx] = None

            grammars[name_loc_idx] = None

        grammars = [grammar for grammar in grammars if grammar is not None]
        return grammars

    @staticmethod
    def yes_no_case(grammars):
        for grammar in grammars:
            if 'WH' in grammar.type:
                return False
        return True

    def construct_grammar(self, relations):
        grammars = []
        for relation in relations:
            if relation.relation_type == 'WH_det':
                type = 'WH_{} ?'.format(self.MAPPER[relation.l.lower()])
                alias = self.MAPPER[relation.l.lower()][0].lower() + '1'
                grammars.append(GrammaticalRelation(type, alias))
            elif relation.relation_type == 'nsubj':
                if self.MAPPER.get(relation.l.lower()) is None:
                    continue
                type = '{}_{} ?'.format(self.MAPPER[relation.l.lower()],
                                        self.MAPPER[relation.r.lower()])
                alias = self.MAPPER[relation.r.lower()][0].lower() + '1'
                grammars.append(GrammaticalRelation(type, alias))
            elif relation.relation_type == 'nmod':
                type = self.MAPPER[relation.l.lower()]
                grammars.append(GrammaticalRelation(type, NAME(
                    relation.r) if relation.r.lower() in self.NAMES or self.AIRLINE_PATTERNS.match(
                    relation.r.lower()) else NOUN(relation.r)))
            elif relation.relation_type == 'name_loc':
                grammars.append(GrammaticalRelation('NAME_LOC', NAME(relation.r)))
            elif relation.relation_type == 'to_loc':
                if relation.r.lower() == 'đến':
                    if relation.l.lower() in self.NAMES:
                        grammars.append(GrammaticalRelation('TO_LOC', NAME(relation.l)))
                    else:
                        grammars.append(GrammaticalRelation('TO_LOC', NOUN(relation.l)))
                else:
                    if relation.r.lower() in self.NAMES:
                        grammars.append(GrammaticalRelation('TO_LOC', NAME(relation.r)))
                    else:
                        grammars.append(GrammaticalRelation('TO_LOC', NOUN(relation.r)))
            elif relation.relation_type == 'in_loc':
                grammars.append(GrammaticalRelation('IN_LOC', NAME(relation.l)))
            elif relation.relation_type == 'from_loc':
                if relation.l.lower() in self.NAMES:
                    grammars.append(GrammaticalRelation('FROM_LOC', NAME(relation.l)))
                else:
                    grammars.append(GrammaticalRelation('FROM_LOC', NOUN(relation.l)))
            elif relation.relation_type == 'name':
                grammars.append(NAME(relation.r))
            elif relation.relation_type == 'time':
                if relation.r not in self.WH_WORDS:
                    grammars.append(GrammaticalRelation('AT_TIME', NAME(relation.r)))
                else:
                    grammars.append(GrammaticalRelation('WH_TIME ?', 't1'))
            elif relation.relation_type == 'run_time':
                grammars.append(GrammaticalRelation('RUN_TIME', NAME(relation.r)))
            elif relation.relation_type == 'query_time':
                if 'WH_TIME ?' in [grammar.type for grammar in grammars]:
                    continue
                type = 'WH_TIME_COUNT ?'
                alias = 't1'
                grammars.append(GrammaticalRelation(type, alias))
        grammar_len = len(grammars)
        while grammar_len > 0:
            grammars = self.postprocess_grammar(grammars)
            if len(grammars) == grammar_len:
                break
            grammar_len = len(grammars)
        if self.yes_no_case(grammars):
            grammars.append(GrammaticalRelation('YES_NO', 'NONE'))
        return grammars

    def construct_logical_form(self, grammars):
        YES_NO_phrases = []
        WH_phrases = []
        FLIGHT_phrases = []
        DEST_phrases = []
        TIME_phrases = []
        SOURCE_DEST_phrases = []

        for grammar in grammars:
            if grammar.type.startswith('WH_'):
                WH_phrases.append(grammar)
            elif grammar.type.startswith('DEST_'):
                DEST_phrases.append(grammar)
            elif grammar.type.startswith('TO_LOC'):
                if DEST_phrases:
                    DEST_phrases.append(grammar)
            elif grammar.type.startswith('AT_TIME'):
                TIME_phrases.append(grammar)
            elif grammar.type.startswith('RUN_TIME'):
                TIME_phrases.append(grammar)
            elif grammar.type.startswith('SOURCE') or grammar.type.startswith('DEST'):
                SOURCE_DEST_phrases.append(grammar)
            elif grammar.type.startswith('YES_NO'):
                YES_NO_phrases.append(grammar)
            elif grammar.type == 'FLIGHT' and grammar.token.type == 'NAME':
                FLIGHT_phrases.append(grammar)

        if DEST_phrases:
            DEST_phrases = [GrammaticalRelation(DEST_phrases[0], DEST_phrases[1])]
        if SOURCE_DEST_phrases and len(SOURCE_DEST_phrases) == 2:
            SOURCE_DEST_phrases = [
                OpRelation([*FLIGHT_phrases, SOURCE_DEST_phrases[0], SOURCE_DEST_phrases[1]],
                           '&')]
            FLIGHT_phrases = []
        elif SOURCE_DEST_phrases and len(SOURCE_DEST_phrases) == 1:
            SOURCE_DEST_phrases = [
                OpRelation([*FLIGHT_phrases, SOURCE_DEST_phrases[0]], '&')]
            FLIGHT_phrases = []

        for idx, wh in enumerate(WH_phrases):
            if wh.type.startswith('WH_TIME ?'):
                if DEST_phrases:
                    WH_phrases[idx] = GrammaticalRelation('WH_DTIME ?', 't1')
                elif SOURCE_DEST_phrases and len(SOURCE_DEST_phrases) == 1:
                    WH_phrases[idx] = GrammaticalRelation(
                        'WH_ATIME ?' if SOURCE_DEST_phrases[0].type == 'SOURCE' else 'WH_DTIME',
                        't1')
                else:
                    WH_phrases[idx] = GrammaticalRelation('WH_TIME ?', 't1')
        if YES_NO_phrases:
            YES_NO_phrases = [GrammaticalRelation('YES NO ?', None)]
        # logical_forms = [*WH_phrases, *YES_NO_phrases, *DEST_phrases, *SOURCE_DEST_phrases,
        #                  *FLIGHT_phrases,
        #                  *TIME_phrases]
        logical_forms = {
            'WH': WH_phrases,
            'YES_NO': YES_NO_phrases,
            'DEST': DEST_phrases,
            'SOURCE_DEST': SOURCE_DEST_phrases,
            'FLIGHT': FLIGHT_phrases,
            'TIME': TIME_phrases
        }

        return logical_forms

    def construct_procedural_semantic(self, logical_forms):
        procedural_semantics = []
        objective = None
        p_sem_obj = None
        phrs = [phrase.type for phrase in logical_forms.get('WH', [])]

        if 'WH_FLIGHT ?' in phrs and ('WH_ATIME' in phrs or 'WH_DTIME' in phrs):
            procedural_semantics.append(ProceduralSemantic('PRINT-ALL', '?f1 ?t1'))
            objective = '?f1'
            p_sem_obj = ProceduralSemantic('FLIGHT', objective)
        elif 'WH_FLIGHT ?' in phrs:
            procedural_semantics.append(ProceduralSemantic('PRINT-ALL', '?f1'))
            objective = '?f1'
            p_sem_obj = ProceduralSemantic('FLIGHT', objective)
        elif 'WH_DTIME' in phrs or 'WH_ATIME' in phrs:
            procedural_semantics.append(ProceduralSemantic('PRINT-ALL', '?t1'))
            objective = '?t1'
        elif 'WH_TIME_COUNT ?' in phrs:
            procedural_semantics.append(ProceduralSemantic('PRINT-ALL', '?t1'))
            objective = '?t1'
        elif 'WH_DEST ?' in phrs:
            procedural_semantics.append(ProceduralSemantic('PRINT-ALL', '?d1'))
            objective = '?d1'
            procedural_semantics.append(ProceduralSemantic(type='ATIME', object=objective,
                                                           flight=self.NAMES_MAPPER[
                                                               logical_forms.get('FLIGHT')[
                                                                   0].token.org_token.lower()],
                                                           start_place=None,
                                                           end_place=None,
                                                           time=None))

        if logical_forms.get('YES_NO'):
            procedural_semantics.append(ProceduralSemantic('PRINT-YES-NO'))

        if logical_forms.get('DEST'):
            if logical_forms.get('TIME'):
                p_sem2 = ProceduralSemantic(type='ATIME', object=objective,
                                            end_place=self.NAMES_MAPPER[
                                                logical_forms.get('DEST')[
                                                    0].token.token.org_token.lower()],
                                            time=logical_forms.get('TIME')[
                                                0].token.org_token.lower())
                procedural_semantics.append(OpProceduralSemantic([p_sem_obj, p_sem2], '&'))

        if logical_forms.get('SOURCE_DEST'):
            time_token = None if not logical_forms.get('TIME') else logical_forms.get('TIME')[
                0].token.org_token.lower()
            if 'FLIGHT' in [rel.type for rel in logical_forms.get('SOURCE_DEST')[0].relations]:
                flight_token = self.NAMES_MAPPER.get(
                    logical_forms.get('SOURCE_DEST')[0].relations[0].token.org_token.lower(),
                    logical_forms.get('SOURCE_DEST')[0].relations[0].token.org_token)

                if len(logical_forms.get('SOURCE_DEST')[0].relations) == 3:
                    p_sem2 = ProceduralSemantic(type='RUNTIME',
                                                object=objective,
                                                flight=flight_token,
                                                start_place=self.NAMES_MAPPER[
                                                    logical_forms.get('SOURCE_DEST')[
                                                        0].relations[1].token.org_token.lower()],
                                                end_place=self.NAMES_MAPPER[
                                                    logical_forms.get('SOURCE_DEST')[
                                                        0].relations[2].token.org_token.lower()],
                                                time=time_token
                                                )
                elif logical_forms.get('SOURCE_DEST')[0].relations[1].type == 'SOURCE':
                    p_sem2 = ProceduralSemantic(type='DTIME',
                                                object=objective,
                                                flight=flight_token,
                                                start_place=self.NAMES_MAPPER[
                                                    logical_forms.get('SOURCE_DEST')[
                                                        0].relations[1].token.org_token.lower()],
                                                end_place=None,
                                                time=time_token)
                else:
                    p_sem2 = ProceduralSemantic(type='ATIME', object=objective,
                                                flight=flight_token,
                                                start_place=None,
                                                end_place=
                                                self.NAMES_MAPPER[
                                                    logical_forms.get('SOURCE_DEST')[0].relations[
                                                        1].token.org_token.lower()],
                                                time=time_token)
            else:
                if len(logical_forms.get('SOURCE_DEST')[0].relations) == 2:
                    p_sem2 = ProceduralSemantic(type='RUNTIME', object=objective,
                                                # flight=flight_token,
                                                start_place=self.NAMES_MAPPER[
                                                    logical_forms.get('SOURCE_DEST')[
                                                        0].relations[0].token.org_token.lower()],
                                                end_place=self.NAMES_MAPPER[
                                                    logical_forms.get('SOURCE_DEST')[
                                                        0].relations[1].token.org_token.lower()],
                                                time=time_token)
                elif logical_forms.get('SOURCE_DEST')[0].relations[0].type == 'SOURCE':
                    p_sem2 = ProceduralSemantic(type='DTIME', object=objective,
                                                # flight=flight_token,
                                                start_place=self.NAMES_MAPPER[
                                                    logical_forms.get('SOURCE_DEST')[
                                                        0].relations[0].token.org_token.lower()],
                                                end_place=None,
                                                time=time_token)
                else:
                    p_sem2 = ProceduralSemantic(type='ATIME', object=objective,
                                                # flight=flight_token,
                                                start_place=None,
                                                end_place=self.NAMES_MAPPER[
                                                    logical_forms.get('SOURCE_DEST')[
                                                        0].relations[0].token.org_token.lower()],
                                                time=time_token)
            if p_sem_obj:
                procedural_semantics.append(OpProceduralSemantic([p_sem_obj, p_sem2], '&'))
            else:
                procedural_semantics.append(p_sem2)

        return procedural_semantics
