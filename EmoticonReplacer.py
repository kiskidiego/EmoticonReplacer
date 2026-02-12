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
MAX_RESULTS = 100

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

root = tk.Tk()
root.withdraw()  # Hide the main root window
search_window_ref = None
add_window_ref = None


def get_closest_keywords(query, limit=MAX_RESULTS):
    keys = list(local_db.get("keywords", []))
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
    global add_window_ref

    if add_window_ref and add_window_ref.winfo_exists():
        add_window_ref.lift()
        add_window_ref.focus_force()
        return

    add_window_ref = tk.Toplevel(root)
    add_window_ref.title("Add Custom Emoticon")
    add_window_ref.attributes("-topmost", True)
    #add_window_ref.geometry("300x200+700+400")
    add_window_ref.configure(bg="#2b2b2b")

    # Styling for labels and entries
    style = {"bg": "#2b2b2b", "fg": "white", "font": ("Arial", 10)}
    
    tk.Label(add_window_ref, text="Keyword:", **style).pack(pady=5)
    key_entry = tk.Entry(add_window_ref)
    key_entry.pack(pady=5)
    
    tk.Label(add_window_ref, text="Emoticon:", **style).pack(pady=5)
    emo_entry = tk.Entry(add_window_ref)
    emo_entry.pack(pady=5)

    def save_new_entry():
        keyword = key_entry.get().strip().lower()
        emoticon = emo_entry.get().strip()
        
        if keyword and emoticon:
            if keyword not in local_db["emoticons"]:
                local_db["emoticons"][keyword] = []
            
            # Add to the top of the list
            if emoticon in local_db["emoticons"][keyword]:
                local_db["emoticons"][keyword].remove(emoticon)
            local_db["emoticons"][keyword].insert(0, emoticon)

            if keyword in local_db["keywords"]:
                local_db["keywords"].remove(keyword)
            local_db["keywords"].insert(0, keyword)
            
            save_db()
            
            print(f"Added {emoticon} to '{keyword}'")
            add_window_ref.destroy()

    tk.Button(add_window_ref, text="Save", command=save_new_entry, bg="#444444", fg="white").pack(pady=10)

    width = add_window_ref.winfo_reqwidth()
    height = add_window_ref.winfo_reqheight()
    
    # Get screen dimensions
    screen_width = add_window_ref.winfo_screenwidth()
    screen_height = add_window_ref.winfo_screenheight()
    
    # Calculate coordinates for the center
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    
    add_window_ref.geometry(f'{width}x{height}+{x}+{y}')

def save_db():
    for keyword in local_db["emoticons"]:
        # We use a list comprehension to create a NEW list of cleaned strings
        cleaned_list = []
        for emoticon in local_db["emoticons"][keyword]:
            # Chain the replaces or use a loop
            e = (emoticon.replace('｀', '`')
                         .replace('（', '(')
                         .replace('）', ')')
                         .replace('˂', '<')
                         .replace('˃', '>')
                         .replace('＾', '^'))
            cleaned_list.append(e)
        
        # Now remove duplicates from the cleaned strings
        local_db["emoticons"][keyword] = list(dict.fromkeys(cleaned_list))

    with open(db_path, 'w', encoding='utf-8') as f:
        json.dump(local_db, f, ensure_ascii=False, indent=4)
        
    print("Database saved.")

def quit_window(icon, item):
    icon.stop()
    # Check if popup exists before trying to close it
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
        f.write('{"emoticons": {},' \
        '"keywords": []}')

local_db = {
    "emoticons": {},
    "keywords": []
}
with open(db_path, 'r', encoding='utf-8') as f:
    try:
        local_db = json.load(f)
    except:
        local_db = {"emoticons": {}, "keywords": []}

menu = (
    pystray.MenuItem('Add Emoticon',
        lambda: root.after(0, open_add_emoticon_window)),
    pystray.MenuItem('Search Emoticon',
        lambda: root.after(0, open_search_for_emoticon_window)),
    pystray.MenuItem('Quit', quit_window),
)
icon = pystray.Icon("EmoticonReplacer", image, "EmoticonReplacer", menu)

# Run this in a separate thread so it doesn't block your macro
threading.Thread(target=icon.run, daemon=True).start()

