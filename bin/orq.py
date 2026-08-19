#!/usr/bin/env python3

# for compatibility reasons
from __future__ import annotations

import argparse
import difflib
import json
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_MODEL = "nvidia/nemotron-3-ultra-550b-a55b:free"
API_URL = "https://openrouter.ai/api/v1/chat/completions"
SCRIPT_DIR = Path(__file__).resolve().parent


def get_api_key() -> str:
    try:
        result = subprocess.run(
            ["secret-tool", "lookup", "service", "openrouter", "account", "default"],
            capture_output=True,
            text=True,
            check=True,
        )
    except FileNotFoundError:
        sys.exit("Error: secret-tool not found. Please install libsecret-tools.")
    except subprocess.CalledProcessError:
        sys.exit("Error: No OpenRouter API key found in secret-tool.")

    key = result.stdout.strip()
    if not key:
        sys.exit("Error: secret-tool returned an empty key.")
    return key


def find_agents_md(start: Path) -> str | None:
    # walk up from start directory looking for an AGENTS.md
    for directory in [start, *start.parents]:
        candidate = directory / "AGENTS.md"
        if candidate.is_file():
            return candidate.read_text(encoding="utf-8").strip()
    return None


def resolve_prompt_file(name: str) -> Path | None:
    search_dirs = [Path.cwd() / "prompts", SCRIPT_DIR.parent / "prompts"]
    for directory in search_dirs:
        for ext in (".md", ".txt"):
            candidate = directory / f"{name}{ext}"
            if candidate.is_file():
                return candidate
    return None


def list_prompts() -> None:
    seen: set[str] = set()
    for directory in (Path.cwd() / "prompts", SCRIPT_DIR.parent / "prompts"):
        if not directory.is_dir():
            continue
        for f in sorted(directory.glob("*")):
            if f.suffix in (".md", ".txt") and f.stem not in seen:
                seen.add(f.stem)
                print(f"{f.stem}\t({f})")
    if not seen:
        print("No prompts found.")


def build_system_prompt(prompt_name: str | None) -> str:
    parts: list[str] = []

    agents_context = find_agents_md(Path.cwd())
    if agents_context:
        parts.append(agents_context)

    if prompt_name:
        prompt_path = resolve_prompt_file(prompt_name)
        if prompt_path is None:
            sys.exit(f"Error: No prompt file found for '{prompt_name}'.")
        parts.append(prompt_path.read_text(encoding="utf-8").strip())

    return "\n\n---\n\n".join(parts)


def gather_input(files: list[str]) -> str:
    if files:
        # Positional arguments are treated as files if they exist on disk, otherwise treat the whole thing as raw text typed directly on the command line.
        if all(Path(f).is_file() for f in files):
            texts = [Path(f).read_text(encoding="utf-8") for f in files]
            return "\n\n".join(texts)
        return " ".join(files)
    if not sys.stdin.isatty():
        return sys.stdin.read()
    sys.exit("Error: No input given.")


def call_openrouter(api_key: str, model: str, system_prompt: str, user_input: str) -> str:
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input},
        ],
    }
    request = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        sys.exit(f"Error: OpenRouter returned error {e.code}:\n\n{body}")
    except urllib.error.URLError as e:
        sys.exit(f"Error: OpenRouter could not be reached ({e.reason}).")

    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        sys.exit(f"Error: OpenRouter returned an unexpected response shape:\n\n{json.dumps(data, indent=2)}")


def show_diff(original: str, revised: str, label: str) -> None:
    diff = difflib.unified_diff(
        original.splitlines(keepends=True),
        revised.splitlines(keepends=True),
        fromfile=f"{label} (original)",
        tofile=f"{label} (revised)",
    )
    sys.stdout.writelines(diff)


def main() -> None:
    parser = argparse.ArgumentParser(prog="orq", description="orq is a small CLI wrapper for interacting with OpenRouter AI models. orq will automatically look for AGENTS.md in your current working directory (or any of its parent directories) and prepend its content is to the system prompt.")
    parser.add_argument("-p", "--prompt", help="name of prompt file [without extension] [optional]")
    parser.add_argument("-m", "--model", default=DEFAULT_MODEL, help="OpenRouter model ID [default: " + DEFAULT_MODEL + "] [optional]")
    parser.add_argument("--diff", action="store_true", help="write result to [filename].new[.ext] and print a diff instead of raw output")
    parser.add_argument("--list", action="store_true", help="only list available prompts")
    parser.add_argument("files", nargs="*", help="input files(s) [reads from stdin if omitted]")
    args = parser.parse_args()

    if args.list:
        list_prompts()
        return

    api_key = get_api_key()
    system_prompt = build_system_prompt(args.prompt)
    user_input = gather_input(args.files)

    result = call_openrouter(api_key, args.model, system_prompt, user_input)

    if args.diff:
        if len(args.files) != 1:
            sys.exit("Error: --diff requires exactly one input file.")
        src = Path(args.files[0])
        out_path = src.with_suffix(f".new{src.suffix}")
        out_path.write_text(result, encoding="utf-8")
        show_diff(user_input, result, str(src))
        print(f"\nwrote: {out_path}", file=sys.stderr)
    else:
        print(result)


if __name__ == "__main__":
    main()
