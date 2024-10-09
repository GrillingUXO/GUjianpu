# -*- coding: utf-8 -*-
import os
import tkinter as tk
from tkinter import filedialog, messagebox
from music21 import converter, chord, note, stream
import tempfile
from dotenv import load_dotenv
import musicpy as mp

load_dotenv()

# 标准音符到简谱数字的映射
JIANPU_PITCH_MAP = {
    'C': '1', 'D': '2', 'E': '3', 'F': '4',
    'G': '5', 'A': '6', 'B': '7'
}

# 升降号映射
ACCIDENTALS = {
    1: '♯', 
    -1: '♭', 
}

def open_file_dialog():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="选择要处理的 MIDI 文件",
        filetypes=[
            ("MIDI 文件", "*.mid *.MID"),
            ("所有文件", "*.*")
        ]
    )
    return file_path

def tolerance_selection():
    """创建一个窗口，用于通过滑块选择旋律、和弦及旋律音级的容许阈值。"""
    root = tk.Tk()
    root.title("选择容许阈值")

    tk.Label(root, text="旋律归类容许阈值 (melody tolerance)").pack(padx=10, pady=5)
    melody_slider = tk.Scale(root, from_=6, to=18, orient='horizontal', label="小七度 = 10 (默认)")
    melody_slider.set(10)
    melody_slider.pack(padx=10, pady=5)

    tk.Label(root, text="和弦归类容许阈值 (chord tolerance)").pack(padx=10, pady=5)
    chord_slider = tk.Scale(root, from_=1, to=12, orient='horizontal', label="大六度 = 9 (默认)")
    chord_slider.set(9)
    chord_slider.pack(padx=10, pady=5)

    tk.Label(root, text="旋律音级容许阈值 (melody degree tolerance)").pack(padx=10, pady=5)
    melody_degree_slider = tk.Scale(root, from_=60, to=80, orient='horizontal', label="默认值 B4 = 71")
    melody_degree_slider.set(71)
    melody_degree_slider.pack(padx=10, pady=5)

    def on_submit():
        root.quit()

    tk.Button(root, text="确定", command=on_submit).pack(padx=10, pady=10)

    root.mainloop()

    return melody_slider.get(), chord_slider.get(), melody_degree_slider.get()

def extract_melody_with_musicpy(midi_file, melody_tol, chord_tol, melody_degree_tol):
    try:
        # 使用 musicpy 读取并合并 MIDI 文件
        piece, bpm, start_time = mp.read(midi_file).merge()

        # 使用 melody_tol, chord_tol, 和 melody_degree_tol 进行旋律分离
        melody_chord = piece.split_melody(
            mode='chord',
            melody_tol=melody_tol,
            chord_tol=chord_tol,
            melody_degree_tol='B4'  # 固定为字符串 'B4'
        )
        if not isinstance(melody_chord, mp.chord):
            raise ValueError(f"split_melody 返回了意外的结果: {type(melody_chord)}")

        # 写入临时的 MIDI 文件
        temp_midi_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mid')
        mp.write(melody_chord, bpm, name=temp_midi_file.name)
        return temp_midi_file.name

    except Exception as e:
        raise ValueError(f"旋律解析错误: {str(e)}")

def select_parts(score):
    parts = score.parts
    part_ids = [part.id for part in parts]
    part_names = [part.partName if part.partName else f"声部 {i+1}" for i, part in enumerate(parts)]

    selected_parts = []
    selected_part_ids = []

    def on_submit():
        selected_indices = listbox.curselection()
        for i in selected_indices:
            selected_parts.append(parts[i])
            selected_part_ids.append(part_ids[i])
        root.quit()
        root.destroy()

    root = tk.Tk()
    root.title("选择声部")
    tk.Label(root, text="请选择要转换的声部：").pack(padx=10, pady=10)

    listbox = tk.Listbox(root, selectmode='multiple', width=50)
    for name in part_names:
        listbox.insert(tk.END, name)
    listbox.pack(padx=10, pady=5)

    tk.Button(root, text="确定", command=on_submit).pack(padx=10, pady=10)

    root.mainloop()

    if not selected_parts:
        messagebox.showerror("选择错误", "未选择任何有效的声部。")

    return selected_parts, selected_part_ids

