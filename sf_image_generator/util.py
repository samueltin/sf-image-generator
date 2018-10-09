import os
import logging
import io
import copy
import ruamel.yaml as yaml

logger = logging.getLogger(__name__)
UNK = '<UNK>'

def file_is_valid(path_root, file_name):
    full_path = os.path.join(path_root, file_name)
    return ('txt' in full_path) \
           and not file_name.startswith('.') \
           and not file_name.endswith('.pdf')

def create_dictionaries(vocab_file_path):
    logging.info(vocab_file_path)
    vocabulary_file = io.open(vocab_file_path, mode='r', encoding='utf-8')
    vocabulary = vocabulary_file.readlines()
    vocabulary_file.close()
    vocabulary = [v.strip() for v in vocabulary]  # remove space
    vocabulary.append(' ')
    vocabulary.append(UNK)
    dictionary = dict(zip(vocabulary, list(range(0, len(vocabulary)))))
    reversed_dictionary = dict(zip(dictionary.values(), dictionary.keys()))

    return dictionary, reversed_dictionary

def read_yaml_file(path):
    with open(path, encoding='utf-8') as stream:
        return yaml.safe_load(stream)

class Config(object):
    __slots__ = ['config', 'path']

    def __init__(self, path=None, config=None, *args, **kwargs):
        if config is None:
            config = {}
        self.path = path
        self.config = config

    def to_dict(self):
        return copy.deepcopy(self.config)

    def get(self, dict_keys, default_value=None, config=None):
        if config is None:
            config = self.config
        if isinstance(dict_keys, str):
            dict_keys = dict_keys.split('.')
        if dict_keys[0] in config:
            if len(dict_keys) == 1 or config[dict_keys[0]] is None:
                return config[dict_keys[0]]
            else:
                return self.get(dict_keys[1:], default_value, config[dict_keys[0]])
        else:
            return default_value


class YamlConfig(Config):
    FILE_PATH = None

    def __init__(self, path=None, *args, **kwargs):
        super(YamlConfig, self).__init__(*args, **kwargs)
        self.path = path or self.FILE_PATH
        if self.path:
            self.from_yamlfile(self.path)

    def from_yamlfile(self, path):
        try:
            self.config = read_yaml_file(path)
            if self.config is None:
                self.config = {}
        except yaml.YAMLError as e:
            logger.error("Cannot parse YAML config file {}: {}".format(path, e))
            raise e


class AppConfig(YamlConfig):
    FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'conf', 'kersa_config.yml')

    def __init__(self, path=FILE_PATH, *args, **kwargs):
        super(AppConfig, self).__init__(*args, **kwargs)
        self.from_yamlfile(path)

