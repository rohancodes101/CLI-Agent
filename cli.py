API_KEY = "Put-API-Key-Here"
URL = "https://openrouter.ai/api/v1/chat/completions"
import requests
import subprocess
import json
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

console = Console()
MODEL = "meta-llama/llama-3.3-70b-instruct"

# ----------------------------
# Run shell command
# ----------------------------
def run_command(cmd):
    try:
        output = subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.STDOUT)
        return output
    except subprocess.CalledProcessError as e:
        return e.output


# ----------------------------
# AI Agent
# ----------------------------
def agent(user_input):
    system_prompt = """
You are an AI DevOps agent.

Rules:
- If user wants to run a command, respond ONLY in JSON:
  {"action": "run", "command": "ls -l"}
- Otherwise respond normally.
- Be concise and helpful.
"""

    response = requests.post(
        URL,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ]
        }
    )

    data = response.json()

    if "choices" not in data:
        return f"[red]API ERROR:[/red] {data}"

    content = data["choices"][0]["message"]["content"]

    # Try tool execution
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
# Main CLI loop
# ----------------------------
def main():
    console.print(Panel("[bold cyan]AI DevOps CLI Agent[/bold cyan]\nType 'exit' to quit", title="🚀 Ready"))

    while True:
        try:
            user_input = Prompt.ask("[bold blue]>>[/bold blue]")

            if user_input.lower() in ["exit", "quit"]:
                console.print("[red]Exiting...[/red]")
                break

            response = agent(user_input)

            console.print(Panel(response, title="🤖 Response", border_style="green"))

        except KeyboardInterrupt:
            console.print("\n[red]Interrupted[/red]")
            break


if __name__ == "__main__":
    main()
