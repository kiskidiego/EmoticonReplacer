import keyboard
import pyperclip
import time
import tkinter as tk
import requests
from bs4 import BeautifulSoup
import urllib.parse
import threading
import pystray
from PIL import Image
import difflib
import sys
import os
import json


HOST = "127.0.0.1"
PORT = 54321
MAGIC = b"EMOTICON_REPLACER_V1"

import ctypes
import sys

def ensure_single_instance():
    mutex_name = "Global\\EmoticonReplacer_Mutex"

    kernel32 = ctypes.windll.kernel32
    mutex = kernel32.CreateMutexW(None, False, mutex_name)
    last_error = kernel32.GetLastError()

    ERROR_ALREADY_EXISTS = 183

    if last_error == ERROR_ALREADY_EXISTS:
        # Another instance is already running
        sys.exit(0)

ensure_single_instance()

def show_preview():
    global popup, typed_buffer, preview_results
    if not typed_buffer:
        if popup: popup.withdraw()
        return

    # Fuzzy match: find keys in local_db that contain the typed_buffer
    preview_results = get_closest_keywords(typed_buffer, limit=5)
    
    if not preview_results:
        if popup: popup.withdraw()
        return

    # Create/Update popup specifically for previewing keywords
    if not popup:
        popup = tk.Tk()
        popup.overrideredirect(True)
        popup.attributes("-topmost", True)

    for widget in popup.winfo_children():
        widget.destroy()

    # Listbox showing potential keyword matches
    lb = tk.Listbox(popup, font=("Segoe UI Symbol", 12), 
                    width=30, height=len(preview_results))
    lb.pack()
    
    for res in preview_results:
        lb.insert(tk.END, f"  {res}...")

    instructions = tk.Label(popup, text=f". to autocomplete", font=("Arial", 8), fg="gray")
    instructions.pack()

    width = popup.winfo_reqwidth()
    height = popup.winfo_reqheight()
    
    # Get screen dimensions
    screen_width = popup.winfo_screenwidth()
    screen_height = popup.winfo_screenheight()
    
    # Calculate coordinates for the center
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    
    popup.geometry(f'{width}x{height}+{x}+{y}')
    popup.update_idletasks()
    popup.deiconify()
    popup.update()

def get_closest_keywords(query, limit=10):
    keys = list(local_db.keys())
    if not query:
        return keys[:limit]

    return difflib.get_close_matches(
        query,
        keys,
        n=limit,
        cutoff=0.1
    )

def open_add_emoticon_window():
    # Create a small popup window
    add_win = tk.Tk()
    add_win.title("Add Custom Emoticon")
    add_win.attributes("-topmost", True)
    #add_win.geometry("300x200+700+400")
    add_win.configure(bg="#2b2b2b")

    # Styling for labels and entries
    style = {"bg": "#2b2b2b", "fg": "white", "font": ("Arial", 10)}
    
    tk.Label(add_win, text="Keyword:", **style).pack(pady=5)
    key_entry = tk.Entry(add_win)
    key_entry.pack(pady=5)
    
    tk.Label(add_win, text="Emoticon:", **style).pack(pady=5)
    emo_entry = tk.Entry(add_win)
    emo_entry.pack(pady=5)

    def save_new_entry():
        keyword = key_entry.get().strip().lower()
        emoticon = emo_entry.get().strip()
        
        if keyword and emoticon:
            if keyword not in local_db:
                local_db[keyword] = []
            
            # Add to the top of the list
            if emoticon in local_db[keyword]:
                local_db[keyword].remove(emoticon)
            local_db[keyword].insert(0, emoticon)
            
            save_db()
            
            print(f"Added {emoticon} to '{keyword}'")
            add_win.destroy()

    tk.Button(add_win, text="Save", command=save_new_entry, bg="#444444", fg="white").pack(pady=10)

    width = add_win.winfo_reqwidth()
    height = add_win.winfo_reqheight()
    
    # Get screen dimensions
    screen_width = add_win.winfo_screenwidth()
    screen_height = add_win.winfo_screenheight()
    
    # Calculate coordinates for the center
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    
    add_win.geometry(f'{width}x{height}+{x}+{y}')

    add_win.mainloop()

def save_db():
    with open(db_path, 'w', encoding='utf-8') as f:
        
        json.dump(local_db, f, ensure_ascii=False, indent=4)
    print("Database saved.")

def quit_window(icon, item):
    icon.stop()
    # Check if popup exists before trying to close it
    if popup is not None:
        popup.quit()
    os._exit(0)


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# Use it whenever you load your icon:
icon_path = resource_path("icon.png")
image = Image.open(icon_path)

