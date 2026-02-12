# Emoticon Replacer

A lightweight, background utility for Windows that lets you search, scrape, and insert Japanese kaomojis and emoticons into any text field using simple keyboard triggers.

---

## Quick Start

1.  **Launch the App**: Run the script. A small icon will appear in your **System Tray** (bottom right near the clock).
2.  **The Trigger**: Press the crtl+alt+s to open the emoticon search window. type in your query, something like "happy" or "sad".
3.  **Search**: Press the search button or the enter key to search for matching emoticons. the ones you use will be saved to a local database for your convenience, and will be ordered by most recent use.
4.  **Use the emoticon**: Scroll through the results with the arrow keys or your mouse. Press the enter key or double click a result to copy it to your clickboard and instert it into whatever you were typing before, if anything.

**Add your own emoticons**: Press ctrl+alt+a to open a window to add a custom emoticon. Introduce a keyword to identify it and the emoticon, then press the save button.

You can close the app or open either window by right-clicking the app's tray icon.

---

## Requirements & Setup

To run this script from source, ensure you have Python installed and run the following:

```bash
pip install keyboard pyperclip requests beautifulsoup4 pystray Pillow
```

Once the requirements are met, run makefile.cmd to build the executable.
