# MIDIC

将 MIDI 文件作为输入，按照类似 C 语言的语法进行编译，并在虚拟机上执行

改编自2019年的编译原理大作业（玩具而已，不必较真）

- `pip install -r requirements.txt`: 自动安装，添加 `--proxy 127.0.0.1:7890` 可以使用代理
- `pip freeze > requirements.txt`: 自动生成依赖文件