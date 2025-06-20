__author__ = 'mori'


class GrammarTree:
    """
    语法树类，完成语法树的构建与输出 TODO 行号拓展
    """

    def __init__(self, root):
        self.now_node = self.root = Node(root, None, 1)  # 初始化根节点并进入根节点
        self.iterator = None  # 初始化迭代器

    def new_node(self, val, line_num):
        """
        新建并进入子节点
        :param val: 子节点名
        :param line_num: 行号
        """
        new_node = Node(val, self.now_node, line_num)  # 创建子节点
        self.now_node.sons.append(new_node)  # 插入新节点
        self.now_node = new_node  # 进入子节点

    def new_leaf(self, val, line_num):
        """
        新建并插入叶节点到当前节点
        :param val: 子节点名
        :param line_num: 行号
        """
        self.now_node.sons.append(Node(val, self.now_node, line_num, True))  # 插入叶节点

    def back(self):
        """
        返回上一级节点
        """
        if self.now_node.parent is None:
            raise RuntimeError('已回溯至根节点，无法继续回溯')
        self.now_node = self.now_node.parent

    def print_tree(self):
        """
        打印语法树，深度优先搜索
        """
        out_file = open('out/grammar.o', 'w+', encoding='utf-8')  # 初始化语法树输出文件
        print_all(self.root, out_file)
        if self.now_node is not self.root:
            raise RuntimeError("语法树未回溯至根节点，请检查语法结构")

    def delete_node(self):
        """
        从当前节点的子节点栈中删除一个节点，深度回溯时将导致错误
        """
        self.now_node.sons.pop()

    def next_node(self):
        """
        迭代器指针移动到下一个节点，可以为叶子节点，或者分支接点
        """
        if self.iterator is None:  # 开始迭代，从根节点开始
            self.iterator = self.root
        elif self.iterator.iter_index < len(self.iterator.sons):  # 迭代子节点数组
            now_index = self.iterator.iter_index
            self.iterator.iter_index += 1  # 迭代索引下移
            self.iterator = self.iterator.sons[now_index]  # 移到带下一个节点
        else:
            self.iterator = self.iterator.parent  # 回溯
            if self.iterator:
                return self.next_node()  # 递归回溯，支持循环迭代
            else:
                return None
        return self.iterator

    @DeprecationWarning
    def last_node(self):
        """
        迭代器返回到上一个节点，启用
        """
        if self.iterator.parent is None:
            self.iterator = None
            return None  # 回溯到顶节点，再次回溯则报错
        if self.iterator.parent.iter_index <= 1:  # 返回到本层首节点
            self.iterator = self.iterator.parent  # 回溯一次
            self.iterator.iter_index -= 1
        else:  # 普通情况
            parent = self.iterator.parent  # 本层父节点
            parent.iter_index -= 1  # 父节点索引回退
            result = parent.sons[parent.iter_index - 1]
            while not result.leaf:
                result.iter_index -= 1  # 移动索引到结尾
                result = result.sons[result.iter_index]  # 移到本层尾节点
            self.iterator = result
        return self.iterator


class Node:
    """
    节点类
    """

    def __init__(self, value, parent, line_num, leaf=False):
        self.leaf = leaf  # 是否叶子节点
        self.value = value  # 节点显示名
        self.sons = []  # 后代节点
        self.parent = parent  # 父节点
        self.line_num = line_num
        self.depth = 0 if parent is None else parent.depth + 1   # 节点深度，父节点+1或0
        self.iter_index = 0  # 迭代到的子节点栈索引，供语法树的迭代器使用

    def print_node(self, out_file):
        """
        打印当前节点
        """
        node_type = '\033[4;33;0m▷·· ' if self.leaf else '\033[4;35;0m▼~'  # 控制台输出
        # print("\033[0;36;0m| " * self.depth, node_type, self.value, sep='')  # 备用字符 TODO 控制台输出语法树
        node_type = '▷·· ' if self.leaf else '▼~'  # 文件输出
        out_file.write("| " * self.depth+node_type + self.value + '\n')


def print_all(now_node, out_file):
    """
    递归输出子树结构，深度优先搜索
    :param now_node: 子树根节点
    :param out_file: 输出文件
    """
    now_node.print_node(out_file)
    for index, item in enumerate(now_node.sons):
        print_all(item, out_file)
