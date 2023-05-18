import os

import pandas as pd

from modules.parser import DependencyParser
from modules.semantics import OpProceduralSemantic
from modules.tokenizer import Tokenizer


class QuestionAnswering(object):

    def __init__(self, database_path):
        self.tokenizer = Tokenizer()
        self.parser = DependencyParser()
        self.database = pd.read_csv(database_path)
        self.database['ATIME'] = self.database['ATIME'].astype(str)
        self.database['DTIME'] = self.database['DTIME'].astype(str)
        self.database['RUNTIME'] = self.database['RUNTIME'].astype(str)

    def decode_result(self, result, command):
        if command[0].startswith('PRINT-YES-NO'):
            if result.empty:
                return 'Không'
            else:
                return 'Có'
        if result.empty:
            return 'Dạ thưa, không tìm thấy kết quả phù hợp'
        prompt = 'Dạ thưa, kết quả câu hỏi là:'
        if command[0].startswith('PRINT-ALL'):
            if command[1] == '?f1':
                template = "{prompt} máy bay {flight}"
                flights = result['FLIGHT'].tolist()
                flight = ','.join(flights)
                return template.format(prompt=prompt, flight=flight)
            elif command[1] == '?t1':
                template = "{prompt} {time}"
                if command[2] == 'ATIME':
                    times = result['ATIME'].tolist()
                elif command[2] == 'DTIME':
                    times = result['DTIME'].tolist()
                else:
                    times = result['RUNTIME'].tolist()
                time = ','.join(times)
                return template.format(prompt=prompt, time=time)
            elif command[1] == '?f1 ?t1':
                template = "máy bay {flight}, thời gian {time}\n"
                for idx, row in result.iterrows():
                    flight = row['FLIGHT']
                    if command[2] == 'ATIME':
                        time = row['ATIME']
                    elif command[2] == 'DTIME':
                        time = row['DTIME']
                    else:
                        time = row['RUNTIME']
                    prompt += template.format(flight=flight, time=time)
                return prompt
            elif command[1] == '?d1':
                template = "thành phố {place}\n"
                for idx, row in result.iterrows():
                    if command[2] == 'ATIME':
                        place = row['DEST']
                    elif command[2] == 'DTIME':
                        place = row['SOURCE']
                    prompt += template.format(place=place)
                return prompt

    def query_database(self, procedural_semantics):
        query_procedure = procedural_semantics[0]
        always_true_condition = self.database['FLIGHT'] == self.database['FLIGHT']
        if isinstance(procedural_semantics[1], OpProceduralSemantic):
            condition = procedural_semantics[1].p_sems[1]
        else:
            condition = procedural_semantics[1]
        if 'hr' in condition.time.lower():
            condition.time = condition.time.lower().replace('hr', '')
        if condition.flight == 'VJ':
            self.database_query = self.database[
                self.database['FLIGHT'].str.contains(condition.flight)]
        else:
            self.database_query = self.database
        query_result = self.database_query[
            (self.database_query[
                 'FLIGHT'] == condition.flight if condition.flight and condition.flight != 'VJ' else always_true_condition) &
            (self.database_query[
                 'ATIME'] == condition.time if condition.time != '?t1' and condition.type == 'ATIME' else always_true_condition) &
            (self.database_query[
                 'DTIME'] == condition.time if condition.time != '?t1' and condition.type == 'DTIME' else always_true_condition) &
            (self.database_query[
                 'RUNTIME'] == condition.time if condition.time != '?t1' and condition.type == 'RUNTIME' else always_true_condition) &
            (self.database_query[
                 'SOURCE'] == condition.start_place if condition.start_place else always_true_condition) &
            (self.database_query[
                 'DEST'] == condition.end_place if condition.end_place else always_true_condition)
            ]

        return self.decode_result(query_result,
                                  (query_procedure.type, query_procedure.object, condition.type))

    def answer(self, question):
        tokens = self.tokenizer.tokenize(question)
        relations = self.parser.parse(tokens)
        grammars = self.parser.construct_grammar(relations)
        logical_forms = self.parser.construct_logical_form(grammars)
        procedural_semantics = self.parser.construct_procedural_semantic(logical_forms)
        output_str = self.query_database(procedural_semantics)
        return {
            'relations': relations,
            'grammatical_relations': grammars,
            'logical_forms': logical_forms,
            'procedural_semantics': procedural_semantics,
            'output': output_str
        }


if __name__ == '__main__':
    input_dir = 'input'
    output_dir = 'output'
    qa = QuestionAnswering(database_path=os.path.join(input_dir, 'database.csv'))
    queries_file = os.path.join(input_dir, 'queries.txt')

    with open(queries_file, 'r') as f:
        queries = f.read().splitlines()
    for idx, query in enumerate(queries):
        output = qa.answer(query)
        with open(os.path.join(output_dir, f'output_{idx}.txt'), 'w') as f:
            # relation
            f.write('Relation:\n')
            for relation in output['relations']:
                f.write(relation.__str__() + '\n')
            # grammatical relation
            f.write('\nGrammatical Relation:\n')
            for grammatical_relation in output['grammatical_relations']:
                f.write(grammatical_relation.__str__() + '\n')
            # logical form
            f.write('\nLogical Form:\n')
            for key, logical_form in output['logical_forms'].items():
                if logical_form:
                    f.write(f"{' '.join(loc.__str__() for loc in logical_form)}\n")
            # procedural semantic
            f.write('\nProcedural Semantic:\n')
            for procedural_semantic in output['procedural_semantics']:
                f.write(procedural_semantic.__str__() + '\n')
            # output
            f.write('\nOutput:\n')
            f.write(output['output'] + '\n')
