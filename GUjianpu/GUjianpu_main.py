# -*- coding: utf-8 -*-
import os
import tkinter as tk
from tkinter import filedialog, messagebox
from music21 import converter, chord, note, stream
import tempfile
import shutil
from dotenv import load_dotenv
import musicpy as mp

load_dotenv()

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
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="选择要处理的 MIDI 文件",
        filetypes=[
            ("MIDI Files", "*.mid *.MID"),
            ("All Files", "*.*")
        ]
    )
    return file_path

def extract_melody_with_musicpy(midi_file):
    piece, bpm, start_time = mp.read(midi_file).merge()

    # Split the theme
    melody_chord = piece.split_melody(mode='chord')

    temp_midi_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mid')
    mp.write(melody_chord, bpm, name=temp_midi_file.name)
    return temp_midi_file.name, melody_chord, bpm

# Function to prompt user to select parts to convert
def select_parts(score):
    parts = score.parts
    part_ids = [part.id for part in parts]
    part_names = [part.partName if part.partName else f"Part {i+1}" for i, part in enumerate(parts)]

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
    """Convert a music21 note or rest to Jianpu notation, handling duration, octave markers, and dotted notes."""

    # Rest
    if isinstance(m21_note, note.Rest):
        quarter_length = m21_note.duration.quarterLength
        dots = m21_note.duration.dots

        # Mapping rest duration based on quarterLength
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
            rest_notation = '0'  # Fallback for any undefined rests

        # Handle dotted rests
        if dots == 1:  # Single dotted rest
            rest_notation += '·'
        elif dots == 2:  # Double dotted rest
            rest_notation += '··'

        return rest_notation

    # Handle notes (音符)
    step = m21_note.pitch.step
    octave = m21_note.pitch.octave
    alter = m21_note.pitch.accidental.alter if m21_note.pitch.accidental else 0
    quarter_length = m21_note.duration.quarterLength  # Use quarterLength for precision
    dots = m21_note.duration.dots

    # Accidentals
    if alter == 1:
        step += '♯'
    elif alter == -1:
        step += '♭'

    # Convert step to Jianpu number
    base_step = step[0]
    jianpu_number = JIANPU_PITCH_MAP.get(base_step, '')

    # Add accidental
    if len(step) > 1:
        jianpu_number = ACCIDENTALS.get(alter, '') + jianpu_number

    # Add octave marking
    if octave < 4:
        jianpu_number = jianpu_number + '̣' * (4 - octave)
    elif octave > 4:
        jianpu_number = jianpu_number + '̇' * (octave - 4)

    # Adjust duration based on quarter length
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

    # Dotted notes
    if dots == 1:  
        jianpu_number += '·'
    elif dots == 2:  
        jianpu_number += '··'

    return jianpu_number

# Function to extract the root or bass note of a chord
def get_chord_root_or_bass(chrd):
    """
    Extracts the root of a chord using music21's chord analysis features.
    If it is a known chord, the root is derived from chord type (major, minor, etc.).
    Otherwise, returns the lowest note in the chord (bass).
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
        raise ValueError("The input must be a music21 chord object.")

# Function to convert a chord to Jianpu notation by extracting its root or bass note
def convert_chord_to_jianpu(m21_chord):
    """Convert a music21 chord to Jianpu notation by taking its root or bass note."""
    root_note = get_chord_root_or_bass(m21_chord)  
    return convert_note_to_jianpu(root_note)

# Function to process and convert the selected parts to Jianpu notation
def process_selected_parts(score, selected_parts, output_txt_file):
    """Convert the selected parts to Jianpu notation and save the result as a text file."""
    try:
        with open(output_txt_file, 'w', encoding='utf-8') as jianpu_file:
            jianpu_file.write("简谱转换结果:\n")

            # Iterate through selected parts
            for part in selected_parts:
                part_name = part.partName if part.partName else f"Part {part.id}"
                jianpu_file.write(f"\n声部: {part_name}\n")

                # Iterate through measures in the part
                measures = part.getElementsByClass(stream.Measure)
                measure_jianpu = []  # Store the Jianpu for the current line

                for i, measure in enumerate(measures, start=1):
                    measure_content = []  
                    notes = measure.notes

                    for element in notes:
                        if isinstance(element, chord.Chord):
                            jianpu_notation = convert_chord_to_jianpu(element)
                        elif isinstance(element, note.Note):
                            jianpu_notation = convert_note_to_jianpu(element)
                        elif isinstance(element, note.Rest):
                            jianpu_notation = convert_note_to_jianpu(element)

                        measure_content.append(jianpu_notation)

                    # Combine the Jianpu of this measure, separating notes with spaces
                    measure_str = ' '.join(measure_content)
                    measure_jianpu.append(f"|  {measure_str}  |")

                    # Every 4 measures, write a line of Jianpu, separating each measure with four spaces
                    if i % 4 == 0:
                        jianpu_file.write('    '.join(measure_jianpu) + '\n\n\n')
                        measure_jianpu = []  # Reset for the next set of 4 measures

                # Write any remaining measures with four spaces between measures
                if measure_jianpu:
                    jianpu_file.write('    '.join(measure_jianpu) + '\n\n\n')

        messagebox.showinfo("成功", f"简谱已保存为 {output_txt_file}")

    except Exception as e:
        messagebox.showerror("错误", f"处理文件时出错: {e}")
        print(f"Error: {e}")

# Main function to handle file processing and user interactions
def main():
    input_midi = open_file_dialog()
    if not input_midi:
        messagebox.showinfo("提示", "未选择任何文件。")
        return

    try:
        temp_midi, melody_chord, bpm = extract_melody_with_musicpy(input_midi)
    except Exception as e:
        messagebox.showerror("错误", f"无法提取主旋律: {e}")
        return

    save_melody_midi = filedialog.asksaveasfilename(defaultextension=".mid", filetypes=[("MIDI files", "*.mid")])
    if save_melody_midi:
        try:
            # Save as .midi file
            mp.write(melody_chord, bpm, name=save_melody_midi)
            messagebox.showinfo("成功", f"主旋律 MIDI 已保存为 {save_melody_midi}")
        except Exception as e:
            messagebox.showerror("错误", f"保存主旋律 MIDI 文件时出错: {e}")
            return

    # Extract the .midi using music21
    try:
        score = converter.parse(temp_midi)
    except Exception as e:
        messagebox.showerror("错误", f"无法解析临时 MIDI 文件: {e}")
        return

    # Select parts to convert
    selected_parts, selected_part_ids = select_parts(score)
    if not selected_parts:
        return

    output_txt_file = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])

    if output_txt_file:
        process_selected_parts(score, selected_parts, output_txt_file)
    else:
        messagebox.showinfo("提示", "未选择任何保存路径。")

if __name__ == "__main__":
    main()
