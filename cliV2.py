#THis uses the jaccard similalriyt
import requests
import subprocess
import json
import os
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

console = Console()

# ----------------------------
# CONFIG
# ----------------------------
API_KEY = "sk-or-v1-sdfasdf6"
URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "meta-llama/llama-3.3-70b-instruct"

MEMORY_FILE = "memory.json"


# ----------------------------
# MEMORY LOAD/SAVE
# ----------------------------
def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return []
    try:
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    except:
        return []


def save_memory(memory):
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2)


# ----------------------------
# SIMPLE KEYWORD SIMILARITY
# ----------------------------
def simple_similarity(a, b):
    a_words = set(a.lower().split())
    b_words = set(b.lower().split())

    common = a_words.intersection(b_words)

    if not common:
        return 0

    return len(common) / len(a_words.union(b_words))


# ----------------------------
# RETRIEVE RELEVANT MEMORY
# ----------------------------
def retrieve_relevant(memory, query, top_k=3):
    scored = []

    for item in memory:
        content = item.get("content", "")
        score = simple_similarity(query, content)
        scored.append((score, content))

    scored.sort(reverse=True)

    return [text for score, text in scored[:top_k] if score > 0]


# ----------------------------
# COMMAND EXECUTION
# ----------------------------
def run_command(cmd):
    try:
        output = subprocess.check_output(
            cmd, shell=True, text=True, stderr=subprocess.STDOUT
        )
        return output
    except subprocess.CalledProcessError as e:
        return e.output


# ----------------------------
# AGENT
# ----------------------------
def agent(user_input):
    memory = load_memory()

    relevant = retrieve_relevant(memory, user_input)

    system_prompt = """
You are an AI DevOps agent.

Rules:
- If user wants to run a command, respond ONLY in JSON:
  {"action": "run", "command": "ls -l"}
- Otherwise respond normally.
- Be concise and helpful.
"""

    messages = [{"role": "system", "content": system_prompt}]

    # Inject relevant memory
    for r in relevant:
        messages.append({"role": "system", "content": f"Relevant past: {r}"})

    messages.append({"role": "user", "content": user_input})

    response = requests.post(
        URL,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": MODEL,
            "messages": messages
        }
    )

    data = response.json()

    if "choices" not in data:
        return f"[red]API ERROR:[/red] {data}"

    content = data["choices"][0]["message"]["content"]

    # Save memory
    memory.append({"role": "user", "content": user_input})
    memory.append({"role": "assistant", "content": content})

    # Limit memory size
    memory = memory[-50:]

    save_memory(memory)

    # TOOL EXECUTION
    try:
        parsed = json.loads(content)
        if parsed.get("action") == "run":
            cmd = parsed.get("command")
            console.print(f"[yellow]⚡ Running:[/yellow] {cmd}")
            result = run_command(cmd)
            return f"[green]{result}[/green]"
    except:
        pass

    return content


# ----------------------------
# MAIN LOOP
# ----------------------------
def main():
    console.print(
        Panel(
            "[bold cyan]AI DevOps CLI Agent (Memory v2.1 - Lightweight)[/bold cyan]\n"
            "✔ No embeddings API\n✔ No numpy\n✔ Fast + stable",
            title="Ready 🚀",
        )
    )

    while True:
        try:
            user_input = Prompt.ask("[bold blue]>>[/bold blue]")

            if user_input.lower() in ["exit", "quit"]:
                break

            if user_input.lower() == "clear":
                save_memory([])
                console.print("[yellow]Memory cleared[/yellow]")
                continue

            response = agent(user_input)

            console.print(
                Panel(response, title="🤖 Response", border_style="green")
            )

        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    main()
