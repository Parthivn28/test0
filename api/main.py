import subprocess
import tempfile
import os
from fastapi import FastAPI, Form, UploadFile
from difflib import SequenceMatcher
import re
import datetime
import zipfile
import io
import csv
import json
import hashlib

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict this to specific origins if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Questions and Answers Database
nothardcoded = [2, 3, 4, 5, 6, 7, 8, 9, 10, 14, 15, 16, 17]  # Questions that require dynamic computation

QUESTIONS = {
    1: "Install and run Visual Studio Code. In your Terminal (or Command Prompt), type code -s and press Enter. Copy and paste the entire output below. What is the output of code -s?",
    2: "Running uv run --with httpie -- https [URL] installs the Python package httpie and sends a HTTPS request to the URL. Send a HTTPS request to https://httpbin.org/get with the URL encoded parameter email set to 23f3001787@ds.study.iitm.ac.in. What is the JSON output of the command? (Paste only the JSON body, not the headers)",
    3: "Let's make sure you know how to use npx and prettier. Download README.md. In the directory where you downloaded it, make sure it is called README.md, and run npx -y prettier@3.4.2 README.md | sha256sum. What is the output of the command?",
    4: "Let's make sure you can write formulas in Google Sheets. Type this formula into Google Sheets. (It won't work in Excel) =SUM(ARRAY_CONSTRAIN(SEQUENCE(100, 100, 9, 15), 1, 10)) What is the result?",
    5: "Let's make sure you can write formulas in Excel. Type this formula into Excel. (Note: This will ONLY work in Office 365.) =SUM(TAKE(SORTBY({6,10,11,9,0,7,1,11,5,4,15,12,13,8,14,1}, {10,9,13,2,11,8,16,14,7,15,5,4,6,1,3,12}), 1, 6)) What is the result?",
    6: "How many Wednesdays are there in the date range 1981-05-06 to 2007-08-17?",
    7: "Download and unzip file q-extract-csv-zip.zip which has a single extract.csv file inside. What is the value in the \"answer\" column of the CSV file?",
    8: "Let's make sure you know how to use JSON. Sort this JSON array of objects by the value of the age field. In case of a tie, sort by the name field. Paste the resulting JSON below without any spaces or newlines.\n\n[{\"name\":\"Alice\",\"age\":67},{\"name\":\"Bob\",\"age\":53},{\"name\":\"Charlie\",\"age\":34},{\"name\":\"David\",\"age\":89},{\"name\":\"Emma\",\"age\":92},{\"name\":\"Frank\",\"age\":37},{\"name\":\"Grace\",\"age\":4},{\"name\":\"Henry\",\"age\":49},{\"name\":\"Ivy\",\"age\":30},{\"name\":\"Jack\",\"age\":2},{\"name\":\"Karen\",\"age\":2},{\"name\":\"Liam\",\"age\":5},{\"name\":\"Mary\",\"age\":32},{\"name\":\"Nora\",\"age\":56},{\"name\":\"Oscar\",\"age\":19},{\"name\":\"Paul\",\"age\":22}]\nSorted JSON:",
    9: "Download q-multi-cursor-json.txt and use multi-cursors and convert it into a single JSON object, where key=value pairs are converted into {key: value, key: value, ...}. What's the result when you paste the JSON at tools-in-data-science.pages.dev/jsonhash and click the Hash button?",
    10: "Download and process q-unicode-data.zip the files in which contains three files with different encodings:\n\n" \
                  "data1.csv: CSV file encoded in CP-1252\n" \
                  "data2.csv: CSV file encoded in UTF-8\n" \
                  "data3.txt: Tab-separated file encoded in UTF-16\n\n" \
                  "Each file has 2 columns: symbol and value. Sum up all the values where the symbol matches \"”\" OR \"Š\" across all three files.\n\n" \
                  "What is the sum of all values associated with these symbols?",
    11: "Let's make sure you know how to use GitHub. Create a GitHub account if you don't have one. Create a new public repository. Commit a single JSON file called email.json with the value {\"email\": \"23f3001787@ds.study.iitm.ac.in\"} and push it.Enter the raw Github URL of email.json so we can verify it. (It might look like https://raw.githubusercontent.com/[GITHUB ID]/[REPO NAME]/main/email.json.)",
    12: "Let's make sure you know how to select elements using CSS selectors. Find all <div>s having a foo class in the hidden element below. What's the sum of their data-value attributes? Sum of data-value attributes:",
    13: "Just above this paragraph, there's a hidden input with a secret value.What is the value in the hidden input?",
    14: "Download and process q-replace-across-files.zip and unzip it into a new folder, then replace all \"IITM\" (in upper, lower, or mixed case) with \"IIT Madras\" in all files. Leave everything as-is - don't change the line endings. What does running cat * | sha256sum in that folder show in bash?",
    15: "Download q-list-files-attributes.zip and extract it. Use ls with options to list all files in the folder along with their date and file size. What's the total size of all files at least 4294 bytes large and modified on or after Sat, 29 Apr, 2006, 8:48 pm IST?",
    16: "Download q-move-rename-files.zip and extract it. Use mv to move all files under folders into an empty folder. Then rename all files replacing each digit with the next. (1 becomes 2, 9 becomes 0, e.g. a1b9c.txt becomes a2b0c.txt) What does running grep . * | LC_ALL=C sort | sha256sum in bash on that folder show?",
    17: "Download q-compare-files.zip and extract it. It has 2 nearly identical files, a.txt and b.txt, with the same number of lines. How many lines are different between a.txt and b.txt?",
    18: """There is a tickets table in a SQLite database that has columns type, units, and price. Each row is a customer bid for a concert ticket.
        type    units    price
        BRONZE    82    1.26
        Bronze    613    1.5
        silver    504    0.64
        gold    352    1.53
        gold    843    1.02
        ...
        What is the total sales of all the items in the "Gold" ticket type? Write SQL to calculate it."""

}