def remove_emoticon_from_db(keyword, emoticon):
    if keyword in local_db["emoticons"] and emoticon in local_db["emoticons"][keyword]:
        local_db["emoticons"][keyword].remove(emoticon)
        if not local_db["emoticons"][keyword]:  # If the list is empty, remove the keyword
            remove_keyword_from_db(keyword)
            return
        save_db()
        print(f"Removed {emoticon} from '{keyword}'")
    else:
        print(f"Emoticon '{emoticon}' not found under keyword '{keyword}'")

def remove_keyword_from_db(keyword):
    if keyword in local_db["emoticons"]:
        del local_db["emoticons"][keyword]
    if keyword in local_db["keywords"]:
        local_db["keywords"].remove(keyword)
        save_db()
        print(f"Removed keyword '{keyword}' and all its emoticons")
    else:
        print(f"Keyword '{keyword}' not found in database")

def fetch_emojis_from_web(query):
    global local_db

    """Scrapes EmojiDB for the given query."""
    if not query:
        return {}
    
    # URL encode the query for the search URL
    query = query.replace(' ', '-')
    encoded_query = urllib.parse.quote(query)
    url = f"https://emojidb.org/{encoded_query}"
    
    try:
        response = requests.get(url, timeout=2)
        if response.status_code != 200:
            return {}
        
        soup = BeautifulSoup(response.text, 'html.parser')
        emoji_divs = soup.find_all('div', class_='emoji')
        
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

def get_results(query):
    local_results = local_db.get("emoticons", {}).get(query, [])[:]
    if len(local_results) < MAX_RESULTS:
        web_results = fetch_emojis_from_web(query)
        for emoji in web_results:
            if emoji not in local_results:
                local_results.append(emoji)
            if len(local_results) >= MAX_RESULTS:
                break
    return local_results


