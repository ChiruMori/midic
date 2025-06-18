# 符号表，栈式符号表管理
__author__ = 'mori'


class Scope:
    """
    作用域类，符号表操作
    """

    def __init__(self, previous, scope_id, offset=False, start_add=0):
        self.previous = previous  # 上一层作用域
        self.scope_id = scope_id  # 作用域编号，仅用于识别
        self.table = {}  # 标识符表
        self.now_index = start_add  # 符号表内部命令栈标记
        self.offset = offset

    def get_by_id(self, id_name):
        """
        查表，会持续向上级作用域查找，直到找到
        :param id_name: id
        :return: 地址，没有值返回None
        """
        now_scope = self
        while now_scope:
            temp_val = now_scope.table.get(id_name)
            if temp_val:
                return temp_val
            else:
                now_scope = now_scope.previous
        return None

    def get_scope_str(self, id_name):
        """
        :return: 返回当前标识符所在作用域的字符串表示 TODO 弃用这个
        """
        scope_str = None
        now_scope = self
        while now_scope:
            temp_val = now_scope.table.get(id_name)
            if temp_val is not None:
                scope_str = now_scope.scope_id.__str__()
                now_scope = now_scope.previous
                break
            else:
                now_scope = now_scope.previous
        if scope_str:
            while now_scope:
                scope_str = now_scope.scope_id.__str__() + '-' + scope_str
                now_scope = now_scope.previous
        return scope_str

    def put(self, key, value, size=0, address=''):
        """
        插入符号表
        :param key: 变量名
        :param value: 变量类型
        :param size: 数组长度，参数列表长度
        :param address: 指令起始位置
        :return 是否冲突
        """
        use_address = ":{}".format(self.now_index)
        if self.table.get(key):
            return True  # 同一作用域重复插入
        if value == 'function':
            self.table[key] = (address, value, size)
            return False
        if size:
            self.table[key] = (use_address if self.offset else use_address[1:], value, size)  # 为数组分配地址
            self.now_index += (size - 1)  # 地址索引后移指定长度
        else:
            self.table[key] = (use_address if self.offset else use_address[1:], value)  # 为变量分配地址、保存变量的类型，元组表示
        self.now_index += 1  # 地址+1
        return False
