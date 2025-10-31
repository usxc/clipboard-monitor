import tkinter as tk
from tkinter import TclError


POLL_INTERVAL_MS = 500  # 監視間隔（ミリ秒）。必要に応じて調整


class ClipboardMonitorApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("クリップボード監視")

        # ウィンドウは固定サイズ（リサイズ不可）
        self.root.geometry("640x400")
        self.root.resizable(False, False)

        # テキストボックス（複数行）
        self.text = tk.Text(
            self.root,
            wrap="word",
            font=("Meiryo", 10),  # Windows向けに日本語フォントを指定（未インストールでも動作に支障なし）
        )
        self.text.pack(fill="both", expand=True)

        # ユーザー編集を防ぐ（表示専用）。更新時のみ一時的に有効にする
        self.text.configure(state=tk.DISABLED)

        # 直近のテキスト内容
        self._last_text: str | None = None

        # 起動時に監視開始
        self._schedule_next_poll()

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
        # 次回のポーリングを予約
        self._schedule_next_poll()


def main() -> None:
    root = tk.Tk()
    app = ClipboardMonitorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

