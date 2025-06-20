# 把 midi 文件当字符流来读取
from mido import MidiFile

__author__ = "mori"


def get_score_bit(key: str, note: int) -> int:
    if key not in key_dict:
        raise ValueError("Invalid key signature")
    alphabet = key_dict[key]
    for i, note in enumerate(alphabet):
        if note == note:
            return 1 << i
    # 不在音符表，忽略
    return 0


class MidiReader:
    def __init__(self, file_in: str):
        self.filepath = file_in
        self.msg_index = 0
        self.key_signature = "C"
        self.file = MidiFile(self.filepath)
        self.track = self.file.tracks[0]
        self.msg_index = 0
        # 获得 Track 调性
        while self.track[0][self.msg_index].type != "key_signature":
            self.msg_index += 1
        self.key_signature = self.track[0][self.msg_index].key

    def has_msg(self):
        # 轨道为空，空midi文件
        if len(self.track) == 0:
            return False
        # 音符栈有未解析的音符，说明还有音符没有结束
        if len(self.note_stack) > 0:
            return True
        # 音符栈没有音符，说明所有音符都已经结束
        # 查找下一个音符的开始位置，忽略 velocity 为 0 的音符（仅考虑音符开始的时间）
        while (
            self.track[0][self.msg_index].type != "note_on"
            or self.track[0][self.msg_index].velocity == 0
        ):
            self.msg_index += 1
            if self.msg_index >= len(self.track):
                return False
        return True

    def __iter__(self):
        self.msg_index = 0
        return self

    def __next__(self):
        code = 0
        only_zero_time = False
        # 查找下一个音符的开始位置，如果音符的 time 为 0，除第一个音符以外，均需要和前一个音符合并
        while self.has_msg() and (
            not only_zero_time or self.track[0][self.msg_index].time == 0
        ):
            now_code = get_score_bit(
                self.key_signature, self.track[0][self.msg_index].note
            )
            code |= now_code
            only_zero_time = True
        # TODO: code 转 ASCII
        return code
