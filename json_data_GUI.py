import json
import os
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

# 定義 JSON 檔案路徑
FOLDER_PATH = "db"
FACES_FILE_PATH = f"{FOLDER_PATH}/faces.json"
STORIES_FILE_PATH = f"{FOLDER_PATH}/stories.json"
OBJECT_FILE_PATH = f"{FOLDER_PATH}/objects.json"
VOCABULARIES_FILE_PATH = f"{FOLDER_PATH}/vocabularies.json"

# 確保資料夾存在
if not os.path.exists(FOLDER_PATH):
    os.makedirs(FOLDER_PATH)

# 初始化 JSON 檔案
def init_json(file_path, default_content):
    if not os.path.exists(file_path):
        with open(file_path, 'w') as f:
            json.dump(default_content, f)

init_json(FACES_FILE_PATH, [])
init_json(STORIES_FILE_PATH, [])
init_json(OBJECT_FILE_PATH, [])
init_json(VOCABULARIES_FILE_PATH, [])

# 載入 JSON 文件
def load_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# 保存 JSON 文件
def save_json(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# 更新表格數據
def update_table(tree, json_data, columns, key_field="id"):
    for row in tree.get_children():
        tree.delete(row)
    for item in json_data:
        if key_field == "id":
            tree.insert("", "end", values=tuple(item["id"] if col == "id" else item["data"].get(col, "") for col in columns))
        elif key_field == "story":
            tree.insert("", "end", values=tuple(item["story"] if col == "story" else item["m_data"].get(col, "") for col in columns))

# 新增項目
def add_item(json_data, tree, columns, file_path):
    new_id = simpledialog.askstring("新增", "輸入新的 ID：")
    if not new_id:
        return
    for item in json_data:
        if item["id"] == new_id:
            messagebox.showerror("錯誤", "ID 已存在！")
            return
    new_item = {"id": new_id, "data": {}}
    for col in columns[1:]:
        new_item["data"][col] = ""
    json_data.append(new_item)
    update_table(tree, json_data, columns)
    save_json(file_path, json_data)

def add_item_stories(json_data, tree, columns, file_path, is_story=False, key_field="id"):
    if key_field == "id":
        data_field = "data"
        new_id = simpledialog.askstring("新增", "輸入新的 ID：")
    elif key_field == "story":
        data_field = "m_data"
        new_id = simpledialog.askstring("新增", "輸入新的 Story：")
    if not new_id:
        return
    for item in json_data:
        if item[key_field] == new_id:
            messagebox.showerror("錯誤", "ID 已存在！")
            return
    if key_field == "id":
        new_item = {"id": new_id, "data": {}}
    elif key_field == "story":
        new_item = {"story": new_id, "m_data":{}}
    for col in columns[1:]:
        if col == "total":
            new_item[data_field][col] = 0
        elif col == "pages" and is_story:
            new_item[data_field]["pages"] = []  # 初始化 pages 為空列表
        else:
            new_item[data_field][col] = ""
    json_data.append(new_item)
    update_table(tree, json_data, columns, key_field=key_field)
    save_json(file_path, json_data)

# 刪除選中項目
def delete_item(json_data, tree, columns, file_path, key_field="id"):
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("警告", "請選擇一項目進行刪除！")
        return
    item_id = tree.item(selected[0])["values"][0]
    confirm = messagebox.askyesno("確認刪除",f"您確定要刪除ID為{item_id}的項目嗎?")

    if not confirm:
        return

    for i, item in enumerate(json_data):
        if item[key_field] == item_id:
            del json_data[i]
            update_table(tree, json_data, columns, key_field=key_field)
            save_json(file_path, json_data)
            break

# 編輯窗口
def edit_window(root, item, tree, json_data, columns, file_path, key_field="id", data_field="data"):
    def save_changes():
        item[key_field] = entry_id.get()
        for col in columns[1:]:
            if col == "total":
                try:
                    item[data_field][col] = int(entries[col].get())  # 確保 total 是整數
                except ValueError:
                    messagebox.showerror("錯誤", f"{col} 必須是數字！")
                    return
            else:
                item[data_field][col] = entries[col].get()  # 其他欄位存為字串
        update_table(tree, json_data, columns, key_field=key_field)
        save_json(file_path, json_data)
        edit_win.destroy()
    
    edit_win = tk.Toplevel(root)
    edit_win.title("編輯項目")
    if key_field == "id":
        tk.Label(edit_win, text="ID：").grid(row=0, column=0, padx=5, pady=5, sticky="e")
    elif key_field == "story":
        tk.Label(edit_win, text="Story：").grid(row=0, column=0, padx=5, pady=5, sticky="e")
    entry_id = tk.Entry(edit_win, width=30)
    entry_id.insert(0, item[key_field])
    entry_id.grid(row=0, column=1, padx=5, pady=5)

    entries = {}
    for i, col in enumerate(columns[1:], start=1):
        tk.Label(edit_win, text=f"{col}：").grid(row=i, column=0, padx=5, pady=5, sticky="e")
        entry = tk.Entry(edit_win, width=30)
        entry.insert(0, item[data_field].get(col, ""))
        entry.grid(row=i, column=1, padx=5, pady=5)
        entries[col] = entry

    tk.Button(edit_win, text="保存", command=save_changes).grid(row=len(columns), column=0, columnspan=2, pady=10)

def edit_pages_window(root, story_item, tree, json_data, file_path):
    def update_pages_table():
        for row in pages_tree.get_children():
            pages_tree.delete(row)
        for i, page in enumerate(story_item["data"]["pages"]):
            pages_tree.insert("", "end", values=(i + 1, page["text"], page["audio"], page["image"], page["action"]))

    def add_page():
        new_page = {
            "text": "",
            "audio": "",
            "image": "",
            "action": ""
        }
        story_item["data"]["pages"].append(new_page)
        update_pages_table()

    def edit_page():
        selected = pages_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "請選擇一頁進行編輯！")
            return
        index = int(pages_tree.item(selected[0])["values"][0]) - 1
        edit_single_page_window(story_item["data"]["pages"][index])

    def delete_page():
        selected = pages_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "請選擇一頁進行刪除！")
            return
        index = int(pages_tree.item(selected[0])["values"][0]) - 1
        confirm = messagebox.askyesno("確認刪除",f"您確定要刪除Index為{index+1}的項目嗎?")

        if not confirm:
            return

        del story_item["data"]["pages"][index]
        update_pages_table()
        save_json(file_path, json_data)

    def save_changes():
        save_json(file_path, json_data)
        pages_win.destroy()

    def edit_single_page_window(page):
        def save_changes():
            page["text"] = entry_text.get()
            page["audio"] = entry_audio.get()
            page["image"] = entry_image.get()
            page["action"] = entry_action.get()
            single_page_win.destroy()
            update_pages_table()

        single_page_win = tk.Toplevel(root)
        single_page_win.title("編輯單頁內容")

        tk.Label(single_page_win, text="Text：").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        entry_text = tk.Entry(single_page_win, width=50)
        entry_text.insert(0, page["text"])
        entry_text.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(single_page_win, text="Audio：").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        entry_audio = tk.Entry(single_page_win, width=50)
        entry_audio.insert(0, page["audio"])
        entry_audio.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(single_page_win, text="Image：").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        entry_image = tk.Entry(single_page_win, width=50)
        entry_image.insert(0, page["image"])
        entry_image.grid(row=2, column=1, padx=5, pady=5)

        tk.Label(single_page_win, text="Action：").grid(row=3, column=0, padx=5, pady=5, sticky="e")
        entry_action = tk.Entry(single_page_win, width=50)
        entry_action.insert(0, page["action"])
        entry_action.grid(row=3, column=1, padx=5, pady=5)

        tk.Button(single_page_win, text="保存", command=save_changes).grid(row=4, column=0, columnspan=2, pady=10)

    pages_win = tk.Toplevel(root)
    pages_win.title(f"編輯故事：{story_item['data']['name']} 的頁面")

    # 表格顯示
    columns = ("Index", "Text", "Audio", "Image", "Action")
    pages_tree = ttk.Treeview(pages_win, columns=columns, show="headings", height=10)
    for col in columns:
        pages_tree.heading(col, text=col)
    pages_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # 按鈕區域
    frame_buttons = tk.Frame(pages_win)
    frame_buttons.pack(fill=tk.X, pady=5)

    tk.Button(frame_buttons, text="保存", command=save_changes).pack(side=tk.BOTTOM, padx=5)
    tk.Button(frame_buttons, text="新增頁面", command=add_page).pack(side=tk.LEFT, padx=5)
    tk.Button(frame_buttons, text="編輯頁面", command=edit_page).pack(side=tk.LEFT, padx=5)
    tk.Button(frame_buttons, text="刪除頁面", command=delete_page).pack(side=tk.LEFT, padx=5)

    update_pages_table()

