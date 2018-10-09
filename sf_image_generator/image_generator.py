import os
import io
import logging
import opencc
import traceback
import random
import numpy as np
import argparse

from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from sf_image_generator.util import file_is_valid, create_dictionaries, UNK
from random import choices, choice

DEFAULT_CORPUS=os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'data', 'insurance_corpus')
DEFAULT_FONTS=os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'conf', 'fonts')
DEFAULT_DICT=os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'data', 'dict', 'full_dict.txt')
DEFAULT_FONT_SIZE = [12, 14, 16,  20, 24, 28, 32, 36, 40]
DEFAULT_SENT_LEN = [10, 20, 30, 40, 50]
DEFAULT_SAVE_IMAGE_PATH=os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..', 'data', 'image', 'test')
OUTPUT_ROOT=os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'output')
TRAIN_DATASET=os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'data', 'insurance_corpus', 'train')
VAL_DATASET=os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'data', 'insurance_corpus', 'valid')
DICT_FILE =os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'data', 'dict', 'full_dict.txt')



logger = logging.getLogger(__name__)

class ImageGenerator(object):
    __slots__ = ['font_path', 'tc_font_list', 'sc_font_list', 'font_size', 'dict', 'rev_dict', 'corpus_path', 'skew', 'add_noise', 'mode',
                 'sent_len', 'width_margin', 'height_margin', 'dataset', 'img_h', 'img_w', 'char_dict']

    def __init__(self, corpus_path=DEFAULT_CORPUS, font_path=DEFAULT_FONTS, dict_path=DEFAULT_DICT,
                 font_size=DEFAULT_FONT_SIZE, skew=False, add_noise=False, mode='train', sent_len = DEFAULT_SENT_LEN,
                 width_margin=3, height_margin=3, img_h=32, img_w=256):
        self.font_path=font_path
        self.tc_font_list = self._load_fonts(font_path, 'fonts_tc')
        self.sc_font_list = self._load_fonts(font_path, 'fonts_sc')
        self.font_size=font_size
        self.dict, self.rev_dict = create_dictionaries(dict_path)
        self.corpus_path=corpus_path
        self.skew=skew
        self.add_noise=add_noise
        self.mode=mode
        self.sent_len = sent_len
        self.width_margin=width_margin
        self.height_margin=height_margin
        self._load_dataset(corpus_path)
        self.img_h = img_h
        self.img_w = img_w
        self.char_dict = self._dict_as_str()


    def _load_fonts(self, font_path, sub_path):
        file_list = [os.path.join(font_path, sub_path, name) for name in os.listdir(os.path.join(font_path, sub_path)) if name != ".DS_Store"]
        # file_list = ['simhei.ttf'] #TODO remove this line # for development only not the real training
        return file_list

    def _create_image(self, text, font_list, show_image=False, save_image=False, color=False):

        font_file = choice(font_list)
        # font_size = choice(self.font_size)
        font_size =28
        font = ImageFont.truetype(font_file,font_size)
        text_width, text_height = font.getsize(text)
        # width_margin = random.randint(0, self.width_margin)
        # height_margin = random.randint(0, self.height_margin)
        width_margin = self.width_margin
        height_margin = self.height_margin
        text_width = text_width + (width_margin * 2)
        text_height = text_height + (height_margin * 2)
        # text_width = 1150
        # text_height = 32
        if color:
            img = Image.new("RGB", (text_width, text_height), "white")
        else:
            img = Image.new("L", (text_width, text_height), "white")
        draw = ImageDraw.Draw(img)
        draw.text((width_margin, height_margin), text, 0, font=font)
        #TODO add skew to image
        #TODO add noise to image
        # img = img.resize((self.img_w, self.img_h), Image.ANTIALIAS)
        scale = img.size[1] * 1.0 / 32
        w = img.size[0] / scale
        w = int(w)
        img = img.resize((w, 32))

        if show_image:
            img.show()
        if save_image:
            file = os.path.join(DEFAULT_SAVE_IMAGE_PATH, str(random.randint(1,10000)).zfill(5)+'.png')
            img.save(file)

        # img = image.img_to_array(img)
        return img

    def random_next_item(self):
        no_of_vocab = len(self.dict)
        char_array = []
        idx_array = []
        for i in range(20):
            idx = random.randint(1,no_of_vocab)
            char = self.rev_dict[idx]
            char_array.append(char)
            idx_array.append(idx)
        text = ''.join(char_array)
        print(text)


    def _load_dataset(self, corpus_path):
        dataset = []
        full_corpus_path = corpus_path
        for root, subFolders, files in os.walk(full_corpus_path):
            for name in files:
                if not file_is_valid(root, name):
                    continue
                with open(os.path.join(root, name), mode='r', encoding='utf-8') as corpus_file:
                    try:
                        content=corpus_file.read()
                        corpus_file.close()
                        lines = content.split('\n')
                        dataset.append(lines)
                    except Exception as e:
                        traceback.print_exc()
                        print('Something not very nice happened with {}; skipping file.'.format(os.path.join(root, name)))
        self.dataset = dataset

    def next_item(self, max_len, show_image=False, save_image=False, color=False):
        go = True
        font_list = None

        while go:
            try:
                lines = choice(self.dataset)
                line = lines[random.randint(0,1)]
                if self._random_simplify():
                    line = opencc.convert(line)
                    font_list = self.sc_font_list
                else:
                    line = opencc.convert(line, config='s2t.json')
                    font_list = self.tc_font_list
                text = self._random_pick_text(line, max_len)
                if len(text.strip())>0 and '{' not in text and '\n' not in text:
                    text_img = self._create_image(text, font_list,show_image, save_image, color)
                    idx_list = self._text2idx(text, max_len)
                    go = False
            except Exception as e:
                traceback.print_exception(e)
        return text_img, idx_list, text


    def _random_simplify(self):
        num = random.randint(1,10)
        return 0 == num % 2

    def _random_pick_text(self, line, max_len):
        text = ''
        line_len = len(line)
        if line_len <= max_len:
            text= line
        else:
            max_start = line_len - max_len
            start_idx = random.randint(0, max_start-1)
            text = line[start_idx: start_idx+max_len]

        for char in text:
            if char not in self.char_dict:
                return ''

        return text

    def _text2idx(self, text, max_len):
        idx_list = np.zeros(max_len)
        for i, char in enumerate(text):
            try:
                idx_list[i]=(self.dict[char])
            except KeyError as e:
                idx_list[i] = (self.dict[UNK])


        return idx_list

    def _dict_as_str(self):
        corpus_file = open(DICT_FILE, mode='r', encoding='utf-8')
        content = corpus_file.read()
        corpus_file.close()
        list = content.split('\n')
        return ''.join(list)


