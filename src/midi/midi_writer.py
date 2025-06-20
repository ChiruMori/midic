from os import name
import sys
from mido import MetaMessage, MidiFile, MidiTrack, Message

from .midi_parser import from_char

__author__ = "mori"


class MidiWriter:
    def __init__(self, input_file: str, output_file: str, tempo=500000):
        self.output_file = output_file
        self.input_file = input_file

    def _init_track(self, signature="C"):
        # 逐个字符解析，并添加到 track
        track = MidiTrack()
        track.append(MetaMessage("track_name", name="Piano", time=0))
        track.append(MetaMessage("key_signature", key=signature, time=0))
        track.append(
            MetaMessage(
                "time_signature",
                numerator=4,
                denominator=4,
                clocks_per_click=24,
                notated_32nd_notes_per_beat=8,
                time=0,
            )
        )
        track.append(MetaMessage("set_tempo", tempo=750000, time=0))
        track.append(Message("control_change", channel=0, control=121, value=0, time=0))
        track.append(Message("program_change", channel=0, program=0, time=0))
        track.append(Message("control_change", channel=0, control=7, value=100, time=0))
        track.append(Message("control_change", channel=0, control=10, value=64, time=0))
        track.append(Message("control_change", channel=0, control=91, value=0, time=0))
        track.append(Message("control_change", channel=0, control=93, value=0, time=0))
        return track

    def parse(self):
        # 读取 input_file 的文本内容
        code_content = open(self.input_file, "r").read()
        # 逐个字符解析，并添加到 track
        track = self._init_track()
        track.append(MetaMessage("midi_port", port=0, time=0))
        for c in code_content:
            notes = from_char("C", c)
            for note in notes:
                # 音符均作为 8 分音符处理
                track.append(
                    Message("note_on", channel=0, note=note, velocity=80, time=0)
                )
                track.append(
                    Message("note_on", channel=0, note=note, velocity=0, time=227)
                )
        track.append(MetaMessage("end_of_track", time=1))
        # 将 track 写入 output_file
        mid = MidiFile()
        mid.ticks_per_beat = 480
        mid.tracks.append(track)
        mid.save(self.output_file)


if __name__ == "__main__":
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    MidiWriter(input_file, output_file).parse()
