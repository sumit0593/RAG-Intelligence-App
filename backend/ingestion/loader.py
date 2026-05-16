import os
import fitz  # PyMuPDF
import pandas as pd
import json

def load_pdf(file_path: str) -> str:
    text = ""
    try:
        doc = fitz.open(file_path)
        for page in doc:
            text += page.get_text()
    except Exception as e:
        print(f"Error loading PDF {file_path}: {e}")
    return text

def load_csv(file_path: str) -> str:
    try:
        df = pd.read_csv(file_path)
        return df.to_string()
    except Exception as e:
        print(f"Error loading CSV {file_path}: {e}")
        return ""

def load_json(file_path: str) -> str:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return json.dumps(data, indent=2)
    except Exception as e:
        print(f"Error loading JSON {file_path}: {e}")
        return ""

def load_txt(file_path: str) -> str:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error loading TXT {file_path}: {e}")
        return ""

def load_document(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.pdf':
        return load_pdf(file_path)
    elif ext == '.csv':
        return load_csv(file_path)
    elif ext == '.json':
        return load_json(file_path)
    elif ext == '.txt':
        return load_txt(file_path)
    else:
        raise ValueError(f"Unsupported file extension: {ext}")
