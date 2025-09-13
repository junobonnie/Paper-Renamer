# Paper-Renamer

https://github.com/user-attachments/assets/d24e5ea9-c5da-4740-8abf-779c2f84b481

<br>

**Paper-Renamer** is a convenient Windows tool that automatically renames research paper PDF files based on their titles and author names.
<br>
It supports arXiv papers, extracts metadata, and helps you organize your PDF library with clean and consistent filenames.


### Example
<img width="25%" alt="image" src="https://github.com/user-attachments/assets/17f2f88c-55e1-4a12-8a3f-54ad37d092e0" />


"2409.08956v1.pdf" -> "Discovery Opportunities with Gravitational Waves -- TASI 2024 Lecture Notes - Valerie Domcke.pdf"


---

## ✨ Features

* **Automatic PDF renaming**
  Extracts paper titles and authors to rename files in the format:

  * `Title - Author.pdf`
  * `Title.pdf`

* **arXiv support**
  Automatically retrieves metadata (title, author) from the arXiv API if an arXiv ID is detected.

* **PDF metadata analysis**
  If no arXiv info is found, metadata inside the PDF is analyzed to extract title and author.

* **Author include/exclude option**
  Toggle whether to include author names in the filename.

* **Skip already titled files**
  Automatically skips files that already have proper titles.

* **Duplicate filename prevention**
  Adds `(1)`, `(2)`, etc. when duplicate filenames occur.

* **Intuitive GUI**
  Built with CustomTkinter for a clean and user-friendly interface.

* **Settings auto-save**
  Selected folders and options are saved automatically.

* **Completion notification**
  Pop-up and sound alert when the process is finished.

---

## 🚀 How to Use

1. Launch the program and click **"Folder"** to select the folder containing your PDF files.
2. Use the **"Author"** checkbox to decide whether to include author names in filenames.
3. Use the **"Forced"** checkbox to enable forced renaming.

   * Check this if you want to rename files even if they already have proper titles.
4. Click **"Run"** to start renaming.
5. Monitor progress and results in the log box at the bottom.

---

## 📥 Installation

* ### [Download for Windows](https://github.com/junobonnie/Paper-Renamer/releases/download/v1.0.0/v1.0.0.zip)


