# -*- coding: utf-8 -*-
"""
背夹通信协议解析工具 - GUI版本
Protocol: Q/GDW XXXXX-2022 附录D
"""

import sys
import io
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox

# 修复Windows控制台编码
if sys.platform == "win32" and sys.stdout:
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

from protocol_parser import parse_frame, parse_hex_string, format_result_text


class BackclipParserGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("背夹通信协议解析工具 v1.0")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        self.setup_ui()

    def setup_ui(self):
        # 标题
        title_frame = ttk.Frame(self.root)
        title_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(title_frame, text="背夹通信协议解析工具", font=("Microsoft YaHei", 14, "bold")).pack(side=tk.LEFT)
        ttk.Label(title_frame, text="Q/GDW XXXXX-2022 附录D", font=("Microsoft YaHei", 9, "italic")).pack(side=tk.RIGHT)

        # 输入区域
        input_frame = ttk.LabelFrame(self.root, text="报文输入 (粘贴十六进制报文)", padding=10)
        input_frame.pack(fill=tk.BOTH, padx=10, pady=5)
        self.input_text = tk.Text(input_frame, height=4, font=("Consolas", 11))
        self.input_text.pack(fill=tk.BOTH)

        # 按钮区域
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Button(btn_frame, text="解析报文", command=self.parse_input).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="清空", command=self.clear_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="复制结果", command=self.copy_result).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="示例报文", command=self.load_example).pack(side=tk.RIGHT, padx=5)

        # 分隔
        ttk.Separator(self.root, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=5)

        # 结果区域
        result_frame = ttk.LabelFrame(self.root, text="解析结果", padding=10)
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.result_text = scrolledtext.ScrolledText(result_frame, font=("Consolas", 10), wrap=tk.WORD)
        self.result_text.pack(fill=tk.BOTH, expand=True)

        # 绑定快捷键
        self.input_text.bind("<Control-Return>", lambda e: self.parse_input())
        self.input_text.bind("<Control-Key-a>", lambda e: self.input_text.tag_add(tk.SEL, "1.0", tk.END) or "break")

    def parse_input(self):
        hex_str = self.input_text.get("1.0", tk.END).strip()
        if not hex_str:
            messagebox.showinfo("提示", "请输入报文")
            return
        try:
            data = parse_hex_string(hex_str)
            result, error = parse_frame(data)
            if error:
                self.result_text.delete("1.0", tk.END)
                self.result_text.insert("1.0", f"解析错误: {error}")
                return
            text = format_result_text(result)
            self.result_text.delete("1.0", tk.END)
            self.result_text.insert("1.0", text)
        except Exception as e:
            self.result_text.delete("1.0", tk.END)
            self.result_text.insert("1.0", f"解析异常: {str(e)}")

    def clear_all(self):
        self.input_text.delete("1.0", tk.END)
        self.result_text.delete("1.0", tk.END)

    def copy_result(self):
        text = self.result_text.get("1.0", tk.END).strip()
        if text:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            messagebox.showinfo("提示", "结果已复制到剪贴板")

    def load_example(self):
        examples = [
            ("获取背夹信息请求(测试帧)", "97FFFFFFFFAAAAAAAAAAAA9700000340B0011AE9"),
        ]
        menu = tk.Menu(self.root, tearoff=0)
        for name, data in examples:
            menu.add_command(label=name, command=lambda d=data: self.set_example(d))
        menu.tk_popup(self.root.winfo_x() + 200, self.root.winfo_y() + 200)

    def set_example(self, data):
        self.input_text.delete("1.0", tk.END)
        self.input_text.insert("1.0", data)
        self.parse_input()


def main():
    root = tk.Tk()
    app = BackclipParserGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
