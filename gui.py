import tkinter as tk
from tkinter import scrolledtext
import threading
from agent import ask_rocky, end_session, load_memory, get_initial_messages

class RockyGUI:
    def __init__(self):
        self.conversation_history = []
        self.window = None

    def build_window(self, root):
        self.window = tk.Toplevel(root)
        self.window.title("Rocky")
        self.window.geometry("500x650")
        self.window.configure(bg="#1a1a1a")
        self.window.attributes("-topmost", True)
        self.window.resizable(False, False)

        # center on screen
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - 250
        y = (self.window.winfo_screenheight() // 2) - 325
        self.window.geometry(f"500x650+{x}+{y}")

        # title
        tk.Label(
            self.window,
            text="Rocky",
            bg="#1a1a1a",
            fg="#8b90d6",
            font=("Segoe UI", 14, "bold"),
            pady=10
        ).pack()

        # hint label + input area packed FIRST so they anchor to the bottom
        tk.Label(
            self.window,
            text="Enter to send  •  Shift+Enter for newline  •  Esc to close",
            bg="#1a1a1a",
            fg="#444444",
            font=("Segoe UI", 8)
        ).pack(side=tk.BOTTOM, pady=(0, 8))

        input_frame = tk.Frame(self.window, bg="#1a1a1a")
        input_frame.pack(side=tk.BOTTOM, padx=10, pady=(0, 6), fill=tk.X)

        self.input_box = tk.Text(
            input_frame,
            bg="#2a2a2a",
            fg="#ffffff",
            font=("Segoe UI", 10),
            height=3,
            relief=tk.FLAT,
            padx=8,
            pady=8,
            insertbackground="white"
        )
        self.input_box.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.input_box.bind("<Return>", self.on_enter)
        self.input_box.bind("<Shift-Return>", lambda e: None)

        tk.Button(
            input_frame,
            text="Send",
            bg="#00ff88",
            fg="#000000",
            font=("Segoe UI", 10, "bold"),
            relief=tk.FLAT,
            padx=10,
            command=self.send_message
        ).pack(side=tk.RIGHT, padx=(5, 0))

        # chat display fills the remaining space above
        self.chat_display = scrolledtext.ScrolledText(
            self.window,
            bg="#111111",
            fg="#ffffff",
            font=("Segoe UI", 10),
            wrap=tk.WORD,
            state=tk.DISABLED,
            relief=tk.FLAT,
            padx=10,
            pady=10
        )
        self.chat_display.pack(padx=10, pady=(0, 6), fill=tk.BOTH, expand=True)
        self.window.update_idletasks()

        self.chat_display.tag_config("user", foreground="#00ff88")
        self.chat_display.tag_config("rocky", foreground="#ffffff")
        self.chat_display.tag_config("thinking", foreground="#888888")

        self.window.bind("<Escape>", self.on_close)
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)

        # greeting
        past_summary = load_memory()
        self.conversation_history = get_initial_messages(past_summary)
        if past_summary:
            self.append_message("Rocky", "Hey Prasan, I'm back. What do you need?", "rocky")
        else:
            self.append_message("Rocky", "Hey, I'm Rocky. What do you need?", "rocky")

        self.input_box.focus_set()

    def append_message(self, sender: str, message: str, tag: str):
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, f"{sender}: ", tag)
        self.chat_display.insert(tk.END, f"{message}\n\n")
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)

    def send_message(self):
        user_input = self.input_box.get("1.0", tk.END).strip()
        if not user_input:
            return
        self.input_box.delete("1.0", tk.END)
        self.append_message("You", user_input, "user")
        self.append_message("Rocky", "thinking...", "thinking")
        thread = threading.Thread(target=self.get_response, args=(user_input,))
        thread.daemon = True
        thread.start()

    def get_response(self, user_input: str):
        try:
            response, self.conversation_history = ask_rocky(user_input, self.conversation_history)
            self.window.after(0, self.update_response, response)
        except Exception as e:
            self.window.after(0, self.update_response, f"Error: {str(e)}")

    def update_response(self, response: str):
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete("end-3l", tk.END)
        self.chat_display.config(state=tk.DISABLED)
        self.append_message("Rocky", response, "rocky")

    def on_enter(self, event):
        self.send_message()
        return "break"

    def on_close(self, event=None):
        end_session(self.conversation_history)
        if self.window:
            self.window.destroy()
        self.window = None

    def show(self, root):
        if self.window is not None:
            try:
                if self.window.winfo_exists():
                    self.window.lift()
                    self.window.focus_force()
                    return
            except:
                pass
        self.window = None
        self.conversation_history = []
        self.build_window(root)