def edit_pages_objects_window(root, story_item, tree, json_data, file_path):
    def update_pages_table():
        for row in pages_tree.get_children():
            pages_tree.delete(row)
        for i, page in enumerate(story_item["m_data"]["pages"]):
            pages_tree.insert(
                "", 
                "end", 
                values=(
                    i + 1, 
                    page["id"],
                    page["data"].get("name", ""), 
                    page["data"].get("image", ""),
                    page["data"].get("group", "")
                )
            )

    def add_page():
        new_page = {
            "id": "",
            "data": {
                "name": "",
                "image": "",
                "group": "",
                "sentence": "",
                "definition": "",
                "face": "",
                "action": "",
                "languages": [
                    {
                        "code": "zh_TW",
                        "tr_name": "",
                        "tr_sentence": ""
                    }
                ]
            }
        }
        story_item["m_data"]["pages"].append(new_page)
        update_pages_table()

    def edit_page():
        selected = pages_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "請選擇一頁進行編輯！")
            return
        index = int(pages_tree.item(selected[0])["values"][0]) - 1
        edit_single_page_window(story_item["m_data"]["pages"][index])

    def delete_page():
        selected = pages_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "請選擇一頁進行刪除！")
            return
        index = int(pages_tree.item(selected[0])["values"][0]) - 1
        confirm = messagebox.askyesno("確認刪除",f"您確定要刪除Index為{index+1}的項目嗎?")

        if not confirm:
            return
        
        del story_item["m_data"]["pages"][index]
        update_pages_table()
        save_json(file_path, json_data)

    def save_changes():
        save_json(file_path, json_data)
        pages_win.destroy()

    def edit_single_page_window(page):
        def save_changes():
            page["id"] = entry_id.get()
            page["data"]["name"] = entry_name.get()
            page["data"]["image"] = entry_image.get()
            page["data"]["group"] = entry_group.get()
            page["data"]["sentence"] = entry_sentence.get()
            page["data"]["definition"] = entry_definition.get()
            page["data"]["face"] = entry_face.get()
            page["data"]["action"] = entry_action.get()
            page["data"]["languages"][0]["code"] = entry_code.get()
            page["data"]["languages"][0]["tr_name"] = entry_tr_name.get()
            page["data"]["languages"][0]["tr_sentence"] = entry_tr_sentence.get()
            single_page_win.destroy()
            update_pages_table()
        
        def tk_label(text,row):
            tk.Label(single_page_win, text=f"{text}：").grid(row=row, column=0, padx=5, pady=5, sticky="e")
            entry_text = tk.Entry(single_page_win, width=50)
            entry_text.insert(0, page["data"].get(text))
            entry_text.grid(row=row, column=1, padx=5, pady=5)
            return entry_text
        
        def tk_language_label(text,row):
            tk.Label(single_page_win, text=f"{text}：").grid(row=row, column=0, padx=5, pady=5, sticky="e")
            entry_text = tk.Entry(single_page_win, width=50)
            entry_text.insert(0, page["data"]["languages"][0].get(text))
            entry_text.grid(row=row, column=1, padx=5, pady=5)
            return entry_text
        
        single_page_win = tk.Toplevel(root)
        single_page_win.title("編輯單頁內容")

        tk.Label(single_page_win, text="ID：").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        entry_id = tk.Entry(single_page_win, width=50)
        entry_id.insert(0, page["id"])
        entry_id.grid(row=0, column=1, padx=5, pady=5)

        entry_name = tk_label(text="name",row=1)
        entry_image = tk_label(text="image",row=2)
        entry_group = tk_label(text="group",row=3)
        entry_sentence = tk_label(text="sentence",row=4)
        entry_definition = tk_label(text="definition",row=5)
        entry_face = tk_label(text="face",row=6)
        entry_action = tk_label(text="action",row=7)
        tk.Label(single_page_win, text="language：").grid(row=8, column=0, padx=5, pady=5, sticky="e")
        entry_code = tk_language_label(text="code",row=9)
        entry_tr_name = tk_language_label(text="tr_name",row=10)
        entry_tr_sentence = tk_language_label(text="tr_sentence",row=11)

        tk.Button(single_page_win, text="保存", command=save_changes).grid(row=12, column=0, columnspan=2, pady=10)

    pages_win = tk.Toplevel(root)
    pages_win.title(f"編輯故事：{story_item['m_data']['story_name']} 的頁面")

    # 表格顯示
    columns = ("Index", "ID", "Name", "Image", "Group")
    pages_tree = ttk.Treeview(pages_win, columns=columns, show="headings", height=10)
    for col in columns:
        pages_tree.heading(col, text=col)
    pages_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # 按鈕區域
    frame_buttons = tk.Frame(pages_win)
    frame_buttons.pack(fill=tk.X, pady=5)

    tk.Button(frame_buttons, text="保存", command=save_changes).pack(side=tk.BOTTOM, padx=5)
    tk.Button(frame_buttons, text="新增頁面", command=add_page).pack(side=tk.LEFT, padx=5)
    tk.Button(frame_buttons, text="編輯頁面", command=edit_page).pack(side=tk.LEFT, padx=5)
    tk.Button(frame_buttons, text="刪除頁面", command=delete_page).pack(side=tk.LEFT, padx=5)

    update_pages_table()

