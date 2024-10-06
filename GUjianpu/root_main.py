import os
import tkinter as tk
from tkinter import filedialog, messagebox
from music21 import converter, chord, note, stream

# Mapping from standard musical notes to Jianpu numbers
JIANPU_PITCH_MAP = {
    'C': '1', 'D': '2', 'E': '3', 'F': '4',
    'G': '5', 'A': '6', 'B': '7'
}

# Accidentals mapping
ACCIDENTALS = {
    1: '♯',
    -1: '♭',
}

def open_file_dialog():
    """Open file dialog to select MIDI or MusicXML file."""
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="选择要处理的 MIDI 或 MusicXML 文件",
        filetypes=[
            ("MIDI Files", "*.mid *.MID"),
            ("MusicXML Files", "*.xml *.musicxml"),
            ("All Files", "*.*")
        ]
    )
    return file_path

def get_chord_root_or_bass(chrd):
    """Extract root note of a chord."""
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
        raise ValueError("The input must be a music21 chord object.")

def convert_note_to_jianpu(m21_note):
    """Convert a music21 note or rest to Jianpu notation."""
    if isinstance(m21_note, note.Rest):
        return '0'  # Simplified for rests, can extend for different lengths

    step = m21_note.pitch.step
    octave = m21_note.pitch.octave
    alter = m21_note.pitch.accidental.alter if m21_note.pitch.accidental else 0

    if alter == 1:
        step += '♯'
    elif alter == -1:
        step += '♭'

    base_step = step[0]
    jianpu_number = JIANPU_PITCH_MAP.get(base_step, '')

    if len(step) > 1:
        jianpu_number = ACCIDENTALS.get(alter, '') + jianpu_number

    if octave < 4:
        jianpu_number = jianpu_number + '̣' * (4 - octave)
    elif octave > 4:
        jianpu_number = jianpu_number + '̇' * (octave - 4)

    return jianpu_number

def process_root_mode(input_file):
    """处理仅根音模式，支持 MIDI 和 MusicXML"""
    try:
        # 使用 music21 直接解析 MIDI 或 MusicXML 文件
        score = converter.parse(input_file)
        return score
    except Exception as e:
        messagebox.showerror("错误", f"解析文件时出错: {e}")
        return None

def select_parts(score):
    """Allow the user to select parts from the score for conversion."""
    parts = score.parts
    part_names = [part.partName if part.partName else f"Part {i+1}" for i, part in enumerate(parts)]

    selected_parts = []

    def on_submit():
        selected_indices = listbox.curselection()
        for i in selected_indices:
            selected_parts.append(parts[i])
        root.quit()

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

    return selected_parts

def convert_selected_parts_to_jianpu(score, selected_parts, output_txt_file, output_midi_file):
    """Convert selected parts to Jianpu and save the result."""
    try:
        melody_stream = stream.Part()  # 用于生成根音 MIDI 文件
        with open(output_txt_file, 'w', encoding='utf-8') as jianpu_file:
            jianpu_file.write("简谱转换结果:\n")

            for part in selected_parts:
                part_name = part.partName if part.partName else f"Part {part.id}"
                jianpu_file.write(f"\n声部: {part_name}\n")
                measures = part.getElementsByClass(stream.Measure)
                measure_jianpu = []

                for i, measure in enumerate(measures, start=1):
                    measure_content = []
                    notes = measure.notes

                    for element in notes:
                        if isinstance(element, chord.Chord):
                            root_note = get_chord_root_or_bass(element)
                            jianpu_notation = convert_note_to_jianpu(root_note)
                            melody_note = root_note
                        elif isinstance(element, note.Note):
                            jianpu_notation = convert_note_to_jianpu(element)
                            melody_note = element
                        elif isinstance(element, note.Rest):
                            jianpu_notation = '0'
                            melody_note = element

                        measure_content.append(jianpu_notation)
                        melody_stream.append(melody_note)

                    measure_str = ' '.join(measure_content)
                    measure_jianpu.append(f"|  {measure_str}  |")

                    # 每 4 小节分行
                    if i % 4 == 0:
                        jianpu_file.write('    '.join(measure_jianpu) + '\n\n\n')
                        measure_jianpu = []

                if measure_jianpu:
                    jianpu_file.write('    '.join(measure_jianpu) + '\n\n\n')

        # 保存根音为 MIDI 文件
        melody_stream.write('midi', fp=output_midi_file)
        messagebox.showinfo("成功", f"简谱已保存为 {output_txt_file}，MIDI 已保存为 {output_midi_file}")
    except Exception as e:
        messagebox.showerror("错误", f"处理文件时出错: {e}")
        print(f"Error: {e}")

def main():
    input_file = open_file_dialog()
    if not input_file:
        messagebox.showinfo("提示", "未选择任何文件。")
        return

    score = process_root_mode(input_file)
    if not score:
        return

    selected_parts = select_parts(score)
    if not selected_parts:
        return

    output_txt_file = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
    output_midi_file = filedialog.asksaveasfilename(defaultextension=".mid", filetypes=[("MIDI files", "*.mid")])

    if output_txt_file and output_midi_file:
        convert_selected_parts_to_jianpu(score, selected_parts, output_txt_file, output_midi_file)
    else:
        messagebox.showinfo("提示", "未选择任何保存路径。")

if __name__ == "__main__":
    main()
