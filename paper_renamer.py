# -*- coding: utf-8 -*-
"""
Created on Fri Sep 12 16:45:39 2025

@author: replica
"""

import os
import re
import json
import requests
import xml.etree.ElementTree as ET
from PyPDF2 import PdfReader
import customtkinter as ctk
from CTkToolTip import *
from tkinter import filedialog
from PIL import Image
import webbrowser
from random import randint

RED = "#a31f5f"
GREEN = "#1fa372"
CONFIG_FILE = "config.json"

# ---------------------------
# Config 함수
# ---------------------------
def load_config():
    default_config = {
        "folder": "",
        "include_author": 1,
        "forced": 0
    }
    if not os.path.exists(CONFIG_FILE):
        return default_config
    
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
        # 키 검증
        for k in default_config:
            if k not in config or not isinstance(config[k], type(default_config[k])):
                raise ValueError("Invalid config")
        return config
    except Exception:
        save_config(default_config)
        return default_config

def save_config(config):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except:
        pass

# ---------------------------
# PDF 처리 함수들
# ---------------------------
def sanitize_filename(name: str) -> str:
    name = name.replace("\n", " ").replace("\r", " ").strip()
    name = re.sub(r"\s+", " ", name)
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    return name[:180]

def extract_arxiv_id(filepath: str) -> str:
    """
    PDF 파일에서 arXiv ID 추출 후,
    해당 ID의 논문 제목이 PDF 첫 2페이지 텍스트에 포함되는지 확인.
    포함되면 (arxiv_id, version) 반환, 아니면 None 반환.
    """
    try:
        reader = PdfReader(filepath)
        text = ""
        # 앞부분 2페이지 정도만 확인
        for page in reader.pages[:1]:
            text += page.extract_text() or ""

        # 정규식으로 arXiv ID 추출
        match = re.search(r'arXiv:(\d{4}\.\d{4,5})(v\d+)?', text)
        if not match:
            return None

        arxiv_id = match.group(1)

        # arXiv API에서 메타데이터 가져오기
        api_url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"
        resp = requests.get(api_url, timeout=10)
        if resp.status_code != 200:
            return None
        # API 응답에는 첫 번째 <title>은 "arXiv Query Results" 이므로 두 번째 <title>을 사용
        titles = re.findall(r"<title>(.*?)</title>", resp.text, re.S)
        arxiv_title = titles[0].strip()

        # PDF 텍스트 안에 제목이 포함되는지 확인 (공백 제거 후 대소문자 무시)
        pdf_text_norm = " ".join(text.split()).lower()
        title_norm = " ".join(arxiv_title.split()).lower()

        if title_norm in pdf_text_norm:
            return arxiv_id
        else:
            return None

    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def get_arxiv_metadata(arxiv_id: str):
    url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"
    try:
        response = requests.get(url, timeout=10)
    except:
        return None, None
    if response.status_code != 200:
        return None, None

    root = ET.fromstring(response.text)
    entry = root.find("{http://www.w3.org/2005/Atom}entry")
    if entry is None:
        return None, None

    # 제목
    title_elem = entry.find("{http://www.w3.org/2005/Atom}title")
    title = title_elem.text.strip() if title_elem is not None else None

    # 저자
    authors = entry.findall("{http://www.w3.org/2005/Atom}author/{http://www.w3.org/2005/Atom}name")
    authors = [a.text.strip() for a in authors if a.text]
    if len(authors) > 3:
        author_str = f"{authors[0]} et al."
    else:
        author_str = ", ".join(authors)

    return title, author_str

def get_pdf_metadata(filepath: str):
    try:
        reader = PdfReader(filepath)
        title = reader.metadata.title if reader.metadata.title else None
        author = reader.metadata.author if reader.metadata.author else None
        return title, author
    except:
        return None, None

def is_probably_title(filename: str) -> bool:
    name = os.path.splitext(filename)[0]
    words = re.split(r"[\s_\-]+", name)
    if len(words) >= 3 and sum(len(w) >= 3 for w in words) >= 3:
        letters = sum(c.isalpha() for c in name)
        if letters / max(len(name), 1) > 0.3:
            return True
    return False

