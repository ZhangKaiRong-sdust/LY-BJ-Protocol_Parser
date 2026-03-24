# -*- coding: utf-8 -*-
"""
背夹通信协议解析工具 - GUI版本
Protocol: Q/GDW XXXXX-2022 附录D
"""

import sys
import io
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk, messagebox

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
        self.root.geometry("980x760")
        self.root.resizable(True, True)
        self.chinese_font_family = "Microsoft YaHei UI"
        self.ascii_font_family = "Consolas"
        self._setup_style()
        self.setup_ui()

    def _setup_style(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Title.TLabel", font=("Microsoft YaHei UI", 16, "bold"))
        style.configure("Subtitle.TLabel", font=("Microsoft YaHei UI", 10, "italic"))
        style.configure("Section.TLabelframe.Label", font=("Microsoft YaHei UI", 10, "bold"))
        style.configure("Action.TButton", font=("Microsoft YaHei UI", 10))

    def _frame_badge_colors(self, frame_kind):
        color_map = {
            "主站请求": ("#E8F1FF", "#0B57D0"),
            "从站正常应答": ("#EAF7EA", "#137333"),
            "从站异常应答": ("#FDECEC", "#C5221F"),
        }
        return color_map.get(frame_kind, ("#F3F4F6", "#4B5563"))

    def set_frame_badge(self, frame_kind=None):
        if not frame_kind:
            frame_kind = "等待解析"
        bg, fg = self._frame_badge_colors(frame_kind)
        self.frame_badge.configure(text=frame_kind, bg=bg, fg=fg)

    def setup_ui(self):
        # 标题
        title_frame = ttk.Frame(self.root)
        title_frame.pack(fill=tk.X, padx=14, pady=(12, 6))
        ttk.Label(title_frame, text="背夹通信协议解析工具", style="Title.TLabel").pack(side=tk.LEFT)
        ttk.Label(title_frame, text="Q/GDW XXXXX-2022 附录D", style="Subtitle.TLabel").pack(side=tk.RIGHT)

        # 输入区域
        input_frame = ttk.LabelFrame(self.root, text="报文输入", padding=10, style="Section.TLabelframe")
        input_frame.pack(fill=tk.X, padx=14, pady=6)

        hint_row = ttk.Frame(input_frame)
        hint_row.pack(fill=tk.X, pady=(0, 6))
        ttk.Label(hint_row, text="粘贴十六进制报文，支持空格和换行。Ctrl+Enter 可直接解析。").pack(side=tk.LEFT)

        input_text_frame = ttk.Frame(input_frame)
        input_text_frame.pack(fill=tk.BOTH)
        self.input_text = tk.Text(
            input_text_frame,
            height=5,
            font=(self.chinese_font_family, 12),
            wrap=tk.NONE,
            relief=tk.FLAT,
            borderwidth=0,
            padx=8,
            pady=8,
        )
        input_x_scroll = ttk.Scrollbar(input_text_frame, orient=tk.HORIZONTAL, command=self.input_text.xview)
        input_y_scroll = ttk.Scrollbar(input_text_frame, orient=tk.VERTICAL, command=self.input_text.yview)
        self.input_text.configure(xscrollcommand=input_x_scroll.set, yscrollcommand=input_y_scroll.set)
        self.input_text.grid(row=0, column=0, sticky="nsew")
        input_y_scroll.grid(row=0, column=1, sticky="ns")
        input_x_scroll.grid(row=1, column=0, sticky="ew")
        input_text_frame.columnconfigure(0, weight=1)
        input_text_frame.rowconfigure(0, weight=1)

        # 按钮区域
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill=tk.X, padx=14, pady=(2, 8))
        ttk.Button(btn_frame, text="解析报文", command=self.parse_input, style="Action.TButton").pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(btn_frame, text="清空", command=self.clear_all, style="Action.TButton").pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(btn_frame, text="复制结果", command=self.copy_result, style="Action.TButton").pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="示例报文", command=self.load_example, style="Action.TButton").pack(side=tk.RIGHT)

        # 分隔
        ttk.Separator(self.root, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=14, pady=4)

        # 结果区域
        result_frame = ttk.LabelFrame(self.root, text="解析结果", padding=10, style="Section.TLabelframe")
        result_frame.pack(fill=tk.BOTH, expand=True, padx=14, pady=6)

        result_info = ttk.Frame(result_frame)
        result_info.pack(fill=tk.X, pady=(0, 6))
        ttk.Label(result_info, text="结果区已禁用自动换行，字段会尽量按列对齐显示。").pack(side=tk.LEFT)
        self.frame_badge = tk.Label(
            result_info,
            text="等待解析",
            font=("Microsoft YaHei UI", 10, "bold"),
            padx=10,
            pady=4,
            bd=0,
            relief=tk.FLAT,
        )
        self.frame_badge.pack(side=tk.RIGHT, padx=(10, 0))
        self.status_var = tk.StringVar(value="等待解析")
        ttk.Label(result_info, textvariable=self.status_var).pack(side=tk.RIGHT)
        self.set_frame_badge()

        result_text_frame = ttk.Frame(result_frame)
        result_text_frame.pack(fill=tk.BOTH, expand=True)
        self.result_text = tk.Text(
            result_text_frame,
            font=(self.chinese_font_family, 12),
            wrap=tk.NONE,
            relief=tk.FLAT,
            borderwidth=0,
            padx=10,
            pady=10,
        )
        result_x_scroll = ttk.Scrollbar(result_text_frame, orient=tk.HORIZONTAL, command=self.result_text.xview)
        result_y_scroll = ttk.Scrollbar(result_text_frame, orient=tk.VERTICAL, command=self.result_text.yview)
        self.result_text.configure(xscrollcommand=result_x_scroll.set, yscrollcommand=result_y_scroll.set)
        self.result_text.grid(row=0, column=0, sticky="nsew")
        result_y_scroll.grid(row=0, column=1, sticky="ns")
        result_x_scroll.grid(row=1, column=0, sticky="ew")
        result_text_frame.columnconfigure(0, weight=1)
        result_text_frame.rowconfigure(0, weight=1)
        self.result_text.configure(state=tk.DISABLED)
        self._configure_text_styles()

        # 绑定快捷键
        self.input_text.bind("<Control-Return>", lambda e: self.parse_input())
        self.input_text.bind("<Control-Key-a>", lambda e: self.input_text.tag_add(tk.SEL, "1.0", tk.END) or "break")
        self.result_text.bind("<Control-Key-a>", lambda e: self.result_text.tag_add(tk.SEL, "1.0", tk.END) or "break")
        self.input_text.bind("<<Modified>>", self.on_input_modified)

    def _configure_text_styles(self):
        ascii_font = tkfont.Font(family=self.ascii_font_family, size=12)
        chinese_font = tkfont.Font(family=self.chinese_font_family, size=12)

        tab_pixels = ascii_font.measure(" " * 24)

        for widget in (self.input_text, self.result_text):
            widget.configure(tabs=(tab_pixels,))
            widget.tag_configure("ascii", font=ascii_font)
            widget.tag_configure("cjk", font=chinese_font)

    def _classify_char_tag(self, char):
        return "ascii" if ord(char) < 128 else "cjk"

    def _apply_mixed_font_tags(self, widget):
        widget.tag_remove("ascii", "1.0", tk.END)
        widget.tag_remove("cjk", "1.0", tk.END)
        text = widget.get("1.0", "end-1c")
        if not text:
            return

        start_index = 0
        current_tag = self._classify_char_tag(text[0])

        for index, char in enumerate(text[1:], start=1):
            tag = self._classify_char_tag(char)
            if tag != current_tag:
                widget.tag_add(current_tag, f"1.0+{start_index}c", f"1.0+{index}c")
                start_index = index
                current_tag = tag

        widget.tag_add(current_tag, f"1.0+{start_index}c", "end-1c")

    def on_input_modified(self, _event=None):
        if not self.input_text.edit_modified():
            return
        self._apply_mixed_font_tags(self.input_text)
        self.input_text.edit_modified(False)

    def set_result(self, text):
        self.result_text.configure(state=tk.NORMAL)
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert("1.0", text)
        self._apply_mixed_font_tags(self.result_text)
        self.result_text.configure(state=tk.DISABLED)

    def parse_input(self):
        hex_str = self.input_text.get("1.0", tk.END).strip()
        if not hex_str:
            messagebox.showinfo("提示", "请输入报文")
            return
        try:
            data = parse_hex_string(hex_str)
            result, error = parse_frame(data)
            if error:
                self.status_var.set("解析失败")
                self.set_frame_badge("解析失败")
                self.set_result(f"解析错误: {error}")
                return
            text = format_result_text(result)
            self.status_var.set(f"解析完成，数据区 {len(result['data_unit'])} 字节")
            self.set_frame_badge(result["control"]["frame_kind"])
            self.set_result(text)
        except Exception as e:
            self.status_var.set("解析异常")
            self.set_frame_badge("解析异常")
            self.set_result(f"解析异常: {str(e)}")

    def clear_all(self):
        self.input_text.delete("1.0", tk.END)
        self._apply_mixed_font_tags(self.input_text)
        self.input_text.edit_modified(False)
        self.set_result("")
        self.status_var.set("等待解析")
        self.set_frame_badge()

    def copy_result(self):
        self.result_text.configure(state=tk.NORMAL)
        text = self.result_text.get("1.0", tk.END).strip()
        self.result_text.configure(state=tk.DISABLED)
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
        self._apply_mixed_font_tags(self.input_text)
        self.input_text.edit_modified(False)
        self.parse_input()


def main():
    root = tk.Tk()
    app = BackclipParserGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