def get_input_generator(path=None, imgH=32, imgW=512):
    if path:
        generator=ImageGenerator(path,img_h=imgH, img_w=imgW)
    else:
        generator=ImageGenerator(img_h=imgH, img_w=imgW)

    return generator

def process(begin_batch=1, train_batch=10, test_batch=1):
    train_generator = get_input_generator(TRAIN_DATASET)
    create_images(train_generator, os.path.join(OUTPUT_ROOT, 'Train'), begin_batch=begin_batch, batch=train_batch)
    val_generator = get_input_generator(VAL_DATASET)
    create_images(val_generator, os.path.join(OUTPUT_ROOT, 'Test'), begin_batch=1, batch=test_batch)

def create_images(generator, root_out_dir, begin_batch=1, batch=5, annotation_name='sample.txt'):
    if not os.path.exists(root_out_dir):
        os.makedirs(root_out_dir, exist_ok=True)
    anno_path = os.path.join(root_out_dir, annotation_name)
    anno_path_csv = os.path.join(root_out_dir, 'sample.csv')
    with open(anno_path, 'w') as anno_file:
        anno_csv = open(anno_path_csv, 'w')
        for i in range(begin_batch,begin_batch+batch+1):
            l1_dir = str(i).zfill(5)
            for j in range(1, 11):
                l2_dir = str(j).zfill(2)
                for k in range(1, 501):
                    try:
                        text_img, _, text =generator.next_item(random.randint(1,16), color=True)
                        # text_img, _, text = generator.next_item(30, color=True)
                        file=str(k).zfill(3) + '.jpg'
                        full_dir_path = os.path.join(root_out_dir, l1_dir, l2_dir)
                        os.makedirs(full_dir_path, exist_ok=True)
                        relative_path = os.path.join('./', l1_dir, l2_dir, file)
                        text_img.save(os.path.join(full_dir_path, file), "JPEG", quality=80, optimize=True, progressive=True)
                        anno_file.write(relative_path+'\t'+text+'\n')
                        formated_text=format_text(text)
                        anno_csv.write(os.path.join(full_dir_path, file) + '\t' + formated_text + '\n')
                    except Exception as e:
                        traceback.print_exc()

def format_text(text):
    array = [x for x in text]
    return '|'.join(array)


def init_args():
    """

    :return:
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--begin_batch', type=int, default=1, help='Begin Batch')
    parser.add_argument('--train_batch', type=int, default=4, help='No of train batch (every batch contains 5000 images)')
    parser.add_argument('--test_batch', type=int, default=1, help='No of test batch (every batch contains 5000 images)')

    return parser.parse_args()

if __name__=='__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')
    logger = logging.getLogger(__name__)
    args = init_args()
    process(args.begin_batch, args.train_batch, args.test_batch)


