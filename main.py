import os
import sys
import threading
import tkinter as tk
from dataclasses import dataclass
from datetime import datetime
from json import dumps
from pathlib import Path
from tkinter import ttk
from webbrowser import open_new_tab

import requests
from dotenv import load_dotenv

API_URL = "https://gnews.io/api/v4/top-headlines"


@dataclass
class Article:
    title: str
    description: str
    source: str
    published_at: str
    url: str


def fetch_articles(api_key: str) -> list[Article]:
    try:
        response = requests.get(
            API_URL,
            params={
                "apikey": api_key,
                "category": "technology",
                "lang": "en",
                "max": 10,
            },
            timeout=15,
        )
    except requests.exceptions.Timeout:
        raise RuntimeError(
            "The news API request timed out. Please try again."
        ) from None
    except requests.exceptions.RequestException:
        raise RuntimeError(
            "Could not connect to the news API. Check your internet connection."
        ) from None

    if not response.ok:
        try:
            error_data = response.json()
        except ValueError:
            error_data = {}

        message = f"The news API returned HTTP {response.status_code}."
        if isinstance(error_data, dict):
            details = (
                error_data.get("errors")
                or error_data.get("error")
                or error_data.get("message")
            )
            if details:
                details = (
                    dumps(details)
                    if isinstance(details, (dict, list))
                    else str(details)
                )
                message += f" Details: {details.replace(api_key, '[redacted]')}"
        if response.status_code == 400:
            message += (
                " Check the error details, your API key, and the GNews dashboard."
            )
        raise RuntimeError(message)

    data = response.json()
    return [
        Article(
            title=item.get("title") or "Untitled",
            description=item.get("description") or "No description available.",
            source=(item.get("source") or {}).get("name") or "Unknown source",
            published_at=item.get("publishedAt") or "Unknown date",
            url=item.get("url") or "",
        )
        for item in data.get("articles", [])
    ]


def main() -> int:
    load_dotenv(dotenv_path=Path(__file__).resolve().with_name(".env"), override=True)
    api_key = os.getenv("GNEWS_API_KEY")
    if "--cli" in sys.argv[1:]:
        if not api_key:
            print("Missing GNEWS_API_KEY. Add your key to a .env file.", file=sys.stderr)
            return 1

        try:
            articles = fetch_articles(api_key)
        except RuntimeError as error:
            print(f"Error: {error}", file=sys.stderr)
            return 1

        if not articles:
            print("No technology news articles were found.")
            return 0

        print(f"Latest technology news ({len(articles)} articles)\n")
        for index, article in enumerate(articles, start=1):
            print(f"{index}. {article.title}")
            print(f"   Source: {article.source} | Published: {article.published_at}")
            print(f"   {article.description}")
            if article.url:
                print(f"   Read more: {article.url}")
            print()
        return 0

    root = tk.Tk()
    NewsApp(root, api_key)
    root.mainloop()

    return 0


