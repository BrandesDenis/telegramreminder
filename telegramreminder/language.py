import configparser
import os


dir_path = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(dir_path, "translations.ini")

configparser = configparser.ConfigParser() 
with open(file_path, encoding='utf-8') as f:
    configparser.read_file(f)


def translate(string, language):
    if language in configparser and string in configparser[language]:
        return configparser[language][string]
   
    return string