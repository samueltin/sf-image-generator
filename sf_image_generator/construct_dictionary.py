import os
import argparse
import traceback
import opencc
from sf_image_generator.util import file_is_valid


CORPUS_ROOT=os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'data', 'insurance_corpus')
OUTPUT_DICT=os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'data',  'dict', 'new_dict.txt')


def process(corpus_path=CORPUS_ROOT, out_dict_path=OUTPUT_DICT):


    full_dict = []

    for root, subFolders, files in os.walk(corpus_path):
        for name in files:
            if file_is_valid(root, name):
                with open(os.path.join(root, name), mode='r', encoding='utf-8') as corpus_file:
                    try:
                        content=corpus_file.read()
                        content_cn = opencc.convert(content, config='t2s.json')
                        corpus_file.close()
                        lines = content.split()
                        lines_cn = content_cn.split()
                        for line in lines:
                            for char in line:
                                if char not in full_dict:
                                    full_dict.append(char)
                        for line in lines_cn:
                            for char in line:
                                if char not in full_dict:
                                    full_dict.append(char)
                    except Exception as e:
                        traceback.print_exc()
                        print('Something not very nice happened with {}; skipping file.'.format(os.path.join(root, name)))

    if '\n' in full_dict:
        full_dict.remove('\n')
    full_dict.sort()

    with open(out_dict_path, mode='w', encoding='utf-8') as cn_cdict_file:
        cn_cdict_file.writelines('\n'.join(full_dict))



if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Build Char Dictionary')
    parser.add_argument(
        '--corpus_dir',
        type=str,
        required=True,
        default=CORPUS_ROOT,
        help='Root path of corpus')

    process(CORPUS_ROOT, OUTPUT_DICT)