class NewsApp:
    BACKGROUND = "#0b1120"
    CARD = "#131e30"
    TEXT = "#eef3fc"
    MUTED = "#96a6bd"
    ACCENT = "#68e0cf"

    def __init__(self, root: tk.Tk, api_key: str | None) -> None:
        self.root = root
        self.api_key = api_key
        self.root.title("Tech News")
        self.root.geometry("940x760")
        self.root.minsize(620, 480)
        self.root.configure(bg=self.BACKGROUND)

        style = ttk.Style(root)
        style.configure(
            "News.Horizontal.TProgressbar",
            troughcolor=self.CARD,
            background=self.ACCENT,
            bordercolor=self.CARD,
            lightcolor=self.ACCENT,
            darkcolor=self.ACCENT,
        )

        header = tk.Frame(root, bg=self.BACKGROUND)
        header.pack(fill="x", padx=38, pady=(30, 18))
        tk.Label(
            header,
            text="TECHNOLOGY  /  LATEST HEADLINES",
            bg=self.BACKGROUND,
            fg=self.ACCENT,
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor="w")
        heading = tk.Frame(header, bg=self.BACKGROUND)
        heading.pack(fill="x", pady=(8, 0))
        tk.Label(
            heading,
            text="Tech News",
            bg=self.BACKGROUND,
            fg=self.TEXT,
            font=("Segoe UI", 26, "bold"),
        ).pack(side="left")
        self.refresh_button = tk.Button(
            heading,
            text="Refresh",
            command=self.refresh,
            bg="#203147",
            fg=self.TEXT,
            activebackground="#304760",
            activeforeground=self.TEXT,
            disabledforeground=self.MUTED,
            relief="flat",
            cursor="hand2",
            padx=17,
            pady=9,
            font=("Segoe UI", 10, "bold"),
        )
        self.refresh_button.pack(side="right", pady=(6, 0))
        tk.Label(
            header,
            text="A fresh selection of English technology news.",
            bg=self.BACKGROUND,
            fg=self.MUTED,
            font=("Segoe UI", 10),
        ).pack(anchor="w", pady=(4, 0))

        status_bar = tk.Frame(root, bg=self.BACKGROUND)
        status_bar.pack(fill="x", padx=40, pady=(0, 12))
        self.status_label = tk.Label(
            status_bar,
            text="Ready",
            bg=self.BACKGROUND,
            fg=self.MUTED,
            font=("Segoe UI", 9),
        )
        self.status_label.pack(side="left")
        self.progress = ttk.Progressbar(
            status_bar,
            mode="indeterminate",
            length=90,
            style="News.Horizontal.TProgressbar",
        )
        self.progress.pack(side="right")

        content = tk.Frame(root, bg=self.BACKGROUND)
        content.pack(fill="both", expand=True, padx=38, pady=(0, 24))
        self.canvas = tk.Canvas(
            content,
            background=self.BACKGROUND,
            highlightthickness=0,
            borderwidth=0,
        )
        scrollbar = tk.Scrollbar(
            content,
            orient="vertical",
            command=self.canvas.yview,
            background=self.CARD,
            troughcolor=self.BACKGROUND,
            activebackground="#304760",
            relief="flat",
            borderwidth=0,
        )
        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.cards_frame = tk.Frame(self.canvas, bg=self.BACKGROUND)
        self.article_labels: list[tk.Label] = []
        self.cards_window = self.canvas.create_window(
            (0, 0), window=self.cards_frame, anchor="nw"
        )
        self.cards_frame.bind("<Configure>", self._update_scroll_region)
        self.canvas.bind("<Configure>", self._resize_cards)
        self.canvas.bind_all("<MouseWheel>", self._scroll)
        self.root.bind("<F5>", lambda _event: self.refresh())
        self.is_loading = False

        if not self.api_key:
            self.status_label.configure(
                text="Add GNEWS_API_KEY to the .env file next to main.py."
            )
            self.refresh_button.configure(state="disabled")
        else:
            self.refresh()

    def _update_scroll_region(self, _event: tk.Event) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _resize_cards(self, event: tk.Event) -> None:
        self.canvas.itemconfigure(self.cards_window, width=event.width)
        for label in self.article_labels:
            label.configure(wraplength=max(300, event.width - 88))

    def _scroll(self, event: tk.Event) -> None:
        if self.root.winfo_exists():
            self.canvas.yview_scroll(int(-event.delta / 120), "units")

    def refresh(self) -> None:
        if not self.api_key or self.is_loading:
            return
        self.is_loading = True
        self.refresh_button.configure(state="disabled")
        self.status_label.configure(text="Fetching the latest headlines...")
        self.progress.start(12)
        threading.Thread(target=self._fetch_in_background, daemon=True).start()

    def _fetch_in_background(self) -> None:
        try:
            articles = fetch_articles(self.api_key)
        except RuntimeError as error:
            self.root.after(0, self._show_result, None, str(error))
            return
        self.root.after(0, self._show_result, articles, None)

    def _show_result(
        self, articles: list[Article] | None, error: str | None
    ) -> None:
        self.is_loading = False
        self.progress.stop()
        self.refresh_button.configure(state="normal")
        if error:
            self.status_label.configure(text=error, fg="#ff9b9b", wraplength=760)
            return

        for card in self.cards_frame.winfo_children():
            card.destroy()
        self.article_labels.clear()

        if not articles:
            self.status_label.configure(
                text="No technology headlines were found.",
                fg=self.MUTED,
                wraplength=760,
            )
            return

        self.status_label.configure(
            text=f"{len(articles)} stories  ·  Updated {datetime.now():%H:%M}",
            fg=self.MUTED,
            wraplength=760,
        )
        for article in articles:
            card = tk.Frame(self.cards_frame, bg=self.CARD, padx=22, pady=17)
            card.pack(fill="x", pady=(0, 12))
            title_label = tk.Label(
                card,
                text=article.title,
                bg=self.CARD,
                fg=self.TEXT,
                font=("Segoe UI", 13, "bold"),
                justify="left",
                anchor="w",
                wraplength=790,
            )
            title_label.pack(fill="x", anchor="w")
            self.article_labels.append(title_label)
            tk.Label(
                card,
                text=f"{article.source}  ·  {article.published_at}",
                bg=self.CARD,
                fg=self.ACCENT,
                font=("Segoe UI", 9, "bold"),
                anchor="w",
            ).pack(fill="x", pady=(8, 5))
            description_label = tk.Label(
                card,
                text=article.description,
                bg=self.CARD,
                fg=self.MUTED,
                font=("Segoe UI", 10),
                justify="left",
                anchor="w",
                wraplength=790,
            )
            description_label.pack(fill="x")
            self.article_labels.append(description_label)
            if article.url:
                tk.Button(
                    card,
                    text="Read article  >",
                    command=lambda url=article.url: open_new_tab(url),
                    bg=self.CARD,
                    fg=self.ACCENT,
                    activebackground=self.CARD,
                    activeforeground=self.TEXT,
                    relief="flat",
                    borderwidth=0,
                    cursor="hand2",
                    font=("Segoe UI", 9, "bold"),
                ).pack(anchor="w", pady=(9, 0))

        self.canvas.yview_moveto(0)


if __name__ == "__main__":
    raise SystemExit(main())