def edit_pages_vocabularies_window(root, story_item, tree, json_data, file_path):
    def update_pages_table():
        for row in pages_tree.get_children():
            pages_tree.delete(row)
        for i, page in enumerate(story_item["data"]["vocabularies"]):
            pages_tree.insert(
                "",
                "end", 
                values=(
                    i + 1, 
                    page["name"], 
                    page["translated"],
                    page["definition"], 
                    page["part_of_speech"]
                )
            )

    def add_page():
        new_page = {
            "name": "",
            "translated": "",
            "definition": "",
            "part_of_speech": "",
            "image": "",
            "audio": "",
            "action": ""
        }
        story_item["data"]["vocabularies"].append(new_page)
        update_pages_table()

    def edit_page():
        selected = pages_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "請選擇一頁進行編輯！")
            return
        index = int(pages_tree.item(selected[0])["values"][0]) - 1
        edit_single_page_window(story_item["data"]["vocabularies"][index])

    def delete_page():
        selected = pages_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "請選擇一頁進行刪除！")
            return
        index = int(pages_tree.item(selected[0])["values"][0]) - 1
        confirm = messagebox.askyesno("確認刪除",f"您確定要刪除Index為{index+1}的項目嗎?")

        if not confirm:
            return
        
        del story_item["data"]["vocabularies"][index]
        update_pages_table()
        save_json(file_path, json_data)

    def save_changes():
        save_json(file_path, json_data)
        pages_win.destroy()

    def edit_single_page_window(page):
        def save_changes():
            page["name"] = entry_name.get()
            page["translated"] = entry_translated.get()
            page["definition"] = entry_definition.get()
            page["part_of_speech"] = entry_part_of_speech.get()
            page["image"] = entry_image.get()
            page["audio"] = entry_audio.get()
            page["action"] = entry_action.get()
            single_page_win.destroy()
            update_pages_table()
        
        def tk_label(text,row):
            tk.Label(single_page_win, text=f"{text}：").grid(row=row, column=0, padx=5, pady=5, sticky="e")
            entry_text = tk.Entry(single_page_win, width=50)
            entry_text.insert(0, page[text])
            entry_text.grid(row=row, column=1, padx=5, pady=5)
            return entry_text

        single_page_win = tk.Toplevel(root)
        single_page_win.title("編輯單頁內容")

        entry_name = tk_label(text="name", row=0)
        entry_translated = tk_label(text="translated", row=1)
        entry_definition = tk_label(text="definition", row=2)
        entry_part_of_speech = tk_label(text="part_of_speech", row=3)
        entry_image = tk_label(text="image", row=4)
        entry_audio = tk_label(text="audio", row=5)
        entry_action = tk_label(text="action", row=6)

        tk.Button(single_page_win, text="保存", command=save_changes).grid(row=7, column=0, columnspan=2, pady=10)

    pages_win = tk.Toplevel(root)
    pages_win.title(f"編輯故事：{story_item['data']['vocabularies']} 的頁面")

    # 表格顯示
    columns = ("Index", "Name", "Translated", "Definition", "Part_Of_Speech")
    pages_tree = ttk.Treeview(pages_win, columns=columns, show="headings", height=10)
    for col in columns:
        pages_tree.heading(col, text=col)
    pages_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # 按鈕區域
    frame_buttons = tk.Frame(pages_win)
    frame_buttons.pack(fill=tk.X, pady=5)

    tk.Button(frame_buttons, text="保存", command=save_changes).pack(side=tk.BOTTOM, padx=5)
    tk.Button(frame_buttons, text="新增頁面", command=add_page).pack(side=tk.LEFT, padx=5)
    tk.Button(frame_buttons, text="編輯頁面", command=edit_page).pack(side=tk.LEFT, padx=5)
    tk.Button(frame_buttons, text="刪除頁面", command=delete_page).pack(side=tk.LEFT, padx=5)

    update_pages_table()