# This ensures the JSON is always created in the same folder as the EXE
db_path = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "emoticon_replacer.json")

if not os.path.exists(db_path):
    with open(db_path, 'w', encoding='utf-8') as f:
        f.write('{}')

local_db = {}
with open(db_path, 'r', encoding='utf-8') as f:
    try:
        local_db = json.load(f)
    except:
        local_db = {}

menu = (
    pystray.MenuItem('Add Emoticon', lambda: threading.Thread(target=open_add_emoticon_window).start()),
    pystray.MenuItem('Quit', quit_window),
)
icon = pystray.Icon("EmoticonReplacer", image, "EmoticonReplacer", menu)

# Run this in a separate thread so it doesn't block your macro
threading.Thread(target=icon.run, daemon=True).start()

TRIGGER = ';'
MAX_RESULTS = 100
RESULTS_PER_PAGE = 10

def fetch_emojis_from_web(query):
    global local_db

    """Scrapes EmojiDB for the given query."""
    if not query:
        return {}
    
    # URL encode the query for the search URL
    encoded_query = urllib.parse.quote(query)
    url = f"https://emojicombos.com/{encoded_query}"
    
    try:
        response = requests.get(url, timeout=2)
        if response.status_code != 200:
            return {}
        
        soup = BeautifulSoup(response.text, 'html.parser')
        emoji_divs = soup.find_all('div', class_='emojis')
        
        results = []
        # Limit results to MAX_RESULTS
        for div in emoji_divs[:MAX_RESULTS]:
            emoji_char = div.text
            if(len(emoji_char) > 20 or len(emoji_char) <= 2):
                continue
            emoji_char = emoji_char.replace('｀', '`')
            emoji_char = emoji_char.replace('（', '(')
            emoji_char = emoji_char.replace('）', ')')
            emoji_char = emoji_char.replace('˂', '<')
            emoji_char = emoji_char.replace('˃', '>')
            emoji_char = emoji_char.replace('＾', '^')
            results.append(emoji_char)
            
        return results
    except Exception as e:
        print(f"Error fetching from EmojiDB: {e}")
        return []

typed_buffer = ""
typing = False
selecting = False
popup = None
results = []
preview_results = []
selected_index = 0
current_page = 0

def close_popup():
    global popup, typing, typed_buffer, results, selecting
    if popup:
        popup.destroy()
        popup = None
    typing = False
    selecting = False
    typed_buffer = ""
    results = []

def insert_emote(emoji_char, emoji_query):
    emoji_char = emoji_char.replace('｀', '`')
    emoji_char = emoji_char.replace('（', '(')
    emoji_char = emoji_char.replace('）', ')')
    emoji_char = emoji_char.replace('˂', '<')
    emoji_char = emoji_char.replace('˃', '>')
    emoji_char = emoji_char.replace('＾', '^')
    print(f"Inserting emoticon '{emoji_char}' for query '{emoji_query}'")
    old_clipboard = pyperclip.paste()
    
    # Backspace the trigger + buffer
    backspaces = len(typed_buffer) + 2
    for _ in range(backspaces):
        keyboard.send("backspace")
    
    pyperclip.copy(emoji_char)
    while(not pyperclip.paste() == emoji_char):
        time.sleep(0.05)

    keyboard.press_and_release('ctrl+v')

    threading.Timer(0.5, lambda: pyperclip.copy(old_clipboard)).start()
    close_popup()

    if emoji_query not in local_db:
        local_db[emoji_query] = []
    
    if emoji_char in local_db[emoji_query]:
        local_db[emoji_query].remove(emoji_char)

    local_db[emoji_query].insert(0, emoji_char)
    save_db()

    

def show_popup(page):
    global popup, results
    if not results:
        if popup: popup.withdraw()
        return
    if not popup:
        popup = tk.Tk()
        popup.overrideredirect(True)
        popup.attributes("-topmost", True)
        #popup.geometry("+600+400")

    for widget in popup.winfo_children():
        widget.destroy()

    page_results = results[page*RESULTS_PER_PAGE:(page+1)*RESULTS_PER_PAGE]

    if not page_results:
        if popup: popup.withdraw()
        return

    longest_emote = max(len(e) for e in page_results) if page_results else 15
    dynamic_width = min(max(longest_emote + 2, 20), 40)

    listbox = tk.Listbox(popup, font=("Segoe UI Symbol", 12), 
                        width=dynamic_width, height=len(page_results))
    
    listbox.pack()

    for emoji in page_results:
        listbox.insert(tk.END, f"  {emoji}")
    
    listbox.selection_set(selected_index)

    instructions = tk.Label(popup, text=f". / , to scroll  + / - to switch pages", font=("Arial", 8), fg="gray")
    instructions.pack()

    total_pages = (len(results) + RESULTS_PER_PAGE - 1) // RESULTS_PER_PAGE
    page_info = tk.Label(popup, text=f"Page {page + 1} of {total_pages}", font=("Arial", 8), fg="gray")
    page_info.pack()

    popup.update_idletasks() # Calculate window size based on content
    
    width = popup.winfo_reqwidth()
    height = popup.winfo_reqheight()
    
    # Get screen dimensions
    screen_width = popup.winfo_screenwidth()
    screen_height = popup.winfo_screenheight()
    
    # Calculate coordinates for the center
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    
    popup.geometry(f'{width}x{height}+{x}+{y}')

    popup.deiconify()
    popup.update()