def convert_note_to_jianpu(m21_note):
    """将 music21 的音符或休止符转换为简谱符号。"""
    # 休止符
    if isinstance(m21_note, note.Rest):
        quarter_length = m21_note.duration.quarterLength
        dots = m21_note.duration.dots

        # 映射休止符时值
        if quarter_length == 4.0:
            rest_notation = '0000'
        elif quarter_length == 2.0:
            rest_notation = '00'
        elif quarter_length == 1.0:
            rest_notation = '0'
        elif quarter_length == 0.5:
            rest_notation = '0̱'
        elif quarter_length == 0.25:
            rest_notation = '0̳'
        elif quarter_length == 0.125:
            rest_notation = '0̹'
        elif quarter_length == 0.0625:
            rest_notation = '0̺'
        else:
            rest_notation = '0'  # 默认休止符

        # 附点休止符
        if dots == 1:
            rest_notation += '·'
        elif dots == 2:
            rest_notation += '··'

        return rest_notation

    step = m21_note.pitch.step
    octave = m21_note.pitch.octave
    alter = m21_note.pitch.accidental.alter if m21_note.pitch.accidental else 0
    quarter_length = m21_note.duration.quarterLength
    dots = m21_note.duration.dots

    if alter == 1:
        step += '♯'
    elif alter == -1:
        step += '♭'

    # 将音名转换为简谱数字
    base_step = step[0]  # 从 'C♯' 或 'C♭' 中提取 'C'
    jianpu_number = JIANPU_PITCH_MAP.get(base_step, '')

    # 添加升降号
    if len(step) > 1:
        jianpu_number = ACCIDENTALS.get(alter, '') + jianpu_number

    # 添加八度标记
    if octave < 4:
        jianpu_number = jianpu_number + '̣' * (4 - octave)
    elif octave > 4:
        jianpu_number = jianpu_number + '̇' * (octave - 4)

    # 调整时值
    if quarter_length == 0.5:
        jianpu_number += '̱'
    elif quarter_length == 0.25:
        jianpu_number += '̳'
    elif quarter_length == 0.125:
        jianpu_number += '̹'
    elif quarter_length == 0.0625:
        jianpu_number += '̺'
    elif quarter_length == 4.0:
        jianpu_number += "  -  -  -"
    elif quarter_length == 2.0:
        jianpu_number += "  -"
    elif quarter_length == 1.0:
        jianpu_number += ''

    # 附点音符
    if dots == 1:
        jianpu_number += '·'
    elif dots == 2:
        jianpu_number += '··'

    return jianpu_number

def get_chord_root_or_bass(chrd):
    """
    使用 music21 的和弦分析功能提取和弦的根音。
    如果是已知和弦，则根据和弦类型提取根音。否则，返回和弦的最低音（即低音）。
    """
    if isinstance(chrd, chord.Chord):
        try:
            root_note = chrd.root()
            if root_note:
                return note.Note(root_note)
        except Exception:
            pass
        bass_note = chrd.bass()
        return note.Note(bass_note)
    else:
        raise ValueError("输入必须是 music21 和弦对象。")

def convert_chord_to_jianpu(m21_chord):
    root_note = get_chord_root_or_bass(m21_chord) 
    return convert_note_to_jianpu(root_note) 

def process_selected_parts(score, selected_parts, output_txt_file, melody_tol, chord_tol, output_melody_midi_file):
    """将选中的声部转换为简谱符号。"""
    try:
        melody_stream = stream.Part()  # 用于保存主旋律的音符
        with open(output_txt_file, 'w', encoding='utf-8') as jianpu_file:
            jianpu_file.write("简谱转换结果:\n")

            # 遍历所选的声部
            for part in selected_parts:
                part_name = part.partName if part.partName else f"声部 {part.id}"
                jianpu_file.write(f"\n声部: {part_name}\n")
                measures = part.getElementsByClass(stream.Measure)
                measure_jianpu = []

                for i, measure in enumerate(measures, start=1):
                    measure_content = []
                    notes = measure.notes

                    for element in notes:
                        if isinstance(element, chord.Chord):
                            jianpu_notation = convert_chord_to_jianpu(element)
                            melody_note = get_chord_root_or_bass(element) 
                        elif isinstance(element, note.Note):
                            jianpu_notation = convert_note_to_jianpu(element)
                            melody_note = element
                        elif isinstance(element, note.Rest):
                            jianpu_notation = convert_note_to_jianpu(element)
                            melody_note = element 

                        measure_content.append(jianpu_notation)
                        melody_stream.append(melody_note) 

                    # 组合该小节的简谱符号，音符之间用空格分隔
                    measure_str = ' '.join(measure_content)
                    measure_jianpu.append(f"|  {measure_str}  |")
                    if i % 2 == 0:
                        jianpu_file.write('    '.join(measure_jianpu) + '\n\n\n')
                        measure_jianpu = []  # 两小节重置

                # 写入剩余的小节，并在小节之间用四个空格分隔
                if measure_jianpu:
                    jianpu_file.write('    '.join(measure_jianpu) + '\n\n\n')

        # 保存主旋律为 MIDI 文件
        melody_stream.write('midi', fp=output_melody_midi_file)

        messagebox.showinfo("成功", f"简谱已保存为 {output_txt_file}，主旋律MIDI已保存为 {output_melody_midi_file}")

    except Exception as e:
        messagebox.showerror("错误", f"处理文件时出错: {e}")
        print(f"Error: {e}")

def main():
    input_midi = open_file_dialog()
    if not input_midi:
        messagebox.showinfo("提示", "未选择任何文件。")
        return

    try:
        melody_tol, chord_tol, melody_degree_tol = tolerance_selection()  # 获取用户选择的容许阈值

        temp_midi = extract_melody_with_musicpy(input_midi, melody_tol, chord_tol, melody_degree_tol)
    except Exception as e:
        messagebox.showerror("错误", f"无法提取主旋律: {e}")
        return

    try:
        score = converter.parse(temp_midi)
    except Exception as e:
        messagebox.showerror("错误", f"无法解析临时 MIDI 文件: {e}")
        return
    selected_parts, selected_part_ids = select_parts(score)
    if not selected_parts:
        return

    output_txt_file = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("文本文件", "*.txt")])
    output_melody_midi_file = filedialog.asksaveasfilename(defaultextension=".mid", filetypes=[("MIDI 文件", "*.mid")])

    if output_txt_file and output_melody_midi_file:
        process_selected_parts(score, selected_parts, output_txt_file, melody_tol, chord_tol, output_melody_midi_file)
    else:
        messagebox.showinfo("提示", "未选择任何保存路径。")

if __name__ == "__main__":
    main()
