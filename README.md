# 🎨 ToonForge – Desktop Cartoonifier

**ToonForge** is a lightweight desktop application that converts images into cartoon-style artwork using classic computer vision techniques.
It is built with **Python**, **OpenCV**, and **Tkinter**, and runs fully offline.

The app provides an interactive UI to experiment with smoothing, edge detection, color quantization, and blending modes.
Using the Preview button, all intermediate processing steps are visualized.

---

## ✨ Features

* Load and process image files (JPG, PNG, etc.)
* Multiple **cartoon presets**
* Adjustable parameters:
  * Smoothing type & strength
  * Edge detection intensity
  * Color quantization mode & depth
  * Blend modes
* Visual preview of **all pipeline steps**
  * Preview processing is performed on a downscaled copy of the image (~40%) for faster feedback
  * The final **Cartoonify** action processes the original image at full resolution for best quality
* Desktop GUI (no browser required)
* Offline processing (CPU-only)

---

## 🧭 Main Actions

* **Open Image**
  Loads an image file to be processed. The original image is always displayed in the left panel.

* **Preview**
  Runs the cartoon pipeline on a downscaled copy of the image and displays all intermediate processing steps, including grayscale, edges, smoothing, color quantization, and the final cartoon result.


* **Cartoonify**
  Processes the image using the selected settings and shows only the final cartoon result.

* **Save Image**
  Saves the final cartoonized image next to the original file with the `_cartoon` suffix.
  If a file with the same name already exists, a numbered suffix is added automatically.

* **Presets**
  Quickly apply predefined combinations of parameters.
  When any setting is changed manually, the preset switches to **Custom**.

---

## 🖥️ Requirements

* Python **3.10+** recommended
* Works on Windows (tested)
* No GPU required

---

## 📦 Installation (Development / Run from source)

### 1️⃣ Clone the repository

```bash
git clone https://github.com/ApoGouv/toonforge-deskapp.git
cd toonforge-deskapp
```

### 2️⃣ Create & activate a virtual environment

```bash
python -m venv .venv
```

**Windows**

```bash
.venv\Scripts\activate
```

**macOS / Linux**

```bash
source .venv/bin/activate
```

### 3️⃣ Install runtime dependencies

These are the **minimum packages required to run the app**:

```bash
pip install -r requirements.txt
```

### 4️⃣ Run the app

```bash
python main.py
```

---

## 📄 `requirements.txt` (Runtime)

This file contains **what the app needs to run**:

```text
numpy
opencv-python
pillow
```

Keeping this file small ensures:

* Faster installs
* Cleaner environments
* Easier troubleshooting

---

## 🛠️ Packaging & Distribution (PyInstaller)

Packaging is **optional** and only needed if you want to distribute a standalone `.exe`.


### 📄 `requirements-dev.txt` (Development / Packaging)

This file contains **build-time dependencies only**, such as:

* `pyinstaller`
* `pyinstaller-hooks-contrib`
* Windows-specific helpers

### 🧩 PyInstaller Spec File

`ToonForge.spec` defines:

* Entry point (`main.py`)
* Included OpenCV binaries
* Hidden imports
* Application metadata (windowed mode, name)


### 1️⃣ Install packaging dependencies

```bash
pip install -r requirements-dev.txt
```

This includes tools like **PyInstaller** and its helpers.

---

### 2️⃣ Build the executable

Use the existing spec file:

```bash
pyinstaller ToonForge.spec
```

After a successful build, you will find the executable in:

```text
dist/ToonForge.exe
```

---

## 📜 License

This project is licensed under the MIT License.
See the LICENSE file for details.