def get_selected_item(tree, json_data, key_field="id"):
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("警告", "請選擇一項目進行操作！")
        return None
    item_id = tree.item(selected[0])["values"][0]  # 提取選中項目的 ID
    for item in json_data:
        if item[key_field] == item_id:
            return item
    return None

# 主窗口
root = tk.Tk()
root.title("資料管理             注意:id、story位置必須為英文")

# Notebook
notebook = ttk.Notebook(root)
notebook.pack(fill=tk.BOTH, expand=True)

# Faces 標籤頁
faces_tab = tk.Frame(notebook)
notebook.add(faces_tab, text="Faces 資料管理")

faces_title = ("id")
faces_columns = ("id", "name", "sentence","face","image","action","tr_name","tr_sentence")
faces_json_data = load_json(FACES_FILE_PATH)

faces_tree = ttk.Treeview(faces_tab, columns=faces_columns, show="headings", height=10)
for col in faces_columns:
    faces_tree.heading(col, text=col)
faces_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

faces_btn_frame = tk.Frame(faces_tab)
faces_btn_frame.pack(fill=tk.X, pady=5)

tk.Button(
    faces_btn_frame, 
    text="新增", 
    command=lambda: add_item(
        faces_json_data, 
        faces_tree, 
        faces_columns, 
        FACES_FILE_PATH
    )
).pack(side=tk.LEFT, padx=5)

