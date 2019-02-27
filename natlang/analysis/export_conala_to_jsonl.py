import json
import keyword
import re
import tokenize
from io import StringIO
import string

REF_DIR = '/Users/ruoyi/Projects/PycharmProjects/data_fixer/conala_orig'
EXPORT = '/Users/ruoyi/Projects/PycharmProjects/data_fixer/conala_exported'

builtin_fns = ('abs', 'delattr', 'hash', 'memoryview', 'set', 'all', 'dict', 'help', 'min', 'setattr', 'any',
               'dir', 'hex', 'next', 'slice', 'ascii', 'divmod', 'id', 'object', 'sorted', 'bin', 'enumerate', 'input',
               'oct', 'staticmethod', 'bool', 'eval', 'int', 'open', 'str', 'breakpoint', 'exec', 'isinstance', 'ord',
               'sum', 'bytearray', 'filter', 'issubclass', 'pow', 'super', 'bytes', 'float', 'iter', 'print', 'tuple',
               'callable', 'format', 'len', 'property', 'type', 'chr', 'frozenset', 'list', 'range', 'vars',
               'classmethod', 'getattr', 'locals', 'repr', 'zip', 'compile', 'globals', 'map', 'reversed', '__import__',
               'complex', 'hasattr', 'max', 'round')

tokenize_nfa = re.compile(r'''
`([^`]+)`|    # annotated
("(?:\\"|[^"])*"|'(?:\\'|[^'])*')|    # str
([^\s]+)    # other stuff
''', re.VERBOSE)

word_checker = re.compile(r'''^[a-zA-Z][a-z]*('s)?$''')
str_checker = re.compile(r'''^("(\\"|[^"])*")|('(\\'|[^'])*')$''')


def parse_src(orig_line):
    value = []
    str_map = {}
    str_cnt = 0
    str_template = '_STR:{}_'
    matches = tokenize_nfa.finditer(' ' + orig_line)  # add a safe blank to the front
    for m in matches:
        groups = [(category, lexeme) for category, lexeme in enumerate(m.groups()) if lexeme is not None]
        if len(groups) > 1:
            raise RuntimeError("Multiple match in groups {}".format(groups))
        else:
            category, lexeme = groups[0]

        if category == 1 or (category == 0 and str_checker.match(lexeme)):
            # str literal or str as annotated content
            try:
                str_content = eval(lexeme)
            except SyntaxError:
                str_content = lexeme
                print('broken string found for entry {}'.format(i))
                print('broken string found in {}'.format(orig_line))
            if str_content in str_map:
                replacement = str_map[str_content]
            else:
                replacement = str_template.format(str_cnt)
                str_cnt += 1
                str_map[str_content] = replacement
            value.append(replacement)
        elif category == 0:
            # annotated variables
            value.append(lexeme)
            j = lexeme.find('.')
            if 0 < j < len(lexeme) - 1:
                new_tokens = ['['] + lexeme.replace('.', ' . ').split(' ') + [']']
                value.extend(new_tokens)
        else:
            punc = None
            if lexeme[-1] in string.punctuation:
                # punctuations
                punc = lexeme[-1]
                if lexeme[:-1]:
                    lexeme = lexeme[:-1]
                else:
                    # pure punctuation
                    value.append(punc)
                    continue

            if not word_checker.match(lexeme):
                # possible variables
                value.append(lexeme)
                j = lexeme.find('.')
                if 0 < j < len(lexeme) - 1:
                    new_tokens = ['['] + lexeme.replace('.', ' . ').split(' ') + [']']
                    value.extend(new_tokens)
            else:
                if lexeme.endswith("\'s"):
                    # 's
                    if lexeme[:-2]:
                        value.append(lexeme[:-2].lower())
                    value.extend(["'", 's'])
                else:
                    # normal word
                    value.append(lexeme.lower())

            if punc is not None:
                value.append(punc)

    return value, str_map


if __name__ == '__main__':
    with open('{}/{}.jsonl'.format(EXPORT, 'test'), 'w') as out_f, \
            open('{}/{}.json'.format(REF_DIR, 'conala-test'), 'r') as in_f:
        in_data = json.load(in_f)

        for i, example in enumerate(in_data):
            jsonl_entry = {'src': [],
                           'token': [],
                           'type': [],
                           'cano_code': [],
                           'decano_code': [],
                           'raw_code': example['snippet']}

            # tokenize src
            if 'rewritten_intent' in example and example['rewritten_intent']:
                jsonl_entry['src'], str_map = parse_src(example['rewritten_intent'])
            else:
                jsonl_entry['src'], str_map = parse_src(example['intent'])

            # fill in the code tokens and types
            raw_tk_stream = []
            for tk in tokenize.generate_tokens(StringIO(jsonl_entry['raw_code']).readline):
                category, lexeme = tk[:2]
                raw_tk_stream.append(list(tk))
                if category == tokenize.ENDMARKER:
                    break
                jsonl_entry['token'].append(lexeme)
                if category == tokenize.NAME:
                    if keyword.iskeyword(lexeme) or lexeme in builtin_fns:
                        jsonl_entry['type'].append('KEYWORD')
                    else:
                        jsonl_entry['type'].append('NAME')
                elif category == tokenize.STRING:
                    try:
                        str_content = eval(lexeme)
                    except SyntaxError:
                        str_content = lexeme
                        print('broken string found for entry {}'.format(i))
                    if str_content in str_map:
                        masked_str = '" {} "'.format(str_map[str_content])
                        jsonl_entry['token'][-1] = masked_str
                        raw_tk_stream[-1][1] = masked_str
                    jsonl_entry['type'].append('STRING')
                elif category == tokenize.NUMBER:
                    jsonl_entry['type'].append('NUMBER')
                elif category == tokenize.OP:
                    jsonl_entry['type'].append('OP')
                elif category == tokenize.NEWLINE:
                    jsonl_entry['type'].append('NEWLINE')
                elif category == tokenize.NL:
                    jsonl_entry['type'].append('NL')
                elif category == tokenize.INDENT:
                    jsonl_entry['type'].append('INDENT')
                elif category == tokenize.DEDENT:
                    jsonl_entry['type'].append('DEDENT')
                else:
                    print("I don't recognize this token {} in code {}".format(
                        repr(lexeme),
                        repr(jsonl_entry['raw_code'])))

            jsonl_entry['cano_code'] = tokenize.untokenize(raw_tk_stream)
            jsonl_entry['decano_code'] = jsonl_entry['cano_code']
            jsonl_entry['str_map'] = str_map

            # assert jsonl_entry['token'] != [] and jsonl_entry['type'] != []
            assert len(jsonl_entry['token']) == len(jsonl_entry['type'])
            out_f.write(json.dumps(jsonl_entry))
            out_f.write('\n')
