import os
import json
import sqlite3
import subprocess
from datetime import datetime
from dateutil.parser import parse
from pathlib import Path
from scipy.spatial.distance import cosine
import requests
import base64
from dotenv import load_dotenv

load_dotenv()

AIPROXY_TOKEN = os.getenv("AIPROXY_TOKEN")

# Set base directory
BASE_DIR = Path(__file__).resolve().parent / "data"


def A1(email="23ds2000055@ds.study.iitm.ac.in"):
    try:
        process = subprocess.Popen(
            [
                "uv",
                "run",
                "https://raw.githubusercontent.com/sanand0/tools-in-data-science-public/tds-2025-01/project-1/datagen.py",
                email,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            print(f"Error: {stderr}")
            return None
        return stdout
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        return None


def A2(prettier_version="prettier@3.4.2", filename=BASE_DIR / "format.md"):
    command = [r"C:\Program Files\nodejs\npx.cmd", prettier_version, "--write", str(filename)]
    try:
        subprocess.run(command, check=True)
        print("Prettier executed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}")


def A3(filename=BASE_DIR / "dates.txt", targetfile=BASE_DIR / "dates-wednesdays.txt", weekday=2):
    if not filename.exists():
        print(f"Error: Input file {filename} does not exist.")
        return

    try:
        with filename.open("r") as file:
            dates = file.readlines()

        weekday_count = sum(1 for date in dates if parse(date.strip()).weekday() == weekday)

        with targetfile.open("w") as file:
            file.write(str(weekday_count))

        print(f"Found {weekday_count} Wednesdays. Saved to {targetfile}")

    except Exception as e:
        print(f"Error processing the file: {e}")


def A4(filename=BASE_DIR / "contacts.json", targetfile=BASE_DIR / "contacts-sorted.json"):
    with filename.open("r") as file:
        contacts = json.load(file)

    sorted_contacts = sorted(contacts, key=lambda x: (x["last_name"], x["first_name"]))

    with targetfile.open("w") as file:
        json.dump(sorted_contacts, file, indent=4)


def A5(log_dir_path=BASE_DIR / "logs", output_file_path=BASE_DIR / "logs-recent.txt", num_files=10):
    log_dir = Path(log_dir_path)

    log_files = sorted(log_dir.glob("*.log"), key=os.path.getmtime, reverse=True)[:num_files]

    with output_file_path.open("w") as f_out:
        for log_file in log_files:
            with log_file.open("r") as f_in:
                f_out.write(f_in.readline().strip() + "\n")


def A6(doc_dir_path=BASE_DIR / "docs", output_file_path=BASE_DIR / "docs/index.json"):
    index_data = {}

    for root, _, files in os.walk(doc_dir_path):
        for file in files:
            if file.endswith(".md"):
                file_path = Path(root) / file
                with file_path.open("r", encoding="utf-8") as f:
                    for line in f:
                        if line.startswith("# "):
                            title = line[2:].strip()
                            relative_path = file_path.relative_to(doc_dir_path).as_posix()
                            index_data[relative_path] = title
                            break

    with output_file_path.open("w", encoding="utf-8") as f:
        json.dump(index_data, f, indent=4)


def A7(filename=BASE_DIR / "email.txt", output_file=BASE_DIR / "email-sender.txt"):
    with filename.open("r") as file:
        email_content = file.readlines()

    sender_email = "unknown@example.com"
    for line in email_content:
        if line.startswith("From"):
            sender_email = line.strip().split(" ")[-1].replace("<", "").replace(">", "")
            break

    with output_file.open("w") as file:
        file.write(sender_email)


def png_to_base64(image_path):
    with image_path.open("rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def A8(filename=BASE_DIR / "credit_card.txt", image_path=BASE_DIR / "credit_card.png"):
    body = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Extract only the credit card number from this image:"},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{png_to_base64(image_path)}"}},
                ],
            }
        ],
    }

    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {AIPROXY_TOKEN}"}

    response = requests.post(
        "http://aiproxy.sanand.workers.dev/openai/v1/chat/completions", headers=headers, data=json.dumps(body)
    )

    if response.status_code != 200:
        print("Error in API request:", response.text)
        return

    result = response.json()
    card_number = result["choices"][0]["message"]["content"].replace(" ", "")

    with filename.open("w") as file:
        file.write(card_number)


def get_embedding(text):
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {AIPROXY_TOKEN}"}
    data = {"model": "text-embedding-3-small", "input": [text]}

    response = requests.post("http://aiproxy.sanand.workers.dev/openai/v1/embeddings", headers=headers, data=json.dumps(data))
    response.raise_for_status()
    return response.json()["data"][0]["embedding"]


def A9(filename=BASE_DIR / "comments.txt", output_filename=BASE_DIR / "comments-similar.txt"):
    with filename.open("r") as f:
        comments = [line.strip() for line in f.readlines()]

    embeddings = [get_embedding(comment) for comment in comments]

    min_distance = float("inf")
    most_similar = (None, None)

    for i in range(len(comments)):
        for j in range(i + 1, len(comments)):
            distance = cosine(embeddings[i], embeddings[j])
            if distance < min_distance:
                min_distance = distance
                most_similar = (comments[i], comments[j])

    with output_filename.open("w") as f:
        f.write(most_similar[0] + "\n" + most_similar[1] + "\n")


def A10(
    filename=BASE_DIR / "ticket-sales.db",
    output_filename=BASE_DIR / "ticket-sales-gold.txt",
    query="SELECT SUM(units * price) FROM tickets WHERE type = 'Gold'",
):
    conn = sqlite3.connect(filename)
    cursor = conn.cursor()

    cursor.execute(query)
    total_sales = cursor.fetchone()[0] or 0

    with output_filename.open("w") as file:
        file.write(str(total_sales))

    conn.close()