tk.Button(
    faces_btn_frame,
    text="編輯",
    command=lambda: (
        selected_faces := get_selected_item(faces_tree, faces_json_data),
        selected_faces and edit_window(
            root,
            selected_faces,
            faces_tree,
            faces_json_data,
            faces_columns,
            FACES_FILE_PATH
        )
    )
).pack(side=tk.LEFT, padx=5)

tk.Button(
    faces_btn_frame, 
    text="刪除", 
    command=lambda: delete_item(
        faces_json_data, 
        faces_tree, 
        faces_columns, 
        FACES_FILE_PATH
    )
).pack(side=tk.LEFT, padx=5)

update_table(faces_tree, faces_json_data, faces_columns)

# object 標籤頁
objects_tab = tk.Frame(notebook)
notebook.add(objects_tab, text="object 資料管理")

object_pages_columns = ("story", "story_name", "total", "pages")
object_columns = ("story", "story_name", "total")
object_json_data = load_json(OBJECT_FILE_PATH)

objects_tree = ttk.Treeview(objects_tab, columns=object_columns, show="headings", height=10)
for col in object_columns:
    objects_tree.heading(col, text=col)
objects_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

object_btn_frame = tk.Frame(objects_tab)
object_btn_frame.pack(fill=tk.X, pady=5)

tk.Button(
    object_btn_frame,
    text="新增",
    command=lambda:add_item_stories(
        object_json_data,
        objects_tree,
        object_pages_columns,
        OBJECT_FILE_PATH,
        is_story=True,
        key_field="story"
    )
).pack(side=tk.LEFT, padx=5)

tk.Button(
    object_btn_frame,
    text="編輯",
    command=lambda:(
        selected_object := get_selected_item(objects_tree, object_json_data, key_field="story"),
        selected_object and edit_window(
            root,
            selected_object,
            objects_tree,
            object_json_data,
            object_columns,
            OBJECT_FILE_PATH,
            key_field="story",
            data_field="m_data"
        )
    )[1]
).pack(side=tk.LEFT, padx=5)

tk.Button(
    object_btn_frame,
    text="編輯頁面",
    command=lambda:(
        selected_object := get_selected_item(objects_tree, object_json_data, key_field="story"),
        selected_object and edit_pages_objects_window(
            root,
            selected_object,
            objects_tree,
            object_json_data,
            OBJECT_FILE_PATH
        )
    )[1]
).pack(side=tk.LEFT, padx=5)

