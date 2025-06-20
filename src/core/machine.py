# 虚拟机
from .compile_error import TestRuntimeError, DIVISOR_IS_0, STACK_OVERFLOW

__author__ = "mori"


class Machine:
    def __init__(self, file_in):
        self.__now_line = -1  # 语句指针
        self.__stack = []  # 栈，动态内存
        self.__data = [0] * 1000  # 静态数据，分配空间
        self.__label_dic = {}  # 标号字典，形式为：{'LABEL1': 0}
        self.__now_cmd = ""
        self.__static_top = 0
        self.__active_fun_flag = []  # 函数活动记录
        self.__return_fun_line = []  # 函数返回行号
        file = open(file_in, "r", encoding="utf-8")
        self.__code = file.read().split("\n")[:-1]  # 加载所有代码，去掉结尾空行
        self.__init_code()  # 初始化标号字典
        file.close()

    def __init_code(self):
        """
        初始化label数组，保存label编号与对应索引
        """
        for index, code in enumerate(self.__code):
            if code[:5] == "LABEL":
                self.__label_dic[code[:-1]] = index

    def __read_code(self):
        """
        指针后移，读下一条语句
        """
        self.__now_line += 1  # 跳过label
        now_code = self.__code[self.__now_line]  # 当前语句
        while now_code[:5] == "LABEL":
            self.__now_line += 1  # 跳过label
            now_code = self.__code[self.__now_line]
        self.__now_cmd = tuple(now_code.split())  # 返回语句元组

    def __addressing(self, address):
        """
        寻址，基于相对静态地址的寻址计算和直接取址
        :param address: 原始地址
        :return: 实际地址
        """
        use_address = 0
        if address[0] == ":":  # 偏移地址计算
            use_address = self.__static_top + int(address[1:])
        else:  # 直接地址
            use_address += int(address)
        return use_address

    def __true_in_1(self, flag):
        """flag为真1入栈，否则0入栈"""
        self.__stack.append(1 if flag else 0)

    def execute(self):
        """
        执行指令，总控程序，使用反射机制
        """
        self.__read_code()
        while self.__now_cmd[0] != "STOP":  # 读到结束语句
            now_function = getattr(self, "fun_" + self.__now_cmd[0].lower(), None)
            if not now_function:
                raise RuntimeError("无法识别的指令", self.__now_cmd[0])
            now_function()
            self.__read_code()  # 读取下一条命令
        print("\n程序运行结束")

    def fun_br(self):
        to_line = self.__label_dic.get(self.__now_cmd[1])
        self.__now_line = to_line

    def fun_sto(self):  # STO命令
        address = self.__now_cmd[1]  # 获取原始地址
        use_address = self.__addressing(address)  # 寻址
        use_data = self.__stack[-1]  # 取栈顶元素，不出栈
        if len(self.__data) <= use_address:
            raise TestRuntimeError(STACK_OVERFLOW)  # 可以在这里拓展数据区域
        else:
            self.__data[use_address] = use_data  # 写入指定地址单元

    def fun_load(self):  # LOAD命令
        address = self.__now_cmd[1]  # 获取原始地址
        use_address = self.__addressing(address)  # 寻址
        use_data = self.__data[use_address]  # 取出数据
        self.__stack.append(int(use_data))  # 数据压栈

    def fun_pop(self):  # POP 命令
        self.__stack.pop()

    def fun_loadi(self):  # LOADI命令
        self.__stack.append(int(self.__now_cmd[1]))

    def fun_in(self):  # 输入数据并插入栈顶
        self.__stack.append(int(input("\033[1;34m请输入数据：\t\033[0m")))

    def fun_out(self):  # 出栈并打印元素
        print("\033[1;36m程序输出：\t{}\033[0m".format(self.__stack.pop()))

    def fun_add(self):  # 出栈，数据加给次栈顶数据
        data = self.__stack.pop()
        self.__stack[-1] += data

    def fun_sub(self):  # 出栈，次栈顶数据减去出栈的数据
        data = self.__stack.pop()
        self.__stack[-1] -= data

    def fun_mult(self):  # 出栈，数据乘给次栈顶
        data = self.__stack.pop()
        self.__stack[-1] *= data

    def fun_div(self):  # 出栈，数据除次栈顶数据
        data = self.__stack.pop()
        if data == 0:
            raise TestRuntimeError(DIVISOR_IS_0)
        self.__stack[-1] /= data

    def fun_brf(self):  # 假条件转移
        if self.__stack.pop() == 0:
            to_line = self.__label_dic.get(self.__now_cmd[1])
            self.__now_line = to_line

    def fun_eq(self):  # 出栈2元素，相等1压栈，否则0压栈
        self.__true_in_1(self.__stack.pop() == self.__stack.pop())

    def fun_noteq(self):  # 出栈2元素，相等0压栈，否则1压栈
        self.__true_in_1(self.__stack.pop() != self.__stack.pop())

    def fun_gt(self):  # 出栈2元素，次栈顶大则1压栈，否则0压栈
        self.__true_in_1(self.__stack.pop() < self.__stack.pop())

    def fun_les(self):  # 出栈2元素，次栈顶小则1压栈，否则0压栈
        self.__true_in_1(self.__stack.pop() > self.__stack.pop())

    def fun_ge(self):
        self.__true_in_1(self.__stack.pop() <= self.__stack.pop())

    def fun_le(self):  # 出栈2元素，次栈顶小等于栈顶则1压栈，否则0压栈
        self.__true_in_1(self.__stack.pop() >= self.__stack.pop())

    def fun_and(self):  # 出栈2元素，次栈顶与栈顶逻辑与结果为真则1压栈，否则0压栈
        self.__true_in_1(self.__stack.pop() and self.__stack.pop())

    def fun_or(self):  # 出栈2元素，次栈顶与栈顶逻辑或结果为真则1压栈，否则0压栈
        self.__true_in_1(self.__stack.pop() or self.__stack.pop())

    def fun_not(self):  # 出栈2元素，栈顶取反结果为真则1压栈，否则0压栈
        self.__true_in_1(not self.__stack.pop())

    def fun_allocate(self):
        """函数空间请求语句"""
        size = self.__now_cmd[1]  # 获取申请的空间大小
        if self.__static_top == 0:
            self.__static_top = int(
                size
            )  # 记录新的静态数据栈顶指针（记录活动记录释放后静态空间的回溯位置、相对寻址基址）
            self.__active_fun_flag.append(0)  # 最初的活动记录
            self.__active_fun_flag.append(
                int(size)
            )  # 函数活动记录，原静态地址加上申请的空间后的指针
        else:
            self.__static_top = self.__active_fun_flag[-1]  # 更新静态数据栈顶指针
            self.__active_fun_flag.append(
                self.__static_top + int(size)
            )  # 建立在活动记录上的活动记录

    def fun_ret(self):
        """RET命令，返回语句：加载数据到返回单元，活动记录出栈"""
        self.__stack.append(self.__data[self.__static_top])  # 加载函数返回值到活动栈顶
        self.__active_fun_flag.pop()  # 活动记录出栈
        if len(self.__active_fun_flag) > 1:
            self.__static_top = self.__active_fun_flag[-2]  # 静态数据区域还原
        else:
            self.__static_top = 0  # 没有函数活动记录，静态指针指向0
        return_line = self.__return_fun_line.pop()  # 找到返回的位置
        self.__now_line = return_line  # 返回到调用的地方

    def fun_jsr(self):
        """JSR命令，调用语句"""
        self.__return_fun_line.append(self.__now_line)  # 返回位置压栈
        to_line = self.__label_dic.get(self.__now_cmd[1])  # 转到函数体
        self.__now_line = to_line
