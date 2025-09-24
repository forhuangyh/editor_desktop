import io
import re
import six

from string import punctuation as en_punc
from pythainlp import word_tokenize


def word_count_func_for_thai(sentence):
    words = word_tokenize(sentence)
    return len(words)


def word_count_func(txt):
    """
    字数统计
    """
    if not isinstance(txt, six.text_type):
        raise TypeError('Word count requires a str string')

    cn = 0  # 汉字数
    en = 0  # 非中文单词
    nm = 0  # 数字
    cnChars = 0  # 全角字符
    enChars = 0  # 英文字母
    ruChars = 0  # 俄语
    nmChars = 0  # 数字字符
    spChars = 0  # 空格
    otChars = 0  # 其它字符

    # 泰语
    if re.findall('[\u0E00-\u0E7F]', txt):
        return word_count_func_for_thai(txt)

    string_val = re.sub(r"[^A-Za-z0-9\u4E00-\u9FA5\u0400-\u04FF\u00C0-\u00FF\']", ' ', txt)
    for ch in string_val.split():
        if re.findall(".*?([a-zA-Z]+).*?", ch) or ch in en_punc:
            enChars += 1
        elif re.findall(".*?([1-9]+).*?", ch):
            nmChars += 1
        elif re.findall('[\u0400-\u04FF]', ch):
            ruChars += 1
        elif ch.isspace():
            spChars += 1
        elif re.findall(".*?([\u4E00-\u9FA5]+).*?", ch):
            cnChars += 1
        else:
            otChars += 1

    return cnChars + enChars + nmChars + ruChars