# ---------------------------
# GUI 동작
# ---------------------------
def select_folder():
    folder = filedialog.askdirectory()
    if folder:
        folder_path.set(folder)
        # 선택한 폴더의 PDF 파일 목록 표시
        pdf_files = [f for f in os.listdir(folder) if f.lower().endswith(".pdf")]
        log(f"📂 Selected folder: {folder}")
        if pdf_files:
            log(f"Found {len(pdf_files)} PDF(s):")
            for f in pdf_files:
                log(f"  - {f}")
        else:
            log("⚠️ No PDF files found in the folder.")

def process_pdfs():
    btn_run.configure(state="disabled")
    status_label.configure(text_color=RED)
    folder = folder_path.get()
    if not os.path.isdir(folder):
        log("❌ Invalid folder.")
        
        btn_run.configure(state="normal")
        status_label.configure(text_color=GREEN)
        return

    pdf_files = [f for f in os.listdir(folder) if f.lower().endswith(".pdf")]
    total = len(pdf_files)
    if total == 0:
        log("⚠️ No PDF files found.")
        
        btn_run.configure(state="normal")
        status_label.configure(text_color=GREEN)
        return

    for idx, filename in enumerate(pdf_files, start=1):
        filepath = os.path.join(folder, filename)
        
        if forced.get() == 0:
            if is_probably_title(filename):
                log(f"[SKIP] Already has title → {filename}")
                progress.set(idx / total)
                app.update_idletasks()
                continue

        match = re.search(r'(\d{4}\.\d{4,5})(v\d+)?', filename)
        title, author = None, None

        if match:
            arxiv_id = match.group(1)
            title, author = get_arxiv_metadata(arxiv_id)
            
        else:
            arxiv_id = extract_arxiv_id(filepath)
            if arxiv_id:
                title, author = get_arxiv_metadata(arxiv_id)
            
        if not title or not author:
            pdf_title, pdf_author = get_pdf_metadata(filepath)
            if not title:
                title = pdf_title
            if not author:
                author = pdf_author

        if not title or title.strip() == "":
            log(f"[SKIP] No title → {filename}")
            progress.set(idx / total)
            app.update_idletasks()
            continue

        # 안전한 파일명 생성
        safe_title = sanitize_filename(title)

        if include_author.get() == 1 and author:  # 체크박스 선택 시만 저자 포함
            safe_author = sanitize_filename(author)
            new_filename = f"{safe_title} - {safe_author}.pdf"
        else:
            new_filename = f"{safe_title}.pdf"

        new_filepath = os.path.join(folder, new_filename)

        # 중복 방지
        counter = 1
        if not filename == new_filename:
            while os.path.exists(new_filepath):
                if include_author.get() == 1 and author:
                    new_filename = f"{safe_title} - {safe_author} ({counter}).pdf"
                else:
                    new_filename = f"{safe_title} ({counter}).pdf"
                new_filepath = os.path.join(folder, new_filename)
                counter += 1

            os.rename(filepath, new_filepath)
        log(f"[OK] {filename} → {new_filename}")

        progress.set(idx / total)
        app.update_idletasks()

    log("✅ All PDF files processed!")
    
    btn_run.configure(state="normal")
    status_label.configure(text_color=GREEN)
    download_complete_popup()
    progress.set(0)
    