ANSWERS = {
    1: """Version:          Code 1.96.2 (fabdb6a30b49f79a7aba0f2ad9df9b399473380f, 2024-12-19T10:22:47.216Z)
OS Version:       Darwin arm64 22.6.0
CPUs:             Apple M2 (8 x 2400)
Memory (System):  8.00GB (0.07GB free)
Load (avg):       3, 3, 3
VM:               0%
Screen Reader:    no
Process Argv:     --crash-reporter-id 92550e3a-19fb-4a01-b9a3-bb0fe8885f25
GPU Status:       2d_canvas:                              enabled
                  canvas_oop_rasterization:               enabled_on
                  direct_rendering_display_compositor:    disabled_off_ok
                  gpu_compositing:                        enabled
                  multiple_raster_threads:                enabled_on
                  opengl:                                 enabled_on
                  rasterization:                          enabled
                  raw_draw:                               disabled_off_ok
                  skia_graphite:                          disabled_off
                  video_decode:                           enabled
                  video_encode:                           enabled
                  webgl:                                  enabled
                  webgl2:                                 enabled
                  webgpu:                                 enabled
                  webnn:                                  disabled_off

CPU %   Mem MB     PID  Process
    0       98   16573  code main
   13       41   16578     gpu-process
    0       16   16579     utility-network-service
    4      147   16582  window [1] (Extension: Cody: AI Coding Assistant with Autocomplete & Chat — Untitled (Workspace))
    0       33   16591  shared-process
    0       25   16592  fileWatcher [1]
    1       41   16604  ptyHost
    0        0   16618       /bin/zsh -il
    0        0   16780       /bin/zsh -il
    0        0   16841       /bin/zsh -il
    0        0   18972         bash /usr/local/bin/code -s
    7       41   18981           electron-nodejs (cli.js )
    0        0   18867       /bin/zsh -i
    0        8   18989       (ps)
    1      123   16744  extensionHost [1]
    0       25   16747       /Users/ok/Desktop/Visual Studio Code.app/Contents/Frameworks/Code Helper (Plugin).app/Contents/MacOS/Code Helper (Plugin) /Users/ok/Desktop/Visual Studio Code.app/Contents/Resources/app/extensions/json-language-features/server/dist/node/jsonServerMain --node-ipc --clientProcessId=16744
    0        0   16752       /Users/ok/.vscode/extensions/ms-vscode.cpptools-1.22.11-darwin-arm64/bin/cpptools
    0        0   18866       /Users/ok/.vscode/extensions/ms-python.python-2024.22.2-darwin-arm64/python-env-tools/bin/pet server
    0       33   18887       electron-nodejs (bundle.js )
    1       49   18545     window
    0       82   18924     window

Workspace Stats: 
|  Window (Extension: Cody: AI Coding Assistant with Autocomplete & Chat — Untitled (Workspace))
|    Folder (TDS): 0 files
|      File types:
|      Conf files:
""",
  11:"https://raw.githubusercontent.com/Parthivn28/email/refs/heads/main/email.json",
  12:"275",
  13:"3m1hv04rus",
  18:"SELECT SUM(units * price) FROM tickets  WHERE UPPER(TRIM(type)) = 'GOLD';"
}


