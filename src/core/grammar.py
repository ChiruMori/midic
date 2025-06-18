# 语法分析程序
from queue import Queue

from core.CompileError import (
    LACK_FUNCTION_BODY,
    LACK_FUNCTION_NAME,
    LACK_LEFT_PARE,
    LACK_NUM,
    LACK_OPERAND,
    LACK_RIGHT_PARE,
    LACK_WHILE,
    NO_STATEMENT,
)

__author__ = "mori"

import re

# 避免使用通配符导入，显式导入需要的异常类
from .core.CompileError import (
    GrammarError,
    LACK_MAIN_DECL,
    UNEXPECTED_END,
    MULTIPLE_DECL,
    LACK_INT,
    LACK_ID,
    LACK_SEMI,
    LACK_RIGHT_BRACE,
    LACK_RIGHT_SQUARE,
    LACK_LEFT_BRACE,
    DISALLOW_STATEMENT,
    UNRECOGNIZED_STATEMENT,
    LACK_CASE,
    LACK_COLON,
)
from .core.GrammarTree import GrammarTree as Tree
from .core.signary import Scope

LOGIC_RE = "^([<>!=]=)|&{2}|\\|{2}|[<>]$"  # 匹配逻辑运算符 <= >= != == < > || &&


def new_scope(func):  # func为被包装的方法
    """
    包装器，用于为需要新建符号表的节点创建符号表以及符号表回溯，部分规则需要单独实现
    """

    def inner_wrapper(self, *args, **kwargs):
        self.new_scope()  # 创建新的作用域（符号表）
        result = func(self, *args, **kwargs)  # 执行被包装的方法
        self.scope_back()  # 作用域回溯
        return result

    return inner_wrapper


def tree_builder(node_name):
    """
    包装器，用于每个节点的建树、语法树回溯操作
    """

    def wrapper(func):  # func为被包装的方法
        def inner_wrapper(self, *args, **kwargs):
            self.tree.new_node(node_name, self.line_num)
            result = func(self, *args, **kwargs)
            assert node_name == self.tree.now_node.value
            self.tree.back()
            return result

        return inner_wrapper

    return wrapper