def open_search_for_emoticon_window():
    global search_window_ref

    if search_window_ref and search_window_ref.winfo_exists():
        search_window_ref.lift()
        search_window_ref.focus_force()
        return

    showing_emoticons = False
    scrolling = False
    # Check if a search window already exists and focus it instead
    for widget in root.winfo_children():
        if isinstance(widget, tk.Toplevel) and widget.title() == "Search Emoticon":
            widget.lift()
            widget.focus_force()
            return
    
    search_window_ref = tk.Toplevel(root)
    search_window_ref.title("Search Emoticon")
    search_window_ref.attributes("-topmost", True)
    search_window_ref.configure(bg="#2b2b2b")
    
    # Mark this window as a search window
    search_window_ref._is_search_window = True

    # Styling
    style = {"bg": "#2b2b2b", "fg": "white", "font": ("Arial", 10)}
    
    tk.Label(search_window_ref, text="Enter keyword to search:", **style).pack(pady=5)
    key_entry = tk.Entry(search_window_ref)
    key_entry.focus()

    def close_search_window():
        nonlocal scrolling, showing_emoticons
        scrolling = False
        showing_emoticons = False
        search_window_ref.destroy()
    
    def show_suggestions(event=None):
        nonlocal scrolling, showing_emoticons
        scrolling = False
        showing_emoticons = False
        keyword = key_entry.get().strip().lower()
        suggestions = get_closest_keywords(keyword, MAX_RESULTS)
        
        results_listbox.delete(0, tk.END)
        if suggestions:
            for sug in suggestions:
                results_listbox.insert(tk.END, sug)

    def perform_search(event=None):
        nonlocal scrolling, showing_emoticons
        scrolling = False
        showing_emoticons = True
        keyword = key_entry.get().strip().lower()
        if keyword:
            results = get_results(keyword)
            
            results_listbox.delete(0, tk.END)
            if results:
                for res in results:
                    results_listbox.insert(tk.END, res)
            else:
                results_listbox.insert(tk.END, "No results found")
        move_focus_to_results(None)

    def move_focus_to_results(event):
        nonlocal scrolling
        if results_listbox.size() > 0 and not scrolling:
            scrolling = True
            results_listbox.focus_set()
            results_listbox.selection_clear(0, tk.END)
            results_listbox.selection_set(0)
            results_listbox.activate(0)
    
    def move_focus_to_search(event):
        nonlocal scrolling
        if scrolling and results_listbox.curselection() == (0,):
            scrolling = False
            key_entry.focus_force()

    # Bind events after everything is defined
    key_entry.bind("<Down>", move_focus_to_results)
    key_entry.bind("<KeyRelease>", show_suggestions)
    key_entry.bind("<Return>", perform_search)
    key_entry.bind("<Escape>", lambda e: close_search_window())
    key_entry.pack(pady=5)

    # Create results listbox
    results_listbox = tk.Listbox(search_window_ref, font=("Segoe UI Symbol", 12), width=30, height=20)
    results_listbox.pack(pady=5)

    def save_emoticon(emoticon, keyword):
        if keyword not in local_db["emoticons"]:
            local_db["emoticons"][keyword] = []
        
        # Add to the top of the list
        if emoticon in local_db["emoticons"][keyword]:
            local_db["emoticons"][keyword].remove(emoticon)
        local_db["emoticons"][keyword].insert(0, emoticon)

        if keyword in local_db["keywords"]:
            local_db["keywords"].remove(keyword)
        local_db["keywords"].insert(0, keyword)
        
        save_db()
        print(f"Saved {emoticon} to '{keyword}'")

    # Add double-click to copy functionality
    def select(event):
        selection = results_listbox.curselection()
        if selection:
            if(showing_emoticons):
                emoticon = results_listbox.get(selection[0])
                if emoticon:
                    if emoticon == "No results found":
                        move_focus_to_search(None)
                    else:
                        pyperclip.copy(emoticon)
                        print(f"Copied '{emoticon}' to clipboard")
                        save_emoticon(emoticon, key_entry.get().strip().lower())
                        search_window_ref.destroy()
                        root.after(100, lambda: keyboard.send('ctrl+v'))
            else:
                # If we're showing keywords, perform a search for that keyword
                key_entry.delete(0, tk.END)
                key_entry.insert(0, results_listbox.get(selection[0]))
                perform_search()
    
    def remove_selected_emoticon(event):
        if showing_emoticons:
            selection = results_listbox.curselection()
            if selection:
                emoticon = results_listbox.get(selection[0])
                keyword = key_entry.get().strip().lower()
                remove_emoticon_from_db(keyword, emoticon)
                perform_search()
        else:
            selection = results_listbox.curselection()
            if selection:
                keyword = results_listbox.get(selection[0])
                remove_keyword_from_db(keyword)
                scrolling = False
                key_entry.focus_force()
                show_suggestions()

    results_listbox.bind("<Up>", move_focus_to_search)
    results_listbox.bind("<Double-Button-1>", select)
    results_listbox.bind("<Return>", select)
    results_listbox.bind("<Delete>", remove_selected_emoticon)
    results_listbox.bind("<BackSpace>", remove_selected_emoticon)
    results_listbox.bind("<Escape>", lambda e: close_search_window())

    tk.Button(search_window_ref, text="Search", command=perform_search, bg="#444444", fg="white").pack(pady=5)
    
    # Add status label
    status_label = tk.Label(search_window_ref, text="", **style)
    status_label.pack(pady=2)

    # Center the window
    search_window_ref.update_idletasks()
    
    width = max(search_window_ref.winfo_reqwidth(), 200)
    height = max(search_window_ref.winfo_reqheight(), 350)
    
    screen_width = search_window_ref.winfo_screenwidth()
    screen_height = search_window_ref.winfo_screenheight()
    
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    
    search_window_ref.geometry(f'{width}x{height}+{x}+{y}')
    
    # Show initial suggestions
    show_suggestions(None)
    
    search_window_ref.deiconify() # Ensure it's not minimized
    search_window_ref.lift()
    key_entry.focus_force()

def listen_for_hotkeys():
    """
    Separate thread to handle hotkey monitoring without 
    interfering with the Tkinter mainloop.
    """
    # Use individual hotkeys with a small sleep to prevent double-triggers
    while True:
        if keyboard.is_pressed('ctrl+alt+a'):
            print("Hotkey: Add triggered")
            root.after(0, open_add_emoticon_window)
            time.sleep(0.5) # Prevent multiple triggers
        
        if keyboard.is_pressed('ctrl+alt+s'):
            print("Hotkey: Search triggered")
            root.after(0, open_search_for_emoticon_window)
            time.sleep(0.5)
            
        time.sleep(0.05) # Tiny sleep to save CPU cycles

# Start the hotkey listener in a daemon thread
hotkey_thread = threading.Thread(target=listen_for_hotkeys, daemon=True)
hotkey_thread.start()

print("EmoticonReplacer is running.")
print("Hotkeys: Ctrl+Alt+A (Add), Ctrl+Alt+S (Search)")

# Standard Tkinter mainloop
try:
    root.mainloop()
except KeyboardInterrupt:
    pass
finally:
    print("Exiting EmoticonReplacer.")
    os._exit(0)