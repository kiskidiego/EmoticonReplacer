# Emoticon Replacer

A lightweight, background utility for Windows that lets you search, scrape, and insert Japanese kaomojis and emoticons into any text field using simple keyboard triggers.

---

## Quick Start

1.  **Launch the App**: Run the script. A small icon will appear in your **System Tray** (bottom right near the clock).
2.  **The Trigger**: Press the semicolon key (**`;`**) once to start a search.
3.  **Type your Query**: Type a keyword (e.g., `cat`, `hug`, `shrug`, or `angry`).
4.  **Search**: Press semicolon (**`;`**) again to fetch results.
5.  **Select & Insert**: Use the navigation keys to find your favorite and press **Space** to paste it!

---

## Keyboard Controls

| Action | Key |
| :--- | :--- |
| **Start / Finish Search** | `;` (Semicolon) |
| **Scroll Results** | `.` (Next) and `,` (Previous) |
| **Change Pages** | `+` (Forward) and `-` (Back) |
| **Autocomplete Keyword** | `.` (While typing the search term) |
| **Confirm / Paste** | `Space` |
| **Cancel / Close** | `Esc` |
| **Add Custom Emote** | `Ctrl + Alt + A` |

---

## Requirements & Setup

To run this script from source, ensure you have Python installed and run the following:

```bash
pip install keyboard pyperclip requests beautifulsoup4 pystray Pillow
```

Once the requirements are met, run makefile.cmd to build the executable.
