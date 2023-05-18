# Assignment for NLP course

## Table of contents
- [Table of contents](#table-of-contents)
- [PERSONAL INFORMATION](#personal-information)
- [Notes](#notes)
  - [Setup](#setup)
  - [Structure](#Structure)


## PERSONAL INFORMATION
- **Name**: Nguyễn Minh Hùng
- **Student ID**: 1952737
- **Mail**: hung.nguyenantslayer@hcmut.edu.vn

## Notes
### Setup
- Python 3.7S
- I used `underthesea` library for word segmentation (tokenizer), and `pandas` for storing database as dataframe.
```bash
pip install -r requirements.txt
```

### Structure
```bash
.
├── input
│   ├── database.csv
│   └── queries.txt
├── main.py
├── modules
│   ├── __init__.py
│   ├── parser.py
│   ├── relations.py
│   ├── semantics.py
│   └── tokenizer.py
├── output
│   ├── output_0.txt
│   ├── output_1.txt
│   ├── ...
├── README.md
└── requirements.txt
```
- `input/database.csv`: Database of the flights.
- `input/queries.txt`: Queries to be processed.
- `output/output_*.txt`: Output files.
- `modules/`: Modules contains needed module to process the queries sequentially.
- `modules/parser.py`: Implement Dependency Parser.
  - ```python
    class DependencyParser(object):
        def parse(self, sentence: str) -> List[Relation]:
            """Something"""
        def construct_grammar(self, relations: List[Relation]) -> List[GrammaticalRelation]:
            """Something"""
        def construct_logical_form(self, grammars: List[GrammaticalRelation]):
            """Something"""
        def construct_procedural_semantic(self, logical_forms) -> List[ProceduralSemantic]:
            """Something"""
    ```
  - `parse(sentence)`: Parse a sentence and return a list of `Relations`.
  - `construct_grammar(relations)`: Construct grammars from a list of `Relations`.
  - `construct_logical_form(grammars)`: Construct logical form from a list of `GrammaticalRelation`.
  - `construct_procedural_semantic(logical_form)`: Construct procedural semantic from logical form.
- `modules/relations.py`: Create some `GrammaticalRelation` class.
- `modules/semantics.py`: Create some procedural semantic classes.
- `modules/tokenizer.py`: Modified Word segmentation for VietNamese.
  - ```python
    class Tokenizer(object):
        def tokenize(self, sentence: str) -> List[str]:
            """Something"""
    ```
  - `tokenize(sentence)`: Tokenize a sentence and return a list of words.
- `output/`: Output folder contains `.txt` files for each query.
- `main.py`: Main file to run the program.
  - ```python
    class QuestionAnswering(object):
        def __init__(self, database_path: str):
            """Something"""
        def answer(self, question:str):
            """Something"""
    ```
  - `database_path`: Path to the database file.
  - `answer(question)`: Answer the queries and return the result.


