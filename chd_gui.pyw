import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import threading
import os
import sys

class CHDConverterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("CHD Converter UI,made by DoC 4 ZOOK :-)")
        self.root.geometry("500x350+{}+{}".format(
            int((self.root.winfo_screenwidth() - 500) / 2),
            int((self.root.winfo_screenheight() - 350) / 2)
        ))
        self.root.resizable(False, False)

        self.input_file = ""
        self.process = None
        self.process_running = False

        tk.Button(root, text="Select Input File (.cue/.iso/.gdi/.chd)", command=self.select_input).pack(pady=10)

        self.convert_cd_btn = tk.Button(root, text="Convert CD → CHD", command=self.convert_cd_to_chd, state=tk.DISABLED)
        self.convert_cd_btn.pack(pady=5)

        self.convert_iso_btn = tk.Button(root, text="Convert ISO → CHD", command=self.convert_iso_to_chd, state=tk.DISABLED)
        self.convert_iso_btn.pack(pady=5)

        self.extract_cd_btn = tk.Button(root, text="Extract CHD → BIN/CUE", command=self.extract_chd, state=tk.DISABLED)
        self.extract_cd_btn.pack(pady=5)

        tk.Button(root, text="Batch Convert Folder (.cue/.gdi/.iso → .chd)", command=self.batch_convert_folder).pack(pady=5)

        self.stop_btn = tk.Button(root, text="Stop Current Process", command=self.stop_process, state=tk.DISABLED, fg="red")
        self.stop_btn.pack(pady=(10, 20))

        self.status_label = tk.Label(root, text="", fg="green")
        self.status_label.pack(pady=10)

        self.progress_label = tk.Label(root, text="")
        self.progress_label.pack()

    def select_input(self):
        filetypes = [("Supported files", "*.cue *.iso *.gdi *.chd")]
        file = filedialog.askopenfilename(title="Select Input File", filetypes=filetypes)
        if file:
            self.input_file = file
            ext = os.path.splitext(file)[1].lower()
            self.convert_cd_btn.config(state=tk.NORMAL if ext in [".cue", ".gdi"] else tk.DISABLED)
            self.convert_iso_btn.config(state=tk.NORMAL if ext == ".iso" else tk.DISABLED)
            self.extract_cd_btn.config(state=tk.NORMAL if ext == ".chd" else tk.DISABLED)
            self.status_label.config(text=f"Selected: {os.path.basename(file)}", fg="blue")
            self.progress_label.config(text="")

    def run_command(self, args, success_message, output_path):
        if self.process_running:
            messagebox.showwarning("Warning", "A process is already running.")
            return

        if os.path.exists(output_path):
            messagebox.showerror("Error", f"File already exists:\n{output_path}")
            return

        def task():
            try:
                self.process_running = True
                self.stop_btn.config(state=tk.NORMAL)
                self.status_label.config(text="Processing...", fg="orange")
                self.progress_label.config(text="")

                # Hide CMD window on Windows
                creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

                with subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, creationflags=creationflags) as proc:
                    self.process = proc
                    for line in proc.stdout:
                        if "%" in line:
                            self.progress_label.config(text=line.strip())
                    proc.wait()
                    if proc.returncode == 0:
                        self.status_label.config(text=success_message, fg="green")
                    elif proc.returncode != 0 and self.process is None:
                        self.status_label.config(text="Aborted by user", fg="green")
                    else:
                        self.status_label.config(text="Process failed.", fg="red")
            finally:
                self.process = None
                self.process_running = False
                self.stop_btn.config(state=tk.DISABLED)

        threading.Thread(target=task).start()

    def convert_cd_to_chd(self):
        if not self.input_file.lower().endswith((".cue", ".gdi")):
            return
        output = os.path.splitext(self.input_file)[0] + ".chd"
        args = ["chdman", "createcd", "-i", self.input_file, "-o", output]
        self.run_command(args, f"Saved: {os.path.basename(output)}", output)

    def convert_iso_to_chd(self):
        if not self.input_file.lower().endswith(".iso"):
            return
        output = os.path.splitext(self.input_file)[0] + ".chd"
        args = ["chdman", "createcd", "-i", self.input_file, "-o", output]
        self.run_command(args, f"Saved: {os.path.basename(output)}", output)

    def extract_chd(self):
        if not self.input_file.lower().endswith(".chd"):
            return
        output = os.path.splitext(self.input_file)[0] + "_extracted.cue"
        args = ["chdman", "extractcd", "-i", self.input_file, "-o", output, "-ob", output.replace(".cue", ".bin")]
        self.run_command(args, f"Extracted to: {os.path.basename(output)}", output)

    def batch_convert_folder(self):
        folder = filedialog.askdirectory(title="Select Folder")
        if not folder:
            return

        for root_dir, _, files in os.walk(folder):
            for file in files:
                if file.lower().endswith((".cue", ".gdi", ".iso")):
                    input_path = os.path.join(root_dir, file)
                    output_path = os.path.splitext(input_path)[0] + ".chd"

                    if os.path.exists(output_path):
                        continue  # Skip existing

                    args = ["chdman", "createcd", "-i", input_path, "-o", output_path]
                    self.status_label.config(text=f"Batch: {file}", fg="orange")
                    self.run_command(args, f"Batch saved: {os.path.basename(output_path)}", output_path)

    def stop_process(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()
            self.process = None
            self.status_label.config(text="Aborted by user", fg="green")
            self.progress_label.config(text="")
            self.stop_btn.config(state=tk.DISABLED)
            self.process_running = False

if __name__ == "__main__":
    root = tk.Tk()
    app = CHDConverterGUI(root)
    root.mainloop()