class GrammarAnalyse:
    """
    语法分析主类
    """

    def __init__(self, file_in):
        self.file_in = open(file_in, "r", encoding="utf-8")  # 打开单词流文件
        self.line_num = 1  # 初始化行号
        self.word_type = ""  # 初始化读取字符
        self.word_value = ""
        self.scope_id = 0
        self.now_scope = None
        self.__new_scope()  # 初始化作用域
        self.__backtrace_queue = Queue()  # 回溯队列
        self.tree = None  # 初始化语法树

    def __check_word(
        self, to_pair, error_str, where, dynamic_name="", read=True, node=True
    ):
        """
        校验字符串
        """
        if read:
            self.__read_word()  # 读单词
        if self.word_type != to_pair:
            raise GrammarError(self.line_num, where, error_str)
        node_name = (
            dynamic_name.format(self.word_value) if dynamic_name else self.word_type
        )
        if node:
            self.tree.new_leaf(node_name, self.line_num)  # 节点名加入语法树

    def program(self):
        """
        1. 分析规则：<program>::=<declaration_list>{fun_declaration}<main_declaration>
        <程序> => <全局变量>{<函数声明>}<主函数>
        """
        self.tree = Tree("<程序>")  # 建树
        self.__read_word()
        if self.word_type == "int":
            self.__declaration_list()  # 全局变量声明
        while self.word_type == "function":
            self.__fun_declaration()  # 分析函数声明
        if not self.word_type == "main":
            raise GrammarError(self.line_num, "<程序>", LACK_MAIN_DECL)
        self.__main_declaration()  # 分析主函数
        if self.word_type is not None:
            raise GrammarError(
                self.line_num, "<程序>", UNEXPECTED_END.format(self.word_value)
            )

    @tree_builder("<函数声明>")
    def __fun_declaration(self):
        """
        2. 分析规则： <fun_declaration>::=function ID(<arguments_list>)<function_body>
        <函数声明>=>function <标识符>()<函数体>
        """
        self.tree.new_leaf(self.word_value, self.line_num)  # function节点
        self.__check_word("ID", LACK_FUNCTION_NAME, "<函数声明>", "ID  {0}")  # 读函数名
        if self.now_scope.put(self.word_value, "function"):
            raise GrammarError(
                self.line_num, "<函数声明>", MULTIPLE_DECL.format(self.word_value)
            )
        self.__check_word("(", LACK_LEFT_PARE, "<函数声明>")  # 读取左括号
        self.__new_scope()  # 为参数列表创建单独的一级作用域
        self.__read_word()  # 读取参数列表
        self.__argument_list()  # 参数列表
        self.__check_word(")", LACK_RIGHT_PARE, "<函数声明>", read=False)  # 检查右括号
        self.__check_word("{", LACK_FUNCTION_BODY, "<函数声明>", node=False)  # 检查{
        self.__function_body()  # 分析函数体
        self.now_scope = self.now_scope.previous  # 作用域回溯

    @tree_builder("<参数列表>")
    def __argument_list(self):
        """
        2.1 读取规则 <argument_list>::=<argument_stat>{, <argument_stat>}|ε
        <参数列表> => {参数声明{,参数声明}}
        """
        if self.word_type == ")":
            return  # 参数列表为空
        self.__check_word("int", LACK_INT, "<参数列表>", read=False, node=False)
        self.__argument_stat()  # 读取参数声明
        while self.word_type == ",":
            self.tree.new_leaf(",", self.line_num)
            self.__read_word()
            self.__argument_stat()

    @tree_builder("<参数声明>")
    def __argument_stat(self):
        """
        2.2 读取规则 <argument_stat>::=int ID
        <参数声明> => int 标识符
        """
        self.tree.new_leaf("int", self.line_num)
        self.__check_word("ID", LACK_ID, "<参数声明>", "ID  {0}")  # 读取标识符
        if self.now_scope.put(self.word_value, "int"):  # 插入当前作用域
            raise GrammarError(
                self.line_num, "<参数声明>", MULTIPLE_DECL.format(self.word_value)
            )
        self.__read_word()  # 后续字符

    @tree_builder("<主函数>")
    def __main_declaration(self):
        """
        3. 分析规则： <main_declaration>::=main()<function_body>
        <主函数>=>main()<函数体>
        """
        self.tree.new_leaf(self.word_value, self.line_num)
        self.__check_word("(", LACK_LEFT_PARE, "<主函数>")  # 读取左圆括号
        self.__check_word(")", LACK_RIGHT_PARE, "<主函数>")  # 读取右圆括号
        self.__read_word()
        self.__function_body()

    @tree_builder("<函数体>")
    def __function_body(self):
        """
        4. 分析规则： <function_body>::={<declaration_list><statement_list>}
        <函数体> => {<声明序列><语句序列>}
        """
        self.tree.new_leaf("{", self.line_num)  # 插入叶节点
        self.__read_word()  # 读取下一句
        self.__declaration_list()  # 分析声明序列
        self.__statement_list()  # 分析语句序
        self.__check_word("}", LACK_RIGHT_BRACE, "<函数体>", read=False)  # 读取}
        self.__read_word()  # 读取后续字符

    @tree_builder("<return语句>")
    def __return_stat(self):
        """
        4.1 分析规则： <return_stat>=>return <expression_stat>
        <return语句> => return <表达式语句>
        """
        self.tree.new_leaf("return", self.line_num)
        self.__read_word()
        self.__expression()  # 表达式语句分析
        self.__check_word(";", LACK_SEMI, "<return语句>", read=False)  # 读取}
        self.__read_word()

    @tree_builder("<声明序列>")
    def __declaration_list(self):
        """
        5. 分析规则：<declaration_list>::=<declaration_list><declaration_stat>|ε
        <声明序列> => <声明序列><声明语句>|ε
        改写规则：<declaration_list>::=(<declaration_state>}
        """
        while self.word_type == "int":
            self.__declaration_stat()  # 声明语句

    @tree_builder("<声明语句>")
    def __declaration_stat(self):
        """
        6. 分析规则：<declaration_stat>::=int ID;
        <声明语句> => int <标识符>;
        规则扩充：<declaration_stat> => <单一声明语句>[{,<单一声明语句>}];
        """
        self.tree.new_leaf(self.word_value, self.line_num)  # 插入叶节点
        self.__read_word()  # 读取下一句
        self.__simple_declaration()  # 单一语句声明
        while self.word_type == ",":
            self.tree.new_leaf(",", self.line_num)
            self.__read_word()  # 读取下一句
            self.__simple_declaration()  # 单一语句声明
        self.__check_word(";", LACK_SEMI, "<声明语句>", read=False)  # check ';'
        self.__read_word()  # 读取下一组

    @tree_builder("<单一声明语句>")
    def __simple_declaration(self):
        """
        6.1 单一变量声明语句分析：<simple_declaration>::=ID[=<bool>]|ID[NUM][=<array_init>]
        """
        # check ID
        self.__check_word("ID", LACK_ID, "<单一声明语句>", "ID  {0}", read=False)
        id_name = self.word_value
        self.__read_word()
        if self.word_type == "=":
            self.tree.new_leaf("=", self.line_num)
            self.__read_word()
            self.__bool_expr()
        elif self.word_type == "[":  # 数组声明
            self.tree.new_leaf("[", self.line_num)
            self.__check_word("NUM", LACK_NUM, "<单一声明语句>", "NUM  {0}")  # 读取NUM
            self.__check_word("]", LACK_RIGHT_SQUARE, "<单一声明语句>")  # 读取]
            self.__read_word()
            if self.word_type == "=":
                self.tree.new_leaf("=", self.line_num)
                self.__array_init()
            if self.now_scope.put(id_name, "array"):  # 插入当前作用域，array
                raise GrammarError(
                    self.line_num, "<单一声明语句>", MULTIPLE_DECL.format(id_name)
                )
            return
        if self.now_scope.put(id_name, "int"):  # 插入当前作用域，int
            raise GrammarError(
                self.line_num, "<单一声明语句>", MULTIPLE_DECL.format(id_name)
            )

    @tree_builder("<数组初始化语句>")
    def __array_init(self):
        """
        6.2 数组元素初始化语句：<array_init_stat>::={{<表达式>{,<表达式>}}}
        """
        self.__check_word("{", LACK_LEFT_BRACE, "<数组初始化语句>")
        self.__read_word()
        if self.word_type == "}":
            self.tree.new_leaf("}", self.line_num)
            self.__read_word()
            return  # 列表为空
        self.__bool_expr()  # 读取参数声明
        while self.word_type == ",":
            self.tree.new_leaf(",", self.line_num)
            self.__read_word()
            self.__bool_expr()
        self.__check_word("}", LACK_RIGHT_BRACE, "<数组初始化语句>", read=False)
        self.__read_word()

    @tree_builder("<语句序列>")
    def __statement_list(self, read_con_bre=False):
        """
        7. 分析规则：<statement_list>::=<statement_list><statement>|ε
        <语句序列> => <语句序列><语句>|ε
        改写规则<statement_list>::={statement}
        """
        while (
            self.word_type != "}"
            and self.word_type != "case"
            and self.word_type != "default"
        ):  # 以FOLLOW集元素为结束标志
            self.__statement(read_con_bre)

    @tree_builder("<语句>")
    def __statement(self, read_con_bre=False):
        """
        8. 分析规则<statement>::=<if_stat>|<while_stat>|<do_while_stat>|
            <for_stat>|<read_stat>|<write_stat>|<compound_stat>|<expression_stat>|<break_continue_stat>
        <语句> => <if语句>|<while语句>|<do-while语句>|<for语句>|<read语句>|<write语句>|<复合语句>|<表达式语句>|<switch语句>
        调用语句处理为因子，因为普通语句的话，无法使用返回值
        """
        if self.word_type is None:
            raise GrammarError(
                self.line_num, "<语句>", UNEXPECTED_END.format("程序可能不完整")
            )
        elif self.word_type == "if":
            self.__if_stat()  # IF语句分析
        elif self.word_type == "while":
            self.__while_stat()  # while语句分析
        elif self.word_type == "do":
            self.__do_while()  # do-while语句分析
        elif self.word_type == "for":
            self.__for_stat()  # for语句分析
        elif self.word_type == "write":
            self.__write_expr()  # write语句分析
        elif self.word_type == "read":
            self.__read_expr()  # read语句分析
        elif self.word_type == "{":
            self.__compound_stat(
                read_con_bre
            )  # 分析复合语句,根据表达式语句的FIRST集合进行判定
        elif (
            self.word_type == "ID"
            or self.word_type == "NUM"
            or self.word_type == "("
            or self.word_type == ";"
            or self.word_type == "call"
        ):
            self.__expression_stat()  # 分析表达式语句
        elif self.word_type == "return":
            self.__return_stat()  # 读取返回语句
        elif self.word_type == "break" or self.word_type == "continue":
            if read_con_bre:
                self.__break_continue()  # 读取break语句
            else:  # 非法的break、continue
                raise GrammarError(
                    self.line_num, "<语句>", DISALLOW_STATEMENT.format(self.word_type)
                )
        elif self.word_type == "switch":
            self.__switch_stat()  # 读取switch语句
        else:
            raise GrammarError(
                self.line_num, "<语句>", UNRECOGNIZED_STATEMENT.format(self.word_type)
            )

    @tree_builder("<break、continue语句>")
    def __break_continue(self):
        """
        8.1 分析break、continue语句 <break_continue> ::= break;
        """
        self.tree.new_leaf(self.word_value, self.line_num)
        self.__check_word(";", LACK_SEMI, "<break、continue语句>")
        self.__read_word()

    @tree_builder("<switch语句>")
    def __switch_stat(self):
        """
        8.2 分析规则<switch_stat>::=switch(<expression>){{<case语句>}{<default语句>}}
        """
        self.tree.new_leaf("switch", self.line_num)
        self.__check_word("(", LACK_LEFT_PARE, "<switch语句>")  # 检查(
        self.__read_word()
        self.__expression()  # 分析表达式
        self.__check_word(")", LACK_RIGHT_PARE, "<switch语句>", read=False)  # 检查)
        self.__check_word("{", LACK_LEFT_BRACE, "<switch语句>")  # 检查{
        self.__check_word("case", LACK_CASE, "<switch语句>", node=False)  # 检查case
        while self.word_type == "case":
            self.__case_stat()  # 分析case语句
        if self.word_type == "default":
            self.__default_stat()  # 分析default语句
        self.__check_word("}", LACK_RIGHT_BRACE, "<switch语句>", read=False)  # 检查}
        self.__read_word()

    @tree_builder("<case语句>")
    def __case_stat(self):
        """
        8.2.1 分析规则：<case_stat>::=case NUM:<statement_list>
        """
        self.tree.new_leaf(self.word_value, self.line_num)
        self.__check_word("NUM", LACK_NUM, "<case语句>", "NUM  {0}")  # 读取NUM
        self.__check_word(":", LACK_COLON, "<case语句>")
        self.__read_word()
        self.__statement_list(True)  # 分析语句序列

    @tree_builder("<default语句>")
    def __default_stat(self):
        """
        8.2.2 分析规则：<default_stat>::=default:<statement_list>
        """
        self.tree.new_leaf(self.word_value, self.line_num)
        self.__check_word(":", LACK_COLON, "<default语句>")
        self.__read_word()
        self.__statement_list(True)  # 分析语句序列

    @tree_builder("<if语句>")
    def __if_stat(self):
        """
        9. 分析规则 <if_stat>::=if(<expression>)<statement>[else<statement>]
        <if语句> => if(<表达式>)<语句>[else<语句>]
        """
        self.tree.new_leaf(self.word_value, self.line_num)
        self.__check_word("(", LACK_LEFT_PARE, "<if语句>")  # 读左括号
        self.__read_word()
        self.__expression()  # expression语句分析
        self.__check_word(")", LACK_RIGHT_PARE, "<if语句>", read=False)  # 检查右括号
        self.__read_word()
        self.__statement()  # statement语句分析
        if self.word_type == "else":  # 如果有else语句，没有不报错
            self.tree.new_leaf("else", self.line_num)
            self.__read_word()  # 预读字符
            self.__statement()  # statement语句分析

    @tree_builder("<while语句>")
    def __while_stat(self):
        """
        10. 分析规则 <while_stat>::=while(<expression>)<statement>
        <while> => (<表达式>)<语句>
        """
        self.tree.new_leaf(self.word_value, self.line_num)
        self.__check_word("(", LACK_LEFT_PARE, "<while语句>")  # 读左括号
        self.__read_word()
        self.__expression()  # expression语句分析
        self.__check_word(")", LACK_RIGHT_PARE, "<while语句>", read=False)  # 检查右括号
        self.__read_word()  # 读取后续字符
        self.__statement(True)  # statement语句分析

    @tree_builder("<for语句>")
    def __for_stat(self):
        """
        11. 分析规则<for_stat>::=for(<expression>;<expression>;<expression>)<statement>
        <for语句> => for(<表达式>;<表达式>;<表达式>)<语句>
        """
        self.tree.new_leaf(self.word_value, self.line_num)
        self.__check_word("(", LACK_LEFT_PARE, "<for语句>")  # 读左括号
        self.__read_word()
        self.__expression()  # 第一个表达式
        self.__check_word(";", LACK_SEMI, "<for语句>", read=False)  # 检查逗号
        self.__read_word()
        self.__expression()  # 第二个表达式
        self.__check_word(";", LACK_SEMI, "<for语句>", read=False)  # 检查逗号
        self.__read_word()
        self.__expression()  # 第三个表达式
        self.__check_word(")", LACK_RIGHT_PARE, "<for语句>", read=False)  # 检查右括号
        self.__read_word()
        self.__statement(True)  # 分析循环体

    @tree_builder("<write语句>")
    def __write_expr(self):
        """
        12. 分析语句 <write_expr>::=write<expression>
        <write语句> => write<表达式>
        """
        self.tree.new_leaf(self.word_value, self.line_num)
        self.__read_word()  # 读取expression开始字符
        self.__expression()
        self.__check_word(";", LACK_SEMI, "<write语句>", read=False)
        self.__read_word()  # 读取后续字符

    @tree_builder("<read语句>")
    def __read_expr(self):
        """
        13. 分析语句 <read_expr>::=read ID;
        <read语句> => read <标识符>;
        """
        self.tree.new_leaf(self.word_value, self.line_num)
        self.__check_word("ID", LACK_ID, "<read语句>", "ID:[{0}]", node=False)  # 读取ID
        self.__id_stat()  # 读取标识符表达式
        self.__check_word(";", LACK_SEMI, "<read语句>", read=False)  # 读取;
        self.__read_word()  # 读取到正确的标识符，读取后续字符

    @tree_builder("<复合语句>")
    def __compound_stat(self, read_con_bre=False):
        """
        14. 分析语句 <compound>::={<statement_list>}
        <复合语句> => {<语句序列>}
        """
        self.tree.new_leaf("{", self.line_num)
        self.__read_word()  # 读取语句序列开始字符
        self.__statement_list(read_con_bre)  # 分析语句序列
        self.__check_word("}", LACK_RIGHT_BRACE, "<复合语句>", read=False)
        self.__read_word()  # 读取后续字符

    @tree_builder("<表达式语句>")
    def __expression_stat(self):
        """
        15. 分析规则 <expression_stat>::=<expression>;|;
        <表达式语句> => <表达式>;|;
        """
        if self.word_type == ";":
            self.tree.new_leaf(";", self.line_num)
            self.__read_word()
            return
        self.__expression()
        self.__check_word(";", LACK_SEMI, "<表达式语句>", read=False)
        self.__read_word()  # 读取后续字符

    @tree_builder("<call语句>")
    def __call_stat(self):
        """
        16. 分析规则：<call_stat>::=call ID({<call_arguments>})
        <call语句> => call<标识符>({<实参列表>})
        """
        self.tree.new_leaf("call", self.line_num)
        self.__check_word("ID", LACK_ID, "<call语句>", "ID  {0}")  # 读取ID
        self.__check_id_scope("<call语句>")  # 检查作用域
        self.__check_word("(", LACK_LEFT_PARE, "<call语句>")  # 检查(
        self.__read_word()
        if self.word_type != ")":
            self.__call_arguments()
            self.__check_word(
                ")", LACK_RIGHT_PARE, "<call语句>", read=False, node=False
            )  # 检查)
        self.tree.new_leaf(")", self.line_num)
        self.__read_word()  # 预读

    @tree_builder("<实参列表>")
    def __call_arguments(self):
        """
        16.1 分析规则：<call_arguments> => <expression>{,<expression>}
        <实参列表> => <表达式>{,<表达式>}|空
        """
        self.__expression()  # 读取参数声明
        while self.word_type == ",":
            self.tree.new_leaf(",", self.line_num)
            self.__read_word()
            self.__expression()

    @tree_builder("<表达式>")
    def __expression(self):
        """
        17. 分析规则 <expression>::=ID=<bool_expr>|<bool_expr>
        <表达式> => ID=<布尔表达式>|<布尔表达式>
        """
        if self.word_type == "ID":
            identifier_name = self.word_value
            index = self.__id_stat()
            if self.word_type == "=":
                self.__read_word()
                self.tree.new_leaf("=", self.line_num)
            else:  # 状态回溯，因为bool_expr可能是单独的标识符，这里的重叠导致回溯
                if index == -1:
                    self.__add_backtrace(
                        self.word_type, self.word_value
                    )  # 回溯，当前已读的数据，如果回溯深度只有一层，则可以不使用队列
                    self.word_type = "ID"
                    self.word_value = identifier_name  # 回溯第二层
                else:
                    self.__add_backtrace("[", "[")
                    self.__add_backtrace("NUM", index)
                    self.__add_backtrace("]", "]")
                    self.__add_backtrace(
                        self.word_type, self.word_value
                    )  # 遇到数组时的回溯
                    self.word_type = "ID"
                    self.word_value = identifier_name  # 回溯第二层
                self.tree.delete_node()  # 语法树剪枝
        self.__bool_expr()  # bool_expr语句分析

    @tree_builder("<布尔表达式>")
    def __bool_expr(self):
        """
        18. 分析规则 <bool_expr>::=<additive>|<additive_expr>(>|<|>=|<=|==|!=|&&|||<additive>)
        <布尔表达式> => <算术表达式>|<算术表达式>(> < >= <= == != && ||<算术表达式>)
        """
        self.__additive_expr()  # additive语句分析
        if re.match(LOGIC_RE, self.word_type):
            self.tree.new_leaf(self.word_value, self.line_num)
            self.__read_word()
            self.__additive_expr()  # additive语句分析

    @tree_builder("<do-while语句>")
    def __do_while(self):
        """
        19. 分析规则 <do_while_stat> => do<statement>while(<expression>);
        <do-while语句> => do<语句>while<表达式>
        """
        self.tree.new_leaf("do", self.line_num)
        self.__read_word()
        self.__statement(True)
        self.__check_word(
            "while", LACK_WHILE, "<do-while语句>", read=False
        )  # 检查while
        self.__check_word("(", LACK_LEFT_PARE, "<do-while语句>")  # 读取(
        self.__read_word()
        self.__expression()
        self.__check_word(")", LACK_RIGHT_PARE, "<do-while语句>", read=False)  # 检查)
        self.__check_word(";", LACK_SEMI, "<do-while语句>")  # 读取;
        self.__read_word()

    @tree_builder("<算术表达式>")
    def __additive_expr(self):
        """
        20. 分析规则 <additive_expr>::=<term>{(+|-)<term>}
        <算术表达式> => <项> {(+|-)<项>}
        """
        self.__term()  # term 语句分析
        while self.word_type == "+" or self.word_type == "-":
            self.tree.new_leaf(self.word_value, self.line_num)
            self.__read_word()  # 预读字符
            self.__term()  # term 语句分析

    @tree_builder("<项>")
    def __term(self):
        """
        21. 分析规则 <term>::=<factor>{(*|/)<factor>}
        <项> => <因子>{(*|/)<因子>}
        """
        self.__factor()  # 因子语句分析
        while self.word_type == "*" or self.word_type == "/":
            self.tree.new_leaf(self.word_type, self.line_num)
            self.__read_word()  # 预读字符
            self.__factor()  # 因子语句分析

    @tree_builder("<因子>")
    def __factor(self):
        """
        22. 分析规则 <factor>::=(<expression>)|NUM|<call_stat>|<ID_stat>
        <因子> => (<表达式>)|<无符号整数>|<call语句>|
        """
        if self.word_type == "(":
            self.tree.new_leaf("(", self.line_num)
            self.__read_word()
            self.__expression()
            self.__check_word(")", LACK_RIGHT_PARE, "<因子>", read=False)
            self.__read_word()
            return
        elif self.word_type == "call":
            self.__call_stat()  # 读取调用语句
            return
        elif not (self.word_type == "NUM" or self.word_type == "ID"):
            raise GrammarError(self.line_num, "<因子>", LACK_OPERAND)
        elif self.word_type == "ID":
            self.__id_stat()  # 标识符语句
            return
        self.tree.new_leaf(
            "{0}  {1}".format(self.word_type, self.word_value), self.line_num
        )
        self.__read_word()

    @tree_builder("<标识符语句>")
    def __id_stat(self):
        """
        22.1 标识符语句 <ID_stat>::=ID|ID[NUM]
        """
        self.tree.new_leaf(
            "{0}  {1}".format(self.word_type, self.word_value), self.line_num
        )
        index = -1
        self.__check_id_scope("标识符语句")
        self.__read_word()
        if self.word_type == "[":  # 数组声明
            self.tree.new_leaf("[", self.line_num)
            self.__check_word("NUM", LACK_NUM, "<标识符语句>", "NUM  {0}")  # 读取NUM
            index = self.word_value
            self.__check_word("]", LACK_RIGHT_SQUARE, "<标识符语句>")  # 读取]
            self.__read_word()
        return index  # 数组下标

    def __read_word(self):
        """
        读取单词，处理多读取的换行符，并进行行号统计、作用域处理
        :return: 是否读到字符，读到文件末尾时返回FALSE
        """
        if not self.__backtrace_queue.empty():  # 读取回溯队列
            now_line = self.__backtrace_queue.get()
            self.word_type = now_line[0]
            self.word_value = now_line[1]
            return True
        now_line = self.file_in.readline()
        while now_line == "[enter]\n":
            self.line_num += 1  # 遇到换行标记
            now_line = self.file_in.readline()  # 读下一行
        if now_line == "":
            self.word_type = self.word_value = None
            return False
        else:
            word_list = now_line.split()  # 切分并处理换行符
            self.word_type = word_list[0]  # 单词类别
            if self.word_type == "{":
                self.__new_scope()  # 读取到'{'，创建新的作用域
            elif self.word_type == "}":
                previous = self.now_scope.previous
                if previous is None:  # 已经回退到顶级作用域
                    raise GrammarError(self.line_num, "<程序>", UNEXPECTED_END)
                self.now_scope = previous  # 读取到'}'，返回上移作用域
            self.word_value = word_list[1]  # 单词值
            return True

    def __add_backtrace(self, word_type, word_value):
        """
        创建回溯元素
        """
        self.__backtrace_queue.put((word_type, word_value))

    def close(self):
        self.file_in.close()  # 关闭打开的文件

    def __new_scope(self):
        """
        新建作用域
        """
        self.now_scope = Scope(self.now_scope, self.scope_id)
        self.scope_id += 1

    def __check_id_scope(self, where):
        """
        标识符作用域检查
        """
        if self.word_type != "ID":
            raise RuntimeError("不是标识符类型，无法进行作用域检查")
        scope = self.now_scope.get_scope_str(self.word_value)
        if scope is None:  # 作用域为None，说明没有声明
            raise GrammarError(
                self.line_num, where, NO_STATEMENT.format(self.word_value)
            )
