# 重用异常类
from abc import abstractmethod, ABCMeta

__author__ = 'mori'


class CompileError(Exception, metaclass=ABCMeta):
    """
    编译公用异常抽象类
    """

    def __init__(self, line_num, error_msg):
        self.line_num = line_num
        self.error_msg = error_msg

    @abstractmethod
    def print(self):
        ...


class LexicalError(CompileError):
    """
    词法错误类
    """

    def print(self):
        print("\033[1;31;40;m第[{0}]行包含词法错误，{1}\033[0m".format(self.line_num, self.error_msg))


LACK_LEFT_PARE = '缺失左圆括号'
LACK_RIGHT_PARE = '缺失右圆括号'
LACK_LEFT_BRACE = '缺失左大括号'
LACK_RIGHT_BRACE = '缺失右大括号'
LACK_RIGHT_SQUARE = '缺少右方括号'
LACK_MAIN_DECL = '缺少主函数声明'
LACK_FUNCTION_NAME = '缺少函数名'
LACK_FUNCTION_BODY = '缺少函数体'
LACK_INT = '缺少int关键字'
LACK_ID = '缺少标识符'
LACK_SEMI = '缺少分号'
LACK_COLON = '缺少冒号'
LACK_CASE = '缺少case语句'
LACK_COMMA = '缺少逗号'
LACK_WHILE = '缺少while关键字'
LACK_OPERAND = '缺少操作数'
LACK_NUM = '缺少正整数'
MULTIPLE_DECL = '标识符[{0}]：重复声明'
UNEXPECTED_END = '意外的结尾[{0}]'
UNRECOGNIZED_STATEMENT = '无法识别的语句:[{0}]'
NO_STATEMENT = '变量[{0}]未声明'
DISALLOW_STATEMENT = '当前位置不允许使用[{0}]'


class GrammarError(CompileError):
    """
    语法错误类
    """

    def __init__(self, line_num, where, error_msg):
        super().__init__(line_num, "{0}: {1}".format(where, error_msg))

    def print(self):
        print("\033[1;31;40;m第[{0}]行附近包含语法错误，{1}\033[0m".format(self.line_num, self.error_msg))


INDEX_ERROR = '数组下标越界，最大值：[{0}]，当前值:[{1}]'
NOT_AN_ARRAY = '变量[{}]不是数组'
MULTIPLE_CASE = '重复的条件'
ERROR_ARGUMENTS_LIST = '没有参数列表或参数数目不匹配'
NOT_CALLABLE = '[{}]不可被调用'


class SemanticError(CompileError):
    """
    语义错误类
    """

    def __init__(self, line_num, where, error_msg):
        super().__init__(line_num, "{0}: {1}".format(where, error_msg))

    def print(self):
        print("\033[1;31;40;m第[{0}]行附近包含语义错误，{1}\033[0m".format(self.line_num, self.error_msg))


DIVISOR_IS_0 = "除数为0"
STACK_OVERFLOW = "内存栈溢出"


class TestRuntimeError(RuntimeError):
    """ 运行时错误类 """

    msg = ''

    def __init__(self, msg):
        self.msg = msg

    def print(self):
        print("\033[1;31;40;m运行时错误：{}\033[0m".format(self.msg))