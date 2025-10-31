import tkinter as tk
from tkinter import TclError, font as tkfont


POLL_INTERVAL_MS = 500  # 監視間隔（ミリ秒）。必要に応じて調整
HISTORY_MAX_ITEMS = 100  # 履歴の最大保持件数


class ClipboardMonitorApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("クリップボード監視")

        self.base_width = 640
        self.base_height = 400
        self.base_font_size = 10

        self.root.geometry(f"{self.base_width}x{self.base_height}")
        self.root.resizable(True, True)
        self.root.minsize(320, 200)

        # ツールバー（クリアボタン配置）
        self.toolbar = tk.Frame(self.root)
        self.toolbar.pack(fill="x")

        self.clear_btn = tk.Button(self.toolbar, text="クリア", command=self._on_clear)
        self.clear_btn.pack(side="right", padx=6, pady=6)

        self.history_btn = tk.Button(self.toolbar, text="履歴…", command=self._open_history_window)
        self.history_btn.pack(side="right", padx=6, pady=6)

        # テキストボックス（複数行）
        self.text = tk.Text(self.root, wrap="word")
        self.text.pack(fill="both", expand=True)

        # ユーザー編集を防ぐ（表示専用）。更新時のみ一時的に有効にする
        self.text.configure(state=tk.DISABLED)

        # フォントはウィンドウサイズに応じて可変
        self.font = tkfont.Font(family="Meiryo", size=self.base_font_size)
        self.text.configure(font=self.font)
        self.clear_btn.configure(font=self.font)
        self.history_btn.configure(font=self.font)

        # 直近のテキスト内容
        self._last_text: str | None = None

        # 履歴（最新が先頭）
        self.history: list[str] = []

        # 履歴ウィンドウ（必要時に生成）
        self._history_win: tk.Toplevel | None = None
        self._history_listbox: tk.Listbox | None = None

        # 起動時に監視開始
        self._schedule_next_poll()

        # リサイズに応じてフォントサイズ調整
        self.root.bind("<Configure>", self._on_configure)

    def _schedule_next_poll(self) -> None:
        self.root.after(POLL_INTERVAL_MS, self._poll_clipboard)

    def _get_clipboard_text(self) -> str | None:
        """クリップボードからプレーンテキストを取得。取得できない場合は None を返す。"""
        try:
            # テキスト以外や空の場合は TclError を投げる場合がある
            return self.root.clipboard_get()
        except TclError:
            return None

    def _update_textbox(self, value: str) -> None:
        # 一時的に編集許可して内容を入れ替え、再び無効化
        self.text.configure(state=tk.NORMAL)
        self.text.delete("1.0", tk.END)
        self.text.insert("1.0", value)
        self.text.see("1.0")
        self.text.configure(state=tk.DISABLED)

    def _poll_clipboard(self) -> None:
        current = self._get_clipboard_text()
        if current is not None and current != self._last_text:
            self._last_text = current
            self._update_textbox(current)
            self._push_history(current)
            self._refresh_history_listbox()
        # 次回のポーリングを予約
        self._schedule_next_poll()

    def _on_configure(self, event: tk.Event) -> None:
        # ウィンドウの実サイズを取得して基準比でフォントサイズを決定
        width = max(1, self.root.winfo_width())
        height = max(1, self.root.winfo_height())
        if width <= 1 or height <= 1:
            return
        w_scale = width / self.base_width
        h_scale = height / self.base_height
        scale = min(w_scale, h_scale)
        new_size = int(self.base_font_size * scale)
        new_size = max(8, min(new_size, 36))
        if new_size != self.font.cget("size"):
            self.font.configure(size=new_size)

    def _on_clear(self) -> None:
        """クリップボードを空文字でクリアし、表示も即時反映する。"""
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append("")
        except TclError:
            pass
        # 表示と内部状態を同期して空にする
        self._last_text = ""
        self._update_textbox("")

    # --- 履歴関連 ---
    def _push_history(self, text: str) -> None:
        """履歴に項目を追加（重複は先頭へ移動）。空文字は追加しない。"""
        if text == "":
            return
        try:
            idx = self.history.index(text)
            # 既存の同一項目があれば削除して先頭へ
            del self.history[idx]
        except ValueError:
            pass
        self.history.insert(0, text)
        # サイズ制限
        if len(self.history) > HISTORY_MAX_ITEMS:
            del self.history[HISTORY_MAX_ITEMS:]

    def _open_history_window(self) -> None:
        if self._history_win is not None and tk.Toplevel.winfo_exists(self._history_win):
            # 既に開いていれば前面へ
            self._history_win.deiconify()
            self._history_win.lift()
            self._history_win.focus_force()
            return

        win = tk.Toplevel(self.root)
        win.title("クリップボード履歴")
        win.geometry("520x360")
        win.transient(self.root)
        self._history_win = win

        # リスト + スクロールバー
        list_frame = tk.Frame(win)
        list_frame.pack(fill="both", expand=True, padx=8, pady=8)
        lb = tk.Listbox(list_frame, selectmode=tk.SINGLE, activestyle="none", font=self.font)
        lb.pack(side="left", fill="both", expand=True)
        sb = tk.Scrollbar(list_frame, orient="vertical", command=lb.yview)
        sb.pack(side="right", fill="y")
        lb.configure(yscrollcommand=sb.set)
        self._history_listbox = lb

        # ボタン行
        btn_frame = tk.Frame(win)
        btn_frame.pack(fill="x", padx=8, pady=(0, 8))
        copy_btn = tk.Button(btn_frame, text="コピーして閉じる", command=self._on_history_copy, font=self.font)
        copy_btn.pack(side="right")
        close_btn = tk.Button(btn_frame, text="閉じる", command=self._close_history_window, font=self.font)
        close_btn.pack(side="right", padx=(0, 8))

        # ダブルクリック/Enter でコピー
        lb.bind("<Double-Button-1>", lambda e: self._on_history_copy())
        lb.bind("<Return>", lambda e: self._on_history_copy())

        # ウィンドウ破棄時ハンドラ
        win.protocol("WM_DELETE_WINDOW", self._close_history_window)

        # 内容反映
        self._refresh_history_listbox()

    def _refresh_history_listbox(self) -> None:
        if self._history_listbox is None:
            return
        lb = self._history_listbox
        # 現在の選択を退避
        try:
            cur = lb.curselection()[0]
        except IndexError:
            cur = None
        lb.delete(0, tk.END)
        for item in self.history:
            lb.insert(tk.END, self._format_history_item(item))
        if cur is not None and cur < len(self.history):
            lb.selection_set(cur)
        elif len(self.history) > 0:
            # 初回など未選択なら先頭を選択
            lb.selection_set(0)

    def _format_history_item(self, s: str) -> str:
        # 改行を可視化しつつ短く表示
        view = s.replace("\r\n", "\n").replace("\r", "\n").replace("\n", " ⏎ ")
        maxlen = 100
        if len(view) > maxlen:
            view = view[:maxlen - 1] + "…"
        return view

    def _on_history_copy(self) -> None:
        if self._history_listbox is None:
            self._close_history_window()
            return
        sel = self._history_listbox.curselection()
        if sel:
            idx = sel[0]
        else:
            # 未選択なら先頭を使用（項目がなければ閉じる）
            if len(self.history) == 0:
                self._close_history_window()
                return
            idx = 0
        if not (0 <= idx < len(self.history)):
            self._close_history_window()
            return
        text = self.history[idx]
        # クリップボードへ設定
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
        except TclError:
            pass
        # 即時に画面へ反映し、履歴の先頭へ移動
        self._last_text = text
        self._update_textbox(text)
        self._push_history(text)
        self._refresh_history_listbox()
        # ウィンドウを閉じる
        self._close_history_window()

    def _close_history_window(self) -> None:
        """履歴ウィンドウを正しく破棄し、参照を解放する。"""
        if self._history_win is not None:
            try:
                self._history_win.destroy()
            except Exception:
                pass
        self._history_win = None
        self._history_listbox = None


def main() -> None:
    root = tk.Tk()
    app = ClipboardMonitorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
