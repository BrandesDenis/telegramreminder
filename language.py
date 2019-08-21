import configparser


configparser = configparser.ConfigParser() 
with open('translations.ini', encoding='utf-8') as f:
    configparser.read_file(f)


def translate(string, language):
    if language in configparser and string in configparser[language]:
        return configparser[language][string]
   
    return string