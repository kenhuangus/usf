
# Gandalf Password Fuzzer (with Local Ollama LLM)

This project is a fun challenge where you try to trick Gandalf (an AI agent) into revealing a secret password. Gandalf gets smarter with each level, and your goal is to extract the password in as few tries as possible.
The script uses a **local Ollama LLM** (such as `llama3`) for language processing, so no cloud API keys are needed.

---

## Features

- Uses [Ollama](https://ollama.com/) to run large language models locally.
- No need for OpenAI or other cloud APIs.
- Works on Windows, Linux, and macOS.

---

## Prerequisites

- **Python 3.11+** installed.
- **Ollama** installed and running on your machine or accessible via network.
- The desired Ollama model (e.g., `llama3`) pulled and available.

---

## Setup Instructions

### 1. Clone or Download the Repository

```
git clone this repo 
```

Or just download the script file.

---

### 2. Install Python Dependencies

**(Recommended) Create and activate a virtual environment:**

- **Windows:**

```sh
python -m venv venv
venv\Scripts\activate
```

- **Linux/macOS:**

```sh
python3 -m venv venv
source venv/bin/activate
```


**Install required packages:**

```sh
pip install requests langchain langchain-ollama
```


---

### 3. Install and Run Ollama

- Download and install Ollama from [https://ollama.com/download](https://ollama.com/download).
- Start the Ollama service:

```sh
ollama serve
```

- Pull the desired model (e.g., `llama3`):

```sh
ollama pull llama3
```


---

### 4. Configure the Ollama Server Address

- By default, the script uses `localhost:11434`.
- To use a remote Ollama server, edit this line in the script:

```python
OLLAMA_BASE_URL = "http://YOUR_OLLAMA_IP:11434"
```

Replace `YOUR_OLLAMA_IP` with your actual server IP or hostname.

---

### 5. Run the Script

**Windows:**

```sh
python your_script.py
```

**Linux/macOS:**

```sh
python3 your_script.py
```


---

## How It Works

- The script communicates with the Gandalf challenge API.
- It uses your local Ollama LLM to generate prompts and detect passwords.
- You have 30 attempts to extract the password for the current level.

---

## Troubleshooting

- **Ollama not found:** Make sure Ollama is installed and running (`ollama serve`).
- **Model not found:** Make sure you have pulled the model you specify in the script.
- **Network issues:** If connecting to a remote Ollama server, ensure firewalls allow access to port 11434.

---

## Customization

- Change the Ollama model by editing the `model` parameter in the script:

```python
ChatOllama(model="llama3", base_url=OLLAMA_BASE_URL)
```

- Adjust the challenge level by changing the `LEVEL` variable.

---

## License

MIT License

---

## Credits

- [Lakera Gandalf Challenge](https://gandalf.lakera.ai/)
- [Ollama](https://ollama.com/)
- [LangChain](https://python.langchain.com/)
- Core logic adapted from [corca-ai/LLMFuzzAgent](https://github.com/corca-ai/LLMFuzzAgent/blob/main/solve.py)


