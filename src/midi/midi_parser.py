# 每个调都基于 8 个音阶进行识别，映射为 8 位 ASCII 编码
# 第一位取 C4（60） 或 C4#（61）
key_dict = {
    "Cb": [59, 61, 63, 64, 66, 68, 70, 71],
    "Abm": [59, 61, 63, 64, 66, 68, 70, 71],
    "Gb": [59, 61, 63, 65, 66, 68, 70, 71],
    "Ebm": [59, 61, 63, 65, 66, 68, 70, 71],
    "Db": [60, 61, 63, 65, 66, 68, 70, 72],
    "Bbm": [60, 61, 63, 65, 66, 68, 70, 72],
    "Ab": [60, 61, 63, 65, 67, 68, 70, 72],
    "Fm": [60, 61, 63, 65, 67, 68, 70, 72],
    "Eb": [60, 62, 63, 65, 67, 68, 70, 72],
    "Cm": [60, 62, 63, 65, 67, 68, 70, 72],
    "Bb": [60, 62, 63, 65, 67, 69, 70, 72],
    "Gm": [60, 62, 63, 65, 67, 69, 70, 72],
    "F": [60, 62, 64, 65, 67, 69, 70, 72],
    "Dm": [60, 62, 64, 65, 67, 69, 70, 72],
    "C": [60, 62, 64, 65, 67, 69, 71, 72],
    "Am": [60, 62, 64, 65, 67, 69, 71, 72],
    "G": [60, 62, 64, 66, 67, 69, 71, 72],
    "Em": [60, 62, 64, 66, 67, 69, 71, 72],
    "D": [61, 62, 64, 66, 67, 69, 71, 73],
    "Bm": [61, 62, 64, 66, 67, 69, 71, 73],
    "A": [61, 62, 64, 66, 68, 69, 71, 73],
    "F#m": [61, 62, 64, 66, 68, 69, 71, 73],
    "E": [61, 63, 64, 66, 68, 69, 71, 73],
    "C#m": [61, 63, 64, 66, 68, 69, 71, 73],
    "B": [61, 63, 64, 66, 68, 70, 71, 73],
    "G#m": [61, 63, 64, 66, 68, 70, 71, 73],
    "F#": [61, 63, 65, 66, 68, 70, 71, 73],
    "D#m": [61, 63, 65, 66, 68, 70, 71, 73],
    "C#": [61, 63, 65, 66, 68, 70, 72, 73],
    "A#m": [61, 63, 65, 66, 68, 70, 72, 73],
}


def from_char(key: str, c: str) -> list[int]:
    """
    将字符转换为音符
    字符处理为 8 位 ASCII 码，即转为整数，取最低 8 位
    """
    if key not in key_dict:
        raise ValueError(f"Invalid key: {key}")
    if len(c) != 1:
        raise ValueError(f"Invalid character: {c}")
    valid_bits = ord(c) & 0b11111111
    res = []
    for i, note in enumerate(key_dict[key]):
        if valid_bits & (1 << i):
            res.append(note)
    return res


def to_char(key: str, notes: list[int]) -> str:
    """
    将音符转换为字符
    音符列表转为整数低 8 位，处理为 ASCII 码对应字符
    """
    if key not in key_dict:
        raise ValueError(f"Invalid key: {key}")
    if len(notes) > 8:
        raise ValueError(f"Invalid notes: {notes}")
    valid_bits = 0
    for i, note in enumerate(key_dict[key]):
        if note in notes:
            valid_bits |= 1 << i
    return chr(valid_bits)


def get_score_bit(key: str, note: int) -> int:
    if key not in key_dict:
        raise ValueError("Invalid key signature")
    alphabet = key_dict[key]
    for i, a_note in enumerate(alphabet):
        if a_note == note:
            return 1 << i
    # 不在音符表，忽略
    return 0
