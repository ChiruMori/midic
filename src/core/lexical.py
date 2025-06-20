# 词法分析
__author__ = "mori"

import os
import re

from ..midi.midi_reader import MidiReader

from .compile_error import LexicalError

LETTER_RE = "^[a-zA-Z]$"  # 匹配单字母
DIGIT_RE = "^\\d$"  # 匹配单数字
SINGLE_RE = "^[\\+\\-*=\\(\\)\\{\\}:;,<>!\\[\\]]$"  # 匹配单分界符，没有/
DOUBLE_ST_RE = "^[\\|&<>!=]$"  # 双分界符起始识别标志
BOUNDARY_RE = "^([<>!=]=)|&{2}|\\|{2}|[\\+\\-*=\\(\\)\\{\\}:;,<>!/]$"  # 匹配分界符
IDENTIFIER_RE = (
    "^[a-z|A-Z][a-z|A-Z|\\d]*$"  # 匹配合法标识符：字母开头，字母数字的任意组合为结尾
)


class LexicalAnalyse:
    """
    词法分析主类
    """

    __keyword = [
        "if",
        "else",
        "for",
        "while",
        "do",
        "int",
        "write",
        "read",
        "switch",
        "case",
        "default",
        "call",
        "function",
        "main",
        "return",
        "call",
        "break",
        "continue",
    ]  # 保留字

    def __init__(self, file_in):
        """
        构造
        :param file_in: 传入的 MIDI 文件名
        """
        if os.path.exists(file_in):
            self.new_id = False  # 新读取ID的标记，读取到int时值为true
            self.midi_reader = iter(MidiReader(file_in))
            self.line_num = 1  # 初始化行号
            self.__keyword.sort()  # 保留字排序，用于二分查找
            file_out = "out/lexical.o"
            self.out_file = open(file_out, "w+", encoding="utf-8")
            self.out_filename = file_out  # 保存输出文件名
        else:
            raise FileNotFoundError("找不到指定的文件")

    def analyse(self):
        """
        词法分析主函数
        """
        temp_char = self.__read_char()
        while temp_char != "":
            try:
                if (temp_char == " ") or (temp_char == "\t") or (temp_char == "\n"):
                    # 读到空格、制表符，重读字符
                    temp_char = self.__read_char()
                elif re.match(LETTER_RE, temp_char):
                    # 读到字母，调用标识符读取函数
                    temp_char = self.__read_identifier(temp_char)
                elif re.match(SINGLE_RE, temp_char) or re.match(
                    DOUBLE_ST_RE, temp_char
                ):
                    # 单分界符或双分界符字首
                    temp_char = self.__read_boundary(temp_char)
                elif re.match(DIGIT_RE, temp_char):
                    # 读到数字，调用数字读取函数
                    temp_char = self.__read_digit(temp_char)
                elif temp_char == "/":
                    # 读到/，进行注释与'/'处理
                    temp_char = self.__read_comment(temp_char)
                elif temp_char == '\0':
                    # 读到文件结束符
                    break
                else:
                    raise LexicalError(
                        self.line_num,
                        "非法字符：[{0}]，code：[{1}]".format(
                            temp_char, ord(temp_char)
                        ),
                    )
            except LexicalError as e:
                e.print()  # 错误输出
                if self.midi_reader.has_msg():
                    temp_char = self.__read_char()  # 发生错误时，继续读取下一个字符，如果需要发生错误时停止，将try-catch放到循环外
                else:
                    break
        return self.out_filename  # 返回单词流文件名

    def __read_comment(self, last_char):
        """
        注释处理、/字符处理
        :param last_char: 当前字符
        :return: 最后读取的字符
        """
        temp_str = last_char
        last_char = self.__read_char()
        if last_char == "*":
            back_char = self.__read_char()
            last_char = self.__read_char()
            temp_str = "/*" + back_char
            # 循环到*/结束
            while not ((back_char == "*") and (last_char == "/")):
                temp_str += last_char  # 拼接注释部分
                back_char = last_char  # 备份字符
                last_char = self.__read_char()  # 读取字符
            temp_str += last_char  # 拼接最后的/
            if temp_str.count("/*") + temp_str.count("*/") > 2:
                raise LexicalError(self.line_num, "注释不允许嵌套")
            last_char = self.__read_char()
            # self.__print_info('comment', temp_str)  # 输出注释，解开本行注释可以输出注释内容
        else:
            self.__print_info(temp_str, temp_str)  # 单独/的处理
        return last_char

    def __read_boundary(self, last_char):
        """
        私有方法，读取分界符
        :param last_char: 当前字符
        :return: 最后读取的字符
        """
        temp_str = last_char
        stop = False
        if re.match(DOUBLE_ST_RE, last_char):
            if re.match(SINGLE_RE, last_char):
                # <>!=开头的分界符
                last_char = self.__read_char()
                if last_char == "=":
                    temp_str += last_char
                else:
                    stop = True
            else:
                # &|开头的分界符
                last_char = self.__read_char()
                if last_char is not temp_str:  # 后一个字符与当前字符不同
                    raise LexicalError(
                        self.line_num,
                        "非法的分界符：{0}{1}".format(temp_str, last_char),
                    )
                else:
                    # 识别为&&或||
                    temp_str += last_char
        # elif re.match(SINGLE_RE, last_char):  # 余下的单分界符，+-*(){};,.这里没有/
        #     if last_char is '{':
        #         self.__new_scope()  # 读取到'{'，创建新的作用域
        #     elif last_char is '}':
        #         previous = self.now_scope.previous
        #         if previous is None:  # 已经回退到顶级作用域
        #             raise CompileError(self.line_num, "不匹配的}")
        #         self.now_scope = previous  # 读取到'}'，返回上移作用域
        self.__print_info(temp_str, temp_str)
        if not stop:
            last_char = self.__read_char()
        return last_char

    def __read_digit(self, last_char):
        """
        私有方法，读取数字
        :param last_char: 上一个字符、开始字符
        :return: 执行后，最后读取的字符
        """
        temp_num = ""
        # 循环到文件结尾或中间返回
        while last_char != "":
            # 空格符、制表符、单分界符、双分界符
            if (
                last_char == " "
                or last_char == "\t"
                or re.match(SINGLE_RE, last_char)
                or re.match(DOUBLE_ST_RE, last_char)
            ):
                break
            elif re.match(DIGIT_RE, last_char):
                # 得到数字，进行拼接
                temp_num += last_char
                last_char = self.__read_char()
            else:
                raise LexicalError(self.line_num, "非法字符：[{0}]".format(last_char))
        self.__print_info("NUM", temp_num)
        return last_char

    def __read_identifier(self, last_char):
        """
        私有方法：分析标识符、保留字
        :param last_char: 上一个字符、开始字符
        :return: 最后读取的字符
        """
        temp_str = ""
        # 为字母和数字时，持续读取字符
        while re.match(DIGIT_RE, last_char) or re.match(LETTER_RE, last_char):
            temp_str += last_char  # 拼接标识符
            last_char = self.__read_char()
        # 如果得到的标识符为保留字，flag为当前字符串。否则为ID
        # flag = temp_str if re.match(self.keyword_re, temp_str) else 'ID'  # 正则表达式方法
        flag = (
            temp_str.lower()
            if self.__is_keyword(temp_str.lower(), 0, len(self.__keyword) - 1)
            else "ID"
        )
        self.__print_info(flag, temp_str)
        return last_char  # 返回最后读取的字符

    def __is_keyword(self, word, left, right):
        """
        二分法查找比对、判断当前单词是否为保留字
        程序中注释掉的部分为正则表达式方式
        :param word: 当前单词
        :param left right: 二分标记
        :return: 布尔值
        """
        mid = int((right + left) / 2)  # 二分索引值
        if self.__keyword[mid] == word:  # 匹配，直接返回
            return True
        elif left == right:
            return False
        elif self.__keyword[mid] > word:  # 中间值大于当前值，递归左边
            return self.__is_keyword(word, left, mid)
        else:  # 递归右边
            return self.__is_keyword(word, mid + 1, right)

    def __print_info(self, i_type, value):
        # if i_type == 'ID':
        #     scope = self.now_scope.get_scope_str(value)
        #     if scope is None:  # 作用域为None，说明没有声明
        #         raise CompileError(self.line_num, "标识符{0}没有声明".format(value))
        #     print('\033[0;34;0m{type:15}{val:15}Scope：{scope}\033[0m'.format(type=i_type, val=value, scope=scope))
        # else:
        # print('\033[0;34;0m{type:15}{val}\033[0m'.format(type=i_type, val=value))
        self.out_file.write("{0:15} {1}\n".format(i_type, value))  # 单词输出到文件

    def close(self):
        """
        关闭文件流，词法分析结束后调用
        """
        self.out_file.close()

    def __read_char(self):
        try:
            # 将读取到的一个字节数据直接转为字符
            temp_char = chr(next(self.midi_reader))
            if temp_char == "\n":
                self.out_file.write(
                    "{0}\n".format("[enter]")
                )  # 单词输出到文件，输出单词与行号
                self.line_num += 1
                temp_char = " "  # 行号加1，转为空格
            return temp_char
        except StopIteration:
            return ""
