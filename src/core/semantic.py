# 语义分析程序，只包含语义，没有语法检查
from .core.CompileError import MULTIPLE_CASE, ERROR_ARGUMENTS_LIST, NOT_AN_ARRAY, NOT_CALLABLE

__author__ = 'mori'

import re

from .core.signary import Scope
from .core.grammar import LOGIC_RE, SemanticError, INDEX_ERROR

OPERATOR_DIC = {  # 运算符与命令对应的字典
    '>': 'GT',
    '>=': 'GE',
    '<': 'LES',
    '<=': 'LE',
    '==': 'EQ',
    '!=': 'NOTEQ',
    '||': 'OR',
    '&&': 'AND',
    '+': 'ADD',
    '-': 'SUB',
    '*': 'MULT',
    '/': 'DIV'
}


def shift(debug, num=1):
    """
    包装器，用于每条规则的字符预读
    """
    def wrapper(func):  # func为被包装的方法
        def inner_wrapper(self, *args, **kwargs):
            assert self.now_node.value == debug  # 节点检查，调试使用
            self.node_shift(num)
            return func(self, *args, **kwargs)
        return inner_wrapper
    return wrapper


class Semantic:
    """
    语义分析类
    """

    LABEL_INDEX = 0  # 起始标号，类静态变量

    def __init__(self, tree, file_out='semantic.tfs'):
        self.tree = tree  # 要分析的语法树
        self.now_scope = self.now_node = None  # 初始化符号表
        self.scope_id = 0
        self.out_file = open(file_out, 'w+', encoding='utf-8')
        self.out_filename = file_out  # 保存输出文件名
        self.node_shift()  # 初始化读取语法树节点
        self.new_scope()  # 初始化作用域
        self.__break_label = self.__continue_label = None
        self.now_command = ''  # 当前写入的命令
        self.__return_address = ''  # 返回空间地址
        self.choke_cmd = ''  # 被阻塞的指令
        self.chock = False  # 阻塞指令输出流

    @shift('<程序>')  # 读取下一个节点、略过<程序>节点
    def program(self):
        """
        1. 语义分析入口 <程序>
        """
        start_add = 0
        if self.now_node.value == '<声明序列>':
            start_add = self.__declaration_list()
        main_label = self.__get_label()  # main函数标记
        self.__file_write('BR', main_label)
        while self.now_node.value == '<函数声明>':
            self.__fun_declaration()
        self.__file_write('label', main_label)
        if self.now_node.value == '<主函数>':
            self.__main_declaration(start_add)
        self.__file_write('STOP')
        print('编译通过\n')
        return self.out_filename  # 返回输出文件名

    @shift('<函数声明>', 2)
    def __fun_declaration(self):
        """
        规则2
        执行时每次调用，创建新的栈，每一个函数为一个子程序
        """
        self.static_address = self.now_scope.now_index  # 记录静态地址
        fun_name = self.now_node.value.split()[1]  # 函数名
        fun_local = self.__get_label()  # 指令起始位置
        self.__file_write('label', fun_local)  # 写入函数开始标记
        self.chock = True  # 阻塞命令输出流
        self.node_shift(2)  # 跳过ID (
        self.new_scope(True)  # 函数作用域（符号表）
        self.now_scope.put('return', 'return')  # 分配return空间
        self.__return_address = self.now_scope.get_by_id('return')[0]  # 记录返回地址
        par_num = self.__argument_list()  # 读取参数列表
        self.now_scope.previous.put(fun_name, 'function', par_num, fun_local)  # 插入外部符号表
        self.node_shift(debug='\\)')
        decl_num = self.__function_body(False)  # 函数体
        self.chock = False  # 解除阻塞
        self.__file_write('ALLOCATE', par_num+decl_num+1)  # 记录必须的静态内存（参数表、声明序列、返回值区域）
        self.__file_write('RET', self.now_scope.get_by_id('return')[0])  # 返回值处理
        self.scope_back()  # 作用域回退

    @shift('<参数列表>')
    def __argument_list(self):
        par_len = 0
        arg_cmd_list = []
        if self.now_node.value == '<参数声明>':
            arg_cmd_list.append(self.__argument_stat())
            par_len = 1
        while self.now_node.value == ',':
            self.node_shift()
            par_len += 1
            arg_cmd_list.append(self.__argument_stat())
        while arg_cmd_list:
            self.__file_write('dir', arg_cmd_list.pop())
        return par_len

    @shift('<参数声明>', 2)
    def __argument_stat(self):
        now_arg = self.now_node.value.split()[1]  # 获取形参名
        self.now_scope.put(now_arg, 'int')
        to_write = "    {0:10}{1}\n    POP\n".format('STO', self.now_scope.get_by_id(now_arg)[0])
        self.node_shift()  # 预读
        return to_write

    @shift('<主函数>', 4)  # 规则3
    def __main_declaration(self, start_add):
        self.chock = True  # 阻塞输出
        main_data = self.__function_body(True, start_add)  # 下移三个节点，分别为main ( )，并读取下一个节点必为<函数体>
        self.chock = False  # 解除阻塞
        main_data += start_add
        self.__file_write('ALLOCATE', 1 if main_data == 0 else main_data)  # 为主函数及全局声明语句申请空间

    @shift('<函数体>', 2)  # 规则4，略去<函数体>节点，同时预读一个节点
    def __function_body(self, new_scope=True, start_add=0):
        if new_scope:
            self.new_scope(start_add=start_add)
        decl_count = self.__declaration_list()
        self.__statement_list()
        self.node_shift(1)  # 略过 }
        if new_scope:
            self.scope_back()
        return decl_count

    @shift('<return语句>', 2)  # 4.1
    def __return_stat(self):
        self.__expression()
        self.node_shift(debug=';')
        self.__file_write('STO', self.__return_address)
        self.__file_write('POP')

    @shift('<声明序列>')  # 规则5
    def __declaration_list(self):
        if self.now_node.value != '<声明语句>':
            self.__warn('声明序列中没有声明语句')
        decl_count = 0  # 声明计数
        while self.now_node.value == '<声明语句>':
            decl_count += self.__declaration_stat()
        return decl_count  # 返回声明的总数

    @shift('<声明语句>', 2)  # 规则6，这里略过<声明语句> int
    def __declaration_stat(self):
        decl_count = self.__simple_declaration()  # 单一声明语句
        while self.now_node.value != ';':
            self.node_shift()  # 跳过','
            decl_count += self.__simple_declaration()
        self.node_shift()  # 跳过';'
        return decl_count  # 返回声明的个数

    @shift('<单一声明语句>')  # 规则6.1
    def __simple_declaration(self):
        now_id = self.now_node.value.split()[1]  # 获取变量名
        self.node_shift()
        if self.now_node.value == '=':  # 普通声明赋值
            self.now_scope.put(now_id, 'int')  # 加入符号表
            self.node_shift()
            self.__bool_expr()
            self.__file_write('STO', self.now_scope.get_by_id(now_id)[0])  # 写入赋值命令
            self.__file_write('POP')
            return 1
        elif self.now_node.value == '[':  # 数组的情况
            self.node_shift()  # 跳过'['
            array_size = int(self.now_node.value.split()[1])  # 获取数组长度
            self.now_scope.put(now_id, 'array', array_size)  # 数组加入符号表
            self.node_shift(2)  # 跳过']'，并预读
            if self.now_node.value == '=':
                self.node_shift()  # 数组初始化语句
                self.__array_init(now_id)
            # else:  # 为数组填充0
            #     self.__fill0(self.now_scope.get_by_id(now_id)[0], array_size)
            return array_size
        else:
            self.now_scope.put(now_id, 'int')  # 加入符号表
            # self.__fill0(self.now_scope.get_by_id(now_id)[0])
            return 1

    @DeprecationWarning
    def __fill0(self, address, num=1):
        # 向指定地址及后续地址填充指定个0
        for offset in range(0, num):
            self.__file_write('LOADI', '0')
            self.__file_write('STO', address, offset)
            self.__file_write('POP')

    @shift('<数组初始化语句>')  # 规则6.2，跳过节点 <数组初始化语句>
    def __array_init(self, array_name):
        arr_data = self.now_scope.get_by_id(array_name)  # 获取数组符号表数据
        arr_size = arr_data[2]  # 数组长度
        arr_add = arr_data[0]  # 数组起始地址
        offset = 0  # 地址偏移
        while self.now_node.value != '}':
            self.node_shift()  # 跳过','和初始的'{'
            self.__bool_expr()  # 读取表达式
            if offset < arr_size:  # 栈顶写入数组对应位置的地址
                self.__file_write('STO', arr_add, offset)
                self.__file_write('POP')  # 用完移除
            else:
                self.__file_write('POP')  # 多余的数据，从栈顶去除
                self.__warn('数组赋值语句存在多余的数据')
            offset += 1  # 数组赋值地址向下偏移
        self.node_shift()  # 预读
        while offset < arr_size:  # 填充数组结尾的0
            self.__file_write('LOADI', '0')  # 设初始值为0
            self.__file_write('STO', arr_add, offset)
            self.__file_write('POP')
            offset += 1

    @shift('<语句序列>')  # 规则7
    def __statement_list(self):
        if self.now_node.value != '<语句>':
            self.__warn('语句序列中没有语句')
            return
        while self.now_node.value == '<语句>':
            self.__statement()  # 分析语句

    @shift('<语句>')  # 规则8
    def __statement(self):
        node_name = self.now_node.value
        if node_name == '<if语句>':
            self.__if_stat()
        elif node_name == '<while语句>':
            self.__while_stat()
        elif node_name == '<for语句>':
            self.__for_stat()
        elif node_name == '<write语句>':
            self.__write_expr()
        elif node_name == '<read语句>':
            self.__read_expr()
        elif node_name == '<复合语句>':
            self.__compound_stat()
        elif node_name == '<表达式语句>':
            self.__expression_stat()
        elif node_name == '<call语句>':
            self.__call_stat()
        elif node_name == '<return语句>':
            self.__return_stat()
        elif node_name == '<break、continue语句>':
            self.__break_continue()
        elif node_name == '<switch语句>':
            self.__switch_stat()
        elif node_name == '<do-while语句>':
            self.__do_while()
        else:
            raise RuntimeError('无法识别的语句', node_name)

    @shift('<break、continue语句>')  # 规则8.1
    def __break_continue(self):
        assert self.__break_label is not None or self.__continue_label is not None
        if self.now_node.value == 'break':
            self.__file_write('BR', self.__break_label)
        else:
            self.__file_write('BR', self.__continue_label)
        self.node_shift(2)  # 预读

    @shift('<switch语句>', 3)  # 规则8.2，略过switch (
    def __switch_stat(self):
        end_label = self.__get_label()  # 结束语句，break转跳使用
        self.__break_label = end_label
        exist_num = {}  # 已有条件字典
        self.__expression()
        exp_command = self.now_command  # 保存指定命令
        self.node_shift(2)  # 读取){
        [next_start_label, next_statement_label] = self.__case_stat(None, None, None, exist_num)  # 第一个case
        while self.now_node.value == '<case语句>':
            [next_start_label, next_statement_label] = \
                self.__case_stat(exp_command, next_start_label, next_statement_label, exist_num)
        self.__file_write('label', next_start_label)
        self.__file_write('label', next_statement_label)
        if self.now_node.value == '<default语句>':
            self.__default_stat()
        self.__file_write('label', end_label)
        self.node_shift(debug='\\}')

    @shift('<case语句>', 2)  # 规则8.2.1
    def __case_stat(self, load_cmd, start, statement, exist_dic):
        """
        规则8.2.1
        :param load_cmd: 加载比较数命令，为None时不进行处理
        :param start: 条件语句标号
        :param statement: 语句标号
        :return: 下一条条件语句标号，下一条语句标号
        """
        next_start = self.__get_label()  # 下调语句条件
        next_statement = self.__get_label()  # 下调语句体
        if start:
            self.__file_write('label', start)  # 设置起始位置标号
        if load_cmd:
            self.__file_write('dir', load_cmd)  # 直接写入读取命令
        num = self.now_node.value.split()[1]  # 用于判断的数字
        if exist_dic.get(num):
            raise SemanticError(self.now_node.line_num, '<case语句>', MULTIPLE_CASE)
        else:
            exist_dic[num] = True
        self.__file_write('LOADI', num)  # 写入数字
        self.__file_write('EQ')  # 比较是否相等
        self.__file_write('BRF', next_start)  # 不相等进入下一条判断
        if statement:
            self.__file_write('label', statement)  # 设置语句标号
        self.node_shift(2)  # 读取下一节点，跳过':'
        self.__statement_list()  # 读取语句序列
        self.__file_write('BR', next_statement)  # 直接转入下条语句
        return [next_start, next_statement]

    @shift('<default语句>', 3)  # 规则8.2.2，跳过default :
    def __default_stat(self):
        self.__statement_list()  # 读取语句序列

    @shift('<if语句>', 3)  # 规则9，略过if (
    def __if_stat(self):
        self.__expression()  # 分析表达式
        else_label = self.__get_label()
        end_label = self.__get_label()
        self.__file_write('BRF', else_label)  # 假条件转移
        self.node_shift(debug='\\)')  # 略过')'
        self.__statement()  # 读取语句
        self.__file_write('BR', end_label)  # 无条件转移
        self.__file_write('label', else_label)  # 写入标号
        if self.now_node.value == 'else':
            self.node_shift()  # 跳过else
            self.__statement()  # else语句块
        self.__file_write('label', end_label)  # 结束标号

    @shift('<while语句>', 3)  # 规则10，略过while (
    def __while_stat(self):
        start_label = self.__get_label()  # 起始标记
        end_label = self.__get_label()  # 结束标记
        self.__file_write('label', start_label)  # 写入起始标记
        self.__expression()  # 分析表达式
        self.__file_write('BRF', end_label)  # 假条件转移
        self.node_shift(debug='\\)')  # 读取)
        self.__break_label = end_label
        self.__continue_label = start_label
        self.__statement()  # 分析语句
        self.__file_write('BR', start_label)  # 无条件转移
        self.__file_write('label', end_label)  # 写入结束标记

    @shift('<for语句>', 3)  # 规则11，略过for (
    def __for_stat(self):
        label12 = self.__get_label()
        label24 = self.__get_label()
        label43 = self.__get_label()
        end_label = self.__get_label()  # 获取4个标号
        self.__expression()  # 表达式1
        self.node_shift(debug=';')  # 读取分号
        self.__file_write('label', label12)  # 写入标号1~2
        self.__expression()  # 表达式2
        self.node_shift(debug=';')  # 读取分号
        self.__file_write('BRF', end_label)  # 为假跳出循环，转移到末尾
        self.__file_write('BR', label24)  # 为真转入循环体
        self.__file_write('label', label43)  # 写入标号4~3
        self.__expression()  # 表达式3
        self.node_shift(debug='\\)')  # 读取')'
        self.__file_write('BR', label12)  # 转入循环起点
        self.__file_write('label', label24)  # 写入标号3~4
        self.__break_label = end_label
        self.__continue_label = label43
        self.__statement()  # 读取语句，即循环体
        self.__file_write('BR', label43)  # 转入判断语句前
        self.__file_write('label', end_label)  # 写入结束标号

    @shift('<write语句>', 2)  # 规则12，跳过'write'
    def __write_expr(self):
        self.__expression()  # 分析表达式
        self.__file_write('OUT')  # 写命令
        self.node_shift()  # 跳过;

    @shift('<read语句>', 2)  # 规则13，跳过'read'
    def __read_expr(self):
        address = self.__id_stat(True)  # 标识符语句寻址
        self.__file_write('IN')  # 读命令
        self.__file_write('STO', address)  # 保存到指定地址
        self.__file_write('POP')  # 操作数出栈
        self.node_shift()  # 跳过;

    @shift('<复合语句>', 2)  # 规则14，跳过'{
    def __compound_stat(self):
        self.__statement_list()  # 读取语句序列
        self.node_shift(debug='\\}')  # 预读

    @shift('<表达式语句>')  # 规则15
    def __expression_stat(self):
        if self.now_node.value == ';':
            self.node_shift()
        else:
            self.__expression()  # 不接受返回值时结果直接出栈
            self.__file_write('POP')  # 出栈
        self.node_shift()  # 预读字符（跳过';'）

    @shift('<call语句>', 2)  # 规则16
    def __call_stat(self):
        fun_name = self.now_node.value.split()[1]  # 获取函数名
        fun_data = self.now_scope.get_by_id(fun_name)  # (LABEL、function、参数列表长度)
        if not fun_data[1] == 'function':
            raise SemanticError(self.now_node.line_num, '<call语句>', NOT_CALLABLE.format(fun_name))
        self.node_shift(2)
        if self.now_node.value == ')' and fun_data[2]:  # 没有参数列表、且形参列表不为空
            raise SemanticError(self.now_node.line_num, '<call语句>', ERROR_ARGUMENTS_LIST)
        if self.now_node.value != ')':  # 参数列表不为空，读取实参列表
            self.__call_arguments(fun_data[2])  # 实参列表
        self.node_shift(debug='\\)')
        self.__file_write('JSR', fun_data[0])

    @shift('<实参列表>')
    def __call_arguments(self, arg_len):
        self.__expression()
        real_arg_len = 1
        while self.now_node.value == ',':
            self.node_shift()
            self.__expression()
            real_arg_len += 1
        if arg_len is not real_arg_len:
            raise SemanticError(self.now_node.line_num, '<实参列表>', ERROR_ARGUMENTS_LIST)

    @shift('<表达式>')  # 规则17
    def __expression(self):
        if self.now_node.value == '<标识符语句>':
            address = self.__id_stat(True)  # 标识符语句，寻址
            if self.now_node.value == '=':
                self.node_shift()
                self.__bool_expr()  # 布尔表达式
                self.__file_write('STO', address)  # 数据存储命令
        else:
            self.__bool_expr()  # 布尔表达式

    @shift('<布尔表达式>')  # 规则18
    def __bool_expr(self):
        self.__additive_expr()
        if re.match(LOGIC_RE, self.now_node.value):
            logic_ope = self.now_node.value  # 暂存操作符，逻辑运算符包含 <= >= != == < > || &&
            self.node_shift()  # 跳过运算符
            self.__additive_expr()
            self.__file_write(OPERATOR_DIC[logic_ope])  # 操作符翻译后写入文件

    @shift('<do-while语句>', 2)  # 规则19，跳过do
    def __do_while(self):
        start_label = self.__get_label()
        end_label = self.__get_label()
        self.__continue_label = start_label
        self.__break_label = end_label
        self.__file_write('label', start_label)  # 开始标记
        self.__statement()  # 循环体
        self.node_shift(2, '^while$')  # 读取while、（
        self.__expression()  # 条件表达式
        self.__file_write('BRF', end_label)  # 为假则退出循环
        self.__file_write('BR', start_label)  # 否则进入循环体
        self.__file_write('label', end_label)  # 结束标记
        self.node_shift(2, debug='\\)')  # 跳过 );

    @shift('<算术表达式>')  # 规则20
    def __additive_expr(self):
        self.__term()
        while self.now_node.value == '+' or self.now_node.value == '-':
            operator = self.now_node.value
            self.node_shift()  # 跳过运算符
            self.__term()
            self.__file_write(OPERATOR_DIC[operator])  # 写入加减命令

    @shift('<项>')  # 规则21
    def __term(self):
        self.__factor()
        while self.now_node.value == '*' or self.now_node.value == '/':
            operator = self.now_node.value
            self.node_shift()  # 跳过运算符
            self.__factor()
            self.__file_write(OPERATOR_DIC[operator])  # 写入乘除命令

    @shift('<因子>')  # 规则22
    def __factor(self):
        if self.now_node.value == '(':
            self.node_shift()  # 略过'('
            self.__expression()
            self.node_shift(debug='\\)')  # 略过')'，预读
        elif self.now_node.value[:3] == 'NUM':
            num = self.now_node.value.split()[1]  # 读取NUM后的数字
            self.__file_write('LOADI', num)  # 常量写入文件
            self.node_shift()  # 预读
        elif self.now_node.value == '<call语句>':
            self.__call_stat()  # 函数调用语句
        elif self.now_node.value == '<标识符语句>':
            self.__id_stat()  # 标识符语句
        else:
            raise RuntimeError('当前节点未成功回溯', self.now_node.value)  # 测试使用

    @shift('<标识符语句>')
    def __id_stat(self, seek=False):
        """
        规则21.1
        :param seek: 是否只寻址，为真时返回地址，默认为假
        """
        var_name = self.now_node.value.split()[1]
        self.node_shift(debug='^ID')
        id_info = self.now_scope.get_by_id(var_name)  # 获取变量地址或数组首地址
        address = id_info[0]
        offset_flag = False
        if address[0] == ':':  # 进行类型修正
            address = address[1:]
            offset_flag = True
        address = int(address)
        if self.now_node.value == '[':
            self.node_shift()  # 略过作方括号
            num = int(self.now_node.value.split()[1])  # 读取NUM后的数字
            if id_info[1] != 'array':
                raise SemanticError(self.now_node.line_num, '<标识符语句>', NOT_AN_ARRAY.format(var_name))
            if num >= id_info[2]:
                raise SemanticError(self.now_node.line_num, '<标识符语句>', INDEX_ERROR.format(id_info[2]-1, num))
            self.node_shift(2)  # 略过右方括号并预读
            address += num  # 计算指定位置
        if offset_flag:
            address = ':{}'.format(address)
        else:
            address = str(address)
        if seek:
            return address
        self.__file_write('LOAD', address)  # 寻址结果写入文件

    def __file_write(self, command, data='', offset=0):
        """
        命令写入文件
        :param command: 指令
        :param data: 指令数据，is_label为真时，data表示label的标号
        """
        if command == 'label':  # 写入标号语句
            real_command = data + ':\n'
        elif command == 'dir':  # 直接写入
            real_command = data
        else:
            if command == 'STO' and self.now_scope.offset and offset:
                if data[0] == ':':
                    data = ':' + str(int(data[1]) + offset)
                else:
                    data = str(int(data) + offset)
            if offset:
                data = int(data) + offset
            real_command = "    {0:10}{1}\n".format(command, data)  # 写入普通指令语句
        self.now_command = real_command
        if self.chock:  # 命令阻塞状态
            self.choke_cmd += real_command  # 拼接命令
        else:
            self.out_file.write(real_command)  # 写入当前命令
            if self.choke_cmd:  # 含有阻塞的命令
                self.out_file.write(self.choke_cmd)  # 写入阻塞的命令
                self.choke_cmd = ''

    def close(self):
        self.out_file.close()  # 关闭输出文件

    def new_scope(self, offset=False, start_add=0):
        """
        新建作用域
        """
        self.now_scope = Scope(self.now_scope, self.scope_id, offset, start_add)
        self.scope_id += 1

    def node_shift(self, num=1, debug=''):
        """
        从语法树中下移指定数量节点
        :param num:  下移的数量
        :param debug: 调试时使用正则表达式
        """
        if debug:
            assert re.match(debug, self.now_node.value)
        while num:
            self.now_node = self.tree.next_node()
            # if self.now_node is not None:
            #     print('|'*self.now_node.depth, self.now_node.value)  # 输出读取的节点，用于判断分析过程
            num -= 1

    def scope_back(self):
        """
        作用域回溯，回溯至顶级则报错
        """
        previous = self.now_scope.previous  # 作用域回溯
        if previous is None:  # 已经回退到顶级作用域
            raise RuntimeError('已退至顶级作用域')
        self.now_scope = previous

    def __warn(self, info):
        """
        打印警告信息
        """
        print('\033[1;33;m警告：第[{0}]行附近，{1}\033[0m'.format(self.now_node.line_num, info))

    @staticmethod
    def __get_label():
        """
        获取标号
        :return: 标号，字符串表示，比如LABEL1
        """
        Semantic.LABEL_INDEX += 1
        return 'LABEL{}'.format(Semantic.LABEL_INDEX)
