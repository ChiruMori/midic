# 主控程序
import os
import sys
from .core.compile_error import TestRuntimeError

__author__ = 'mori'

from .core import lexical, compile_error as CE
from .core import grammar, semantic, machine


def main(midi_path: str):
    lexical_exe = lexical.LexicalAnalyse(midi_path)  # 打开文件
    lexical_file = lexical_exe.analyse()  # 进行词法分析，得到单词流文件
    lexical_exe.close()  # 关闭文件

    try:
        # 语法分析：要求整理出识别的错误
        grammar_exe = grammar.GrammarAnalyse(lexical_file)  # 打开词法分析结果文件
        grammar_exe.program()  # 开始语法分析
        grammar_exe.close()  # 关闭文件
        grammar_exe.tree.print_tree()  # 打印语法树

        # 语义分析与中间代码生成
        semantic_exe = semantic.Semantic(grammar_exe.tree)  # 初始化语义分析程序
        semantic_file = semantic_exe.program()  # 开始语法分析
        semantic_exe.close()  # 关闭相关文件

        # 执行中间代码
        machine_exe = machine.Machine(semantic_file)  # 初始化虚拟机
        machine_exe.execute()  # 执行
    except CE.CompileError as e:
        e.print()
    except TestRuntimeError as e:
        e.print()


if __name__ == '__main__':
    # 从命令行参数中获取MIDI文件路径
    midi_path = sys.argv[1]
    # 检查文件是否存在
    if not os.path.isfile(midi_path):
        print(f"错误：文件 '{midi_path}' 不存在")
        sys.exit(1)
    # 检查文件是否为MIDI文件
    if not midi_path.endswith('.mid'):
        print(f"错误：文件 '{midi_path}' 不是MIDI文件")
        sys.exit(1)
    # 执行主函数
    main(midi_path)
