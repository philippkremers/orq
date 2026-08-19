# orq

orq stands for **O**pen **R**outer **Q**uery and is a small CLI wrapper for using OpenRouter AI models with reusable system prompts and automatic context retrieval. I wrote orq specifically for academic writing tasks.

## Installation

```bash
git clone https://github.com/philippkremers/orq.git
cd orq
chmod +x bin/orq.py
ln -s "$(pwd)/bin/orq.py" ~/.local/bin/orq
```

For security reasons, orq requires the external library `secret-tool` to store your OpenRouter API key securely in the system keyring. This ensures that your API key never gets written to disk in plaintext. How you install `secret-tool` will depends on your operating system.

**Arch**

```bash
sudo pacman -S libsecret
```

**Ubuntu and Debian**

```bash
sudo apt install libsecret-tools
```

Once `secret-tool` is installed, you can store your OpenRouter API key with the following command:

```bash
secret-tool store --label="OpenRouter API Key" service openrouter account default
```

## Usage

| Flag | Description |
|---|---|
| `-p`, `--prompt` | The name of a prompt file (must have either `.txt` or `.md` extension). |
| `-m`, `--model` | OpenRouter model id (default: `nvidia/nemotron-3-ultra-550b-a55b:free`) |
| `--diff` | Write result to `<file>.new<ext>` and print a unified diff instead of raw output. |
| `--list` | List available prompts and exit. |


## Examples

List all available prompts (project-specific and global):
```bash
orq --list
```

You can pass text directly as an argument to orq:

```bash
orq -p polish-academic-en 'One trouble with our institutions is ….'
```

You can also pass an entire file to orq: 

```bash
orq -p polish-academic-en draft.md
```

From a file, with output written to draft.new.md and a diff printed

```bash
orq -p polish-en --diff draft.md
```

You can connect orq via pipe with other commands via stdin: 

```bash
cat notes.md | orq -p critique
```

You can concat multiple files concatenated as input to orq as well:

```bash
orq -p critique ch1.md ch2.md
```

You can also chose a custom AI model for OpenRouter:

```bash
orq -p academic -m anthropic/claude-3.5-sonnet 'One trouble with our institutions is ….'
```

Technically, you can rawdog orq as well by using it without parameters. In that case, the input is forwarded to the AI model without any specific context:

```bash
orq 'What ingredients do I need for banana bread?'
```

## Loading Prompt Files

orq loads prompts from a `prompts/` directory as `.md` or `.txt` files. For example, `prompts/academic.md` is invoked as `-p academic`.

Resolution order (first match wins):

1. `./prompts/[name].md`
2. `./prompts/[name].txt`
3. `[orq’s own directory]/../prompts/[name].md`
4. `[orq’s own directory]/../prompts/[name].txt`

This means a project-local `prompts/` folder overrides your global one,
so you can have a shared set of general-purpose prompts plus
project-specific overrides that take priority when you're `cd`'d into
that project.

## Auto-Loading Context

If orq finds a file named `AGENTS.md` in your current working directory (or any of its parent directories), its content is automatically prepended to the system prompt on every orq call made from that directory or subdirectory. (So, orq looks for `AGENTS.md` file in a similar way as git looks for `.git`.)

So, you should use `AGENTS.md` for standing context for a project: register, terminology, citation rules, editing scope, anything you'd otherwise have to retype into every prompt. See the project for a sample `AGENTS.md` template.