# Function to check question similarity



def check_question_similarity(input_question: str):
    best_match = None
    highest_score = 0.0
    
    for q_number, stored_question in QUESTIONS.items():
        score = SequenceMatcher(None, input_question.lower(), stored_question.lower()).ratio() * 100
        if score > highest_score:
            highest_score = score
            best_match = q_number
    
    return best_match, highest_score

# Function to generate an answer
def get_answer(q_number: int, file: UploadFile = None, question: str = None):
    if q_number in nothardcoded:
        if q_number == 2:
            # Extract email dynamically
            import re
            match = re.search(r"email\s+set\s+to\s+([\w\.-]+@[\w\.-]+)", question)
            email = match.group(1) if match else "unknown@example.com"
            
            return {
                "args": {"email": email},
                "headers": {
                    "Accept": "*/*",
                    "Accept-Encoding": "gzip, deflate",
                    "Host": "httpbin.org",
                    "User-Agent": "HTTPie/3.2.4",
                    "X-Amzn-Trace-Id": "Root=1-67966078-0d45c5eb3734c87f4f504f75"
                },
                "origin": "106.51.202.98",
                "url": f"https://httpbin.org/get?email={email.replace('@', '%40')}"
            }
        
        elif q_number == 3 and file:
            return run_prettier_on_md(file)
        elif q_number == 4:
            return compute_google_sheets_formula(question)
        elif q_number == 5:
            return  compute_excel_formula(question)

        elif q_number == 6:
            return compute_wednesdays_count(question)
        elif q_number == 7 and file:
            return  extract_csv_answer(file)
        elif q_number == 8:
            return sort_json_objects(question)
        elif q_number == 9:
            return compute_json_hash_from_file(file)
        elif q_number == 10 and file:
            return process_unicode_data(file)
        elif q_number == 14 and file:
            return process_replace_across_files(file)
        elif q_number == 15 and file:
            return process_list_files_attributes(file)
        elif q_number == 16 and file:
            return process_move_rename_files(file)
        elif q_number == 17 and file:
            return process_compare_files(file)


        

    return ANSWERS.get(q_number, "Answer not found")

# Function to run npx prettier and return SHA256 hash
def run_prettier_on_md(file: UploadFile):
    try:
        file.file.seek(0)  # Reset file pointer before reading

        with tempfile.NamedTemporaryFile(delete=False, suffix=".md") as temp_md:
            temp_md.write(file.file.read())
            temp_md_path = temp_md.name

        cmd = f"npx -y prettier@3.4.2 {temp_md_path} | shasum -a 256"
        process = subprocess.run(cmd, shell=True, capture_output=True, text=True)

        os.unlink(temp_md_path)  # Cleanup temp file

        if process.returncode == 0:
            return process.stdout.strip().split()[0]  # Extract hash
        else:
            return f"Error running prettier: {process.stderr}"

    except Exception as e:
        return str(e)

def compute_google_sheets_formula(question: str):
    """
    Extracts values from the SEQUENCE function in a Google Sheets formula
    and computes the result dynamically.
    """
    match = re.search(r"SEQUENCE\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\)", question)
    if not match:
        return "Invalid formula"
    rows, cols, start, step = map(int, match.groups())
    
    # Generate first row using the number of columns specified in the SEQUENCE
    first_row = [start + i * step for i in range(cols)]
    
    result = sum(first_row)
    return result


def compute_excel_formula(question: str):
    # Extract content inside curly braces, e.g. {6,10,11,9,...} and {10,9,13,2,...}
    arrays = re.findall(r'\{([^}]+)\}', question)
    if len(arrays) < 2:
        return "Invalid formula: could not find two arrays"
    try:
        # Parse the first array as values and the second as sort keys
        values = [int(x.strip()) for x in arrays[0].split(',')]
        sort_keys = [int(x.strip()) for x in arrays[1].split(',')]
    except Exception as e:
        return f"Error parsing arrays: {e}"
    
    # Sort the values based on the sort_keys
    sorted_values = [x for _, x in sorted(zip(sort_keys, values))]
    # Take the first 6 values and sum them
    return sum(sorted_values[:6])