def on_key(event):
    global typed_buffer, typing, selected_index, results, popup, selecting, current_page

    if event.event_type != "down":
        return
    
    if event.name == TRIGGER and not typing and not selecting:
        print("Trigger detected, starting to type...")
        typing = True
        typed_buffer = ""
        selected_index = 0
        results = []
        show_preview()
        return

    elif typing:
        if event.name == TRIGGER:
            print("Trigger pressed again, searching...")
            typing = False
            
            if(typed_buffer):
                results = get_results(typed_buffer)    
                selected_index = 0
                current_page = 0

                if not results:
                    print("No results found.")
                    close_popup()
                    return

                show_popup(current_page)
                selecting = True
            return
        
        elif event.name == ".":
            print("Autocomplete triggered.")
            if preview_results:
                for _ in range(len(typed_buffer) + 1):
                    keyboard.send("backspace")
                typed_buffer = preview_results[0]
                keyboard.write(typed_buffer)
                show_preview()
        
        elif event.name == "esc":
            close_popup()
            return
        
        elif event.name == "backspace":
            if not typed_buffer:
                typing = False
                if popup: popup.withdraw()
                return
            typed_buffer = typed_buffer[:-1]
            show_preview()

        elif len(event.name) == 1:
            typed_buffer += event.name
            show_preview()

        elif event.name == "space":
            typed_buffer += "-"

        elif event.name in ["enter", "tab"]:
            close_popup()
            return
    
    elif selecting:
        if event.name == "backspace":
            selected_index = 0
            results = []
            if popup: popup.withdraw()
            typing = True
            selecting = False
            return

        elif event.name == "space":
            keyboard.press_and_release('backspace')
            if results:
                insert_emote(results[current_page * RESULTS_PER_PAGE + selected_index], typed_buffer)
                selecting = False
            return
    
        elif event.name == ".":
            keyboard.press_and_release('backspace')
            selected_index += 1
            if selected_index >= min(RESULTS_PER_PAGE, len(results) - current_page * RESULTS_PER_PAGE):
                selected_index = 0
                current_page += 1
                if current_page * RESULTS_PER_PAGE >= len(results):
                    current_page = 0
            show_popup(current_page)
            return
        
        elif event.name == ",":
            keyboard.press_and_release('backspace')
            selected_index -= 1
            if selected_index < 0:
                current_page -= 1
                if current_page < 0:
                    current_page = (len(results) - 1) // RESULTS_PER_PAGE
                selected_index = min(RESULTS_PER_PAGE - 1, len(results) - current_page * RESULTS_PER_PAGE - 1)
            show_popup(current_page)
            return

        elif event.name =="esc":
            close_popup()
            return
        
        elif event.name == "+" or event.name == "=":
            keyboard.press_and_release('backspace')
            if (current_page + 1) * RESULTS_PER_PAGE < len(results):
                current_page += 1
                selected_index = 0
                show_popup(current_page)
            return
        
        elif event.name == "-":
            keyboard.press_and_release('backspace')
            if current_page > 0:
                current_page -= 1
                selected_index = 0
                show_popup(current_page)
            return

        else:
            close_popup()

def get_results(query):
    local_results = local_db.get(query, [])[:]
    if len(local_results) < MAX_RESULTS:
        web_results = fetch_emojis_from_web(query)
        for emoji in web_results:
            if emoji not in local_results:
                local_results.append(emoji)
            if len(local_results) >= MAX_RESULTS:
                break
    return local_results
            

keyboard.hook(on_key)
keyboard.add_hotkey('ctrl+alt+a', lambda: threading.Thread(target=open_add_emoticon_window).start())
print(f"Live EmoticonReplacer macro running. Type {TRIGGER} + query...")
keyboard.wait()