tk.Button(
    object_btn_frame,
    text="刪除",
    command=lambda:delete_item(
        object_json_data,
        objects_tree,
        object_columns,
        OBJECT_FILE_PATH,
        key_field="story"
    )
).pack(side=tk.LEFT, padx=5)

update_table(objects_tree, object_json_data, object_columns, key_field="story")

# Stories 標籤頁
stories_tab = tk.Frame(notebook)
notebook.add(stories_tab, text="Stories 資料管理")

stories_pages_columns = ("id", "name", "total", "pages")
stories_columns = ("id", "name", "total")
stories_json_data = load_json(STORIES_FILE_PATH)

stories_tree = ttk.Treeview(stories_tab, columns=stories_columns, show="headings", height=10)
for col in stories_columns:
    stories_tree.heading(col, text=col)
stories_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

stories_btn_frame = tk.Frame(stories_tab)
stories_btn_frame.pack(fill=tk.X, pady=5)

tk.Button(
    stories_btn_frame,
    text="新增",
    command=lambda: add_item_stories(stories_json_data, stories_tree, stories_pages_columns, STORIES_FILE_PATH, is_story=True)
).pack(side=tk.LEFT, padx=5)

tk.Button(
    stories_btn_frame,
    text="編輯",
    command=lambda: (
        selected_story := get_selected_item(stories_tree,stories_json_data),
        selected_story and edit_window(
            root,
            selected_story,
            stories_tree,
            stories_json_data,
            stories_columns,
            STORIES_FILE_PATH
        )
    )[1]
).pack(side=tk.LEFT, padx=5)

tk.Button(
    stories_btn_frame,
    text="編輯頁面",
    command=lambda: (
        selected_story := get_selected_item(stories_tree, stories_json_data),
        selected_story and edit_pages_window(root, selected_story, stories_tree, stories_json_data, STORIES_FILE_PATH)
    )[1]
).pack(side=tk.LEFT, padx=5)

tk.Button(
    stories_btn_frame, 
    text="刪除", 
    command=lambda: delete_item(
        stories_json_data, 
        stories_tree, 
        stories_columns, 
        STORIES_FILE_PATH
    )
).pack(side=tk.LEFT, padx=5)

update_table(stories_tree, stories_json_data, stories_columns)

# vocabularies 標籤頁
vocabularies_tab = tk.Frame(notebook)
notebook.add(vocabularies_tab, text="vocabularies 資料管理")

vocabularies_pages_columns = ("id", "name", "vocabularies")
vocabularies_columns = ("id", "name")
vocabularies_json_data = load_json(VOCABULARIES_FILE_PATH)

vocabularies_tree = ttk.Treeview(vocabularies_tab, columns=vocabularies_columns, show="headings", height=10)
for col in vocabularies_columns:
    vocabularies_tree.heading(col, text=col)
vocabularies_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

vocabularies_btn_frame = tk.Frame(vocabularies_tab)
vocabularies_btn_frame.pack(fill=tk.X, pady=5)

tk.Button(
    vocabularies_btn_frame,
    text="新增",
).pack(side=tk.LEFT, padx=5)

tk.Button(
    vocabularies_btn_frame,
    text="編輯",
    command=lambda:(
        selected_vocabularies := get_selected_item(vocabularies_tree, vocabularies_json_data),
        selected_vocabularies and edit_window(
            root,
            selected_vocabularies,
            vocabularies_tree,
            vocabularies_json_data,
            vocabularies_columns,
            VOCABULARIES_FILE_PATH
        )
    )[1]
).pack(side=tk.LEFT, padx=5)

tk.Button(
    vocabularies_btn_frame,
    text="編輯頁面",
    command=lambda:(
        selected_vocabularies := get_selected_item(vocabularies_tree, vocabularies_json_data),
        selected_vocabularies and edit_pages_vocabularies_window(
            root,
            selected_vocabularies,
            vocabularies_tree,
            vocabularies_json_data,
            VOCABULARIES_FILE_PATH
        )
    )[1]
).pack(side=tk.LEFT, padx=5)

tk.Button(
    vocabularies_btn_frame,
    text="刪除",
).pack(side=tk.LEFT, padx=5)

update_table(vocabularies_tree, vocabularies_json_data, vocabularies_columns)
# 主循環
root.mainloop()