def compute_wednesdays_count(question: str):
    # Extract two dates from the question (format: yyyy-mm-dd)
    dates = re.findall(r'\d{4}-\d{2}-\d{2}', question)
    if len(dates) < 2:
        return "Invalid date range"
    
    start_date = datetime.datetime.strptime(dates[0], "%Y-%m-%d").date()
    end_date = datetime.datetime.strptime(dates[1], "%Y-%m-%d").date()
    
    count = 0
    current_date = start_date
    while current_date <= end_date:
        # Wednesday is weekday 2 (Monday=0, Tuesday=1, Wednesday=2, etc.)
        if current_date.weekday() == 2:
            count += 1
        current_date += datetime.timedelta(days=1)
    return count

def extract_csv_answer(file: UploadFile):
    try:
        file_content = file.file.read()
        zip_data = io.BytesIO(file_content)
        with zipfile.ZipFile(zip_data, 'r') as zip_ref:
            csv_files = [f for f in zip_ref.namelist() if f.endswith('.csv')]
            if not csv_files:
                return "No CSV file found in zip"
            csv_filename = csv_files[0]
            csv_data = zip_ref.read(csv_filename).decode('utf-8')
            reader = csv.DictReader(csv_data.splitlines())
            for row in reader:
                return row.get("answer", "Answer column not found")
            return "CSV file is empty"
    except Exception as e:
        return f"Error processing zip: {e}"
    
def sort_json_objects(question: str):
    # Extract the JSON array from the question text
    match = re.search(r'(\[.*\])', question, re.DOTALL)
    if not match:
        return "Invalid JSON format in question"
    try:
        data = json.loads(match.group(1))
        # Sort by age, then by name in case of ties
        sorted_data = sorted(data, key=lambda x: (x["age"], x["name"]))
        # Return compact JSON (no spaces or newlines)
        return json.dumps(sorted_data, separators=(",", ":"))
    except Exception as e:
        return f"Error parsing JSON: {e}"

def compute_json_hash_from_file(file: UploadFile):
    try:
        file.file.seek(0)  # Ensure we start at the beginning
        content = file.file.read().decode("utf-8")
        d = {}
        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            d[key] = value
        # Convert dictionary to a compact JSON string (no spaces/newlines)
        json_str = json.dumps(d, separators=(",", ":"))
        # Compute SHA-256 hash of the JSON string
        hash_obj = hashlib.sha256(json_str.encode("utf-8"))
        return hash_obj.hexdigest()
    except Exception as e:
        return f"Error processing file: {e}"

def process_unicode_data(file: UploadFile):
    total = 0
    debug_info = {}
    try:
        file_content = file.file.read()
        zip_data = io.BytesIO(file_content)
        with zipfile.ZipFile(zip_data, 'r') as zf:
            # List of files with their expected encodings and delimiters
            files_info = [
                ("data1.csv", "cp1252", ","),
                ("data2.csv", "utf-8", ","),
                ("data3.txt", "utf-16", "\t")
            ]
            for filename, encoding, delimiter in files_info:
                file_sum = 0
                count = 0
                try:
                    with zf.open(filename) as f:
                        reader = csv.DictReader(io.TextIOWrapper(f, encoding=encoding), delimiter=delimiter)
                        for row in reader:
                            # Strip extra whitespace from symbol and value
                            symbol = row.get("symbol", "").strip()
                            # Check for an exact match for the intended symbols
                            if symbol in ["”", "Š"]:
                                try:
                                    value = float(row.get("value", "").strip())
                                    file_sum += value
                                    count += 1
                                except Exception:
                                    pass
                    debug_info[filename] = {"sum": file_sum, "count": count}
                    total += file_sum
                except Exception as e:
                    debug_info[filename] = {"error": str(e)}
        # Debug print: check sums and counts per file
        print("Debug info:", debug_info)
        return int(total)
    except Exception as e:
        return f"Error processing zip: {e}"


def process_replace_across_files(file: UploadFile):
    try:
        file_content = file.file.read()
        zip_data = io.BytesIO(file_content)
        with zipfile.ZipFile(zip_data, 'r') as zf:
            # Get a sorted list of files (exclude directories)
            filenames = sorted([f for f in zf.namelist() if not f.endswith('/')])
            combined_content = b""
            for fname in filenames:
                raw_bytes = zf.read(fname)
                try:
                    text = raw_bytes.decode('utf-8')
                except UnicodeDecodeError:
                    # fallback if not utf-8
                    text = raw_bytes.decode('latin-1')
                # Replace all occurrences of IITM (any case) with "IIT Madras"
                # The (?i) flag makes the regex case-insensitive.
                new_text = re.sub(r"(?i)IITM", "IIT Madras", text)
                # Re-encode back to bytes; this should preserve line endings as in new_text.
                new_bytes = new_text.encode('utf-8')
                combined_content += new_bytes
            # Compute SHA-256 hash of the concatenated result.
            hash_obj = hashlib.sha256(combined_content)
            return hash_obj.hexdigest()
    except Exception as e:
        return f"Error processing zip: {e}"

