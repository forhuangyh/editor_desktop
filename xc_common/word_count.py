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

    cnChars = 0  # 全角字符
    enChars = 0  # 英文字母
    ruChars = 0  # 俄语
    nmChars = 0  # 数字字符
    # spChars = 0  # 空格
    # otChars = 0  # 其它字符

    thai_chars_pattern = re.compile("[\u0E00-\u0E7F]")
    # 泰语
    if thai_chars_pattern.findall(txt):
        return word_count_func_for_thai(txt)

    string_val_pattern = re.compile(r"[^A-Za-z0-9\u4E00-\u9FA5\u0400-\u04FF\u00C0-\u00FF\']")
    # en_chars_pattern = re.compile(".*?([a-zA-Z]+).*?")
    # nmChars_pattern = re.compile(".*?([1-9]+).*?")
    # ruChars_pattern = re.compile('[\u0400-\u04FF]')
    # cnChars_pattern = re.compile(".*?([\u4E00-\u9FA5]+).*?")

    # en_chars_pattern = re.compile("([a-zA-Z]+)")
    # nmChars_pattern = re.compile("([1-9]+)")
    # ruChars_pattern = re.compile('[\u0400-\u04FF]')
    # cnChars_pattern = re.compile("([\u4E00-\u9FA5]+)")

    string_val = string_val_pattern.sub(' ', txt).strip()
    # for ch in string_val.split():
    #     if en_chars_pattern.findall(ch) or ch in en_punc:
    #         enChars += 1
    #     elif nmChars_pattern.findall(ch):
    #         nmChars += 1
    #     elif ruChars_pattern.findall(ch):
    #         ruChars += 1
    #     elif ch.isspace():
    #         spChars += 1
    #     elif cnChars_pattern.findall(ch):
    #         cnChars += 1
    #     else:
    #         otChars += 1

    WORD_PATTERN = re.compile(
        r'([\u4E00-\u9FA5]+)|'       # Group 1: Chinese characters
        r'([\u0400-\u04FF]+)|'       # Group 2: Russian characters
        r'([a-zA-Z]+)|'             # Group 3: English words
        r'([1-9]+)',                # Group 4: Numbers
        # r'([{}])'.format(re.escape(en_punc))
    )
    for ch in string_val.split():
        if ch in en_punc:
            enChars += 1
            continue
        if ch.isspace():
            continue
        for match in WORD_PATTERN.finditer(ch):
            if match.group(1):  # Matched Chinese characters
                cnChars += 1
                break
            elif match.group(2):  # Matched Russian characters
                ruChars += 1
                break
            elif match.group(3):  # Matched English words
                enChars += 1
                break
            elif match.group(4):  # Matched numbers
                nmChars += 1
                break
    # for match in WORD_PATTERN.finditer(string_val):
    #     if match.group(1):  # Matched Chinese characters
    #         cnChars += 1
    #         continue
    #     elif match.group(2):  # Matched Russian characters
    #         ruChars += 1
    #         continue
    #     elif match.group(3):  # Matched English words
    #         enChars += 1
    #         continue
    #     elif match.group(4):  # Matched numbers
    #         nmChars += 1
    #         continue

    return cnChars + enChars + nmChars + ruChars


# import re
# import six
# from pythainlp import word_tokenize

# # 将常用的正则表达式预编译，提升性能
# # 这个正则表达式可以匹配：
# # - 中文字符: [\u4E00-\u9FA5]+
# # - 俄语字符: [\u0400-\u04FF]+
# # - 英文单词: [a-zA-Z]+
# # - 数字串: [0-9]+
# WORD_PATTERN = re.compile(r'([\u4E00-\u9FA5]+)|([\u0400-\u04FF]+)|([a-zA-Z]+)|([0-9]+)')


# def word_count_func_for_thai(sentence):
#     """泰语字数统计，保持不变"""
#     words = word_tokenize(sentence)
#     return len(words)


# def word_count_func(txt):
#     """
#     字数统计优化版
#     """
#     if not isinstance(txt, six.text_type):
#         raise TypeError('Word count requires a str string')

#     # 先判断是否是泰语，如果是则直接返回
#     if re.search(r'[\u0E00-\u0E7F]', txt):
#         return word_count_func_for_thai(txt)

#     cn_count = 0
#     en_count = 0
#     ru_count = 0
#     nm_count = 0

#     # 使用预编译的正则表达式，一次性找出所有匹配项
#     for match in WORD_PATTERN.finditer(txt):
#         if match.group(1):  # 匹配到中文
#             cn_count += 1
#         elif match.group(2):  # 匹配到俄语
#             ru_count += 1
#         elif match.group(3):  # 匹配到英文
#             en_count += 1
#         elif match.group(4):  # 匹配到数字
#             nm_count += 1

#     return cn_count + en_count + ru_count + nm_count