def get_popup_pos(popup_width, popup_height):
    app_x = app.winfo_x()  # 메인 창의 X 좌표
    app_y = app.winfo_y()  # 메인 창의 Y 좌표
    app_width = app.winfo_width()  # 메인 창의 너비
    app_height = app.winfo_height()  # 메인 창의 높이

    # 팝업 창 위치 계산 (메인 창 중심)
    popup_x = app_x + (app_width // 2) - (popup_width // 2)
    popup_y = app_y + (app_height // 2) - (popup_height // 2)
    return popup_x, popup_y

def download_complete_popup():
    popup_width, popup_height = 100, 50
    popup_x, popup_y = get_popup_pos(popup_width, popup_height)
    
    new_popup = ctk.CTkToplevel(app)
    new_popup.iconbitmap("icon/icon%d.ico"%(randint(0, 14)))
    new_popup.geometry(f"{popup_width}x{popup_height}+{popup_x}+{popup_y}")
    new_popup.title("")
    new_popup.grab_set()
    label = ctk.CTkLabel(new_popup, text="Complete!")
    label.place(relx=0.5, rely=0.5, anchor=ctk.CENTER)
    
def open_github():
    github_url = "https://github.com/junobonnie/chzzk_pay_amount_calculator"  # 이동할 GitHub 페이지 URL
    webbrowser.open(github_url)  

def log(message):
    log_box.configure(state="normal")
    log_box.insert("end", message + "\n")
    log_box.configure(state="disabled")
    log_box.see("end")

# ---------------------------
# customtkinter GUI
# ---------------------------
ctk.set_appearance_mode("dark")

# 설정 불러오기
config = load_config()

app = ctk.CTk()
app.title("Paper Renamer")
app.geometry("500x500")
app.iconbitmap("icon/icon%d.ico"%(randint(0, 14)))

frame = ctk.CTkFrame(app, fg_color="transparent")
frame.pack(pady=10, padx=20, fill="x")

folder_path = ctk.StringVar(value=config["folder"])   # config 반영

btn_select = ctk.CTkButton(frame, text="Folder", width=70,
                           fg_color="#c13036", 
                           hover_color="#781e29", command=select_folder)
btn_select.pack(side="left", padx=(7,0), pady=10)

entry_folder = ctk.CTkEntry(frame, textvariable=folder_path, width=400)
entry_folder.pack(side="left", padx=10, pady=10, fill="x", expand=True)

check_frame = ctk.CTkFrame(app, fg_color="transparent")
check_frame.pack(pady=(0,10), padx=20, fill="x")

# 저자 포함 옵션
include_author = ctk.IntVar(value=config["include_author"])  
chk_author = ctk.CTkCheckBox(check_frame, text="Author", 
                           fg_color="#c13036", 
                           hover_color="#781e29", variable=include_author, onvalue=1, offvalue=0)
chk_author.pack(side="left", padx=7)
CTkToolTip(chk_author, delay=0.5, message="If checked, the author's name will be included in the filename.")

# 강제 옵션
forced = ctk.IntVar(value=config["forced"])  
chk_forced = ctk.CTkCheckBox(check_frame, text="Forced", 
                           fg_color="#c13036", 
                           hover_color="#781e29", variable=forced, onvalue=1, offvalue=0)
chk_forced.pack(side="left", padx=7)
CTkToolTip(chk_forced, delay=0.5, message="If checked, the file will be renamed even if a plausible title already exists.")

git_logo = ctk.CTkImage(dark_image=Image.open("icon/github-mark-white.png"))
btn_info = ctk.CTkButton(check_frame, image=git_logo, text="", width=55,
                           fg_color="#000000", #"#c13036", 
                           hover_color="#888888", command=open_github)
btn_info.pack(side="right", padx=7)

# 다운로드 버튼
download_frame = ctk.CTkFrame(app, fg_color="transparent")
download_frame.pack(padx=20, pady=10, fill='x')

progress = ctk.DoubleVar()
progressbar = ctk.CTkProgressBar(download_frame, 
                           progress_color="#c13036", variable=progress)
progressbar.pack(side='left', fill="x", padx=10, expand=True)

status_label = ctk.CTkLabel(download_frame, text="●", text_color="#1fa372")
status_label.pack(side="left", padx=5)

btn_run = ctk.CTkButton(download_frame, text="Run", width=50,
                           fg_color="#c13036", 
                           hover_color="#781e29", command=process_pdfs)
btn_run.pack(side="right", padx=10)

log_box = ctk.CTkTextbox(app, height=250)
log_box.pack(fill="both", padx=20, pady=10, expand=True)
log_box.configure(state="disabled")

# 종료 시 config 저장
def on_closing():
    cfg = {
        "folder": folder_path.get(),
        "include_author": include_author.get(),
        "forced": forced.get()
    }
    save_config(cfg)
    app.destroy()

app.protocol("WM_DELETE_WINDOW", on_closing)
app.mainloop()