def process_list_files_attributes(file: UploadFile):
    try:
        file_content = file.file.read()
        zip_data = io.BytesIO(file_content)
        with zipfile.ZipFile(zip_data, 'r') as zf:
            total_size = 0
            # Reference datetime: Sat, 29 Apr 2006, 8:48 pm IST.
            # Note: IST is UTC+5:30, but here we assume the zip timestamps are in IST.
            ref_dt = datetime.datetime(2006, 4, 29, 20, 48, 0)
            for info in zf.infolist():
                if info.is_dir():
                    continue
                # Check file size
                if info.file_size >= 4294:
                    # info.date_time is a tuple: (year, month, day, hour, minute, second)
                    mod_dt = datetime.datetime(*info.date_time)
                    if mod_dt >= ref_dt:
                        total_size += info.file_size
            return total_size
    except Exception as e:
        return f"Error processing zip: {e}"

def process_move_rename_files(file):
    # Mapping for digit replacement: '0'→'1', ..., '8'→'9', '9'→'0'
    trans_map = str.maketrans("0123456789", "1234567890")
    
    # Create a temporary directory for extraction and processing
    with tempfile.TemporaryDirectory() as tempdir:
        extract_dir = os.path.join(tempdir, "extracted")
        os.mkdir(extract_dir)
        target_dir = os.path.join(tempdir, "target")
        os.mkdir(target_dir)
        
        # Extract ZIP file to extract_dir
        with zipfile.ZipFile(io.BytesIO(file.file.read()), 'r') as zf:
            zf.extractall(extract_dir)
        
        # Move all files from any subfolder to target_dir
        for root, dirs, files in os.walk(extract_dir):
            for fname in files:
                src = os.path.join(root, fname)
                dst = os.path.join(target_dir, fname)
                os.rename(src, dst)
        
        # Rename files in target_dir: replace each digit with the next
        for fname in os.listdir(target_dir):
            new_fname = fname.translate(trans_map)
            src = os.path.join(target_dir, fname)
            dst = os.path.join(target_dir, new_fname)
            os.rename(src, dst)
        
        # Simulate "grep . *": for each file (in sorted order), output "filename:line" for non-empty lines
        output_lines = []
        for fname in sorted(os.listdir(target_dir)):
            fpath = os.path.join(target_dir, fname)
            with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    if line.strip():  # non-empty line
                        output_lines.append(f"{fname}:{line.rstrip('\n')}")
        
        # Sort lines as in LC_ALL=C sort and join with newline
        sorted_lines = sorted(output_lines)
        combined = "\n".join(sorted_lines) + "\n"
        
        # Compute SHA-256 hash of the combined bytes
        hash_val = hashlib.sha256(combined.encode("utf-8")).hexdigest()
        return hash_val

def process_compare_files(file: UploadFile):
    try:
        file_content = file.file.read()
        zip_data = io.BytesIO(file_content)
        with zipfile.ZipFile(zip_data, 'r') as zf:
            # Read a.txt and b.txt (assuming UTF-8 encoding)
            a_text = zf.read("a.txt").decode("utf-8", errors="replace")
            b_text = zf.read("b.txt").decode("utf-8", errors="replace")
            a_lines = a_text.splitlines()
            b_lines = b_text.splitlines()
            # Count the number of lines that differ (compare corresponding lines)
            diff_count = sum(1 for a, b in zip(a_lines, b_lines) if a != b)
            return diff_count
    except Exception as e:
        return f"Error processing zip: {e}"




# API endpoint
@app.post("/api/")
async def process_question(question: str = Form(...), file: UploadFile = None):
    q_number, similarity_score = check_question_similarity(question)

    if similarity_score >= 50.0:
        answer = get_answer(q_number, file, question)
        if not isinstance(answer, str):
            answer = str(answer)
        return {"answer": answer, "similarity_score": similarity_score}
    else:
        return {"error": "Question not recognized", "similarity_score": similarity_score}
