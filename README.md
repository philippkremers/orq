# orq

`orq` stands for OpenRouter Query and is a small CLI wrapper for using [OpenRouter AI models](https://openrouter.ai/) with reusable system prompts and automatic context retrieval. I wrote `orq` specifically trying to borrow some of the workflow conventions from software development (reusable configuration files, project-specific context loading, and version-control) and apply them to writing prose instead of code.

A quick example, running a paragraph through an academic polishing prompt:

```bash
orq -p academic-polishing "Here it becomes palpably evident which is the most certain path from natural science to mysticism. It is not the extravagant theorising of the philosophy of nature, but the shallowest empiricism that spurns all theory and distrusts all thought. It is not a priori necessity that proves the existence .of spirits, but the empirical observations of Messrs. Wallace, Crookes, and Co."
```

*Output:*
```
The most certain path from natural science to mysticism is not the extravagant theorising of the philosophy of nature, but the shallowest empiricism, which spurns all theory and distrusts all thought. It is not a priori necessity that proves the existence of spirits, but the empirical observations of Messrs. Wallace, Crookes, and Co.
```

`orq` can also be integrated into editors like KDE Kate and VS Code as a keyboard shortcut, so that a text selection can be sent through a chosen prompt and replaced in place without leaving the editor.


## Installation

```bash
git clone https://github.com/philippkremers/orq.git
cd orq
chmod +x bin/orq.py
ln -s "$(pwd)/bin/orq.py" ~/.local/bin/orq
```

You need a free [OpenRouter](https://openrouter.ai/) API key to run `orq`. For security reasons, `orq` requires the external library `secret-tool` to store your OpenRouter API key securely in the system keyring. This ensures that your API key never gets written to disk in plaintext. How you install `secret-tool` will depends on your operating system.

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
| `-m`, `--model` | OpenRouter model id (default: `nvidia/nemotron-3-ultra-550b-a55b:free`). |
| `--diff` | Write result to `[file].new[.ext]` and print a unified diff instead of raw output. |
| `--list` | List available prompts and exit. |


## Examples

List all available prompts (project-specific and global):
```bash
orq --list
```

You can pass text directly as an argument to `orq`:

```bash
orq --prompt academic-polishing "A system can generally be steered more accurately if it uses feedforward, based on prediction of the future, in combination with feedback, to correct the errors of the past. However, forming expectations to deal with uncertainty creates its own problems. Feedforward can have unfortunate destabilizing effects, for a system can overreact to its predictions and go into unstable oscillations. Feedforward in markets can become especially destabilizing when each actor tries to anticipate the actions of the others (and hence their expectations)."
```

You can also pass an entire file to `orq`: 

```bash
orq -p academic-polishing draft.md
```

From a file, with output written to draft.new.md and merely print the difference on stdout:

```bash
orq -p academic-polishing --diff draft.md
```

You can connect `orq` via pipe with other commands via stdin: 

```bash
cat notes.md | orq -p academic-polishing
```

You can concat multiple files concatenated as input to `orq` as well:

```bash
orq -p academic-polishing chapter1.md chapter2.md
```

You can also chose a custom AI model for OpenRouter:

```bash
orq -p academic-polishing -m poolside/laguna-s-2.1:free "A system can generally be steered more accurately if it uses feedforward, based on prediction of the future, in combination with feedback, to correct the errors of the past."
```

Some other free OpenRouter models include `google/gemma-4-26b-a4b-it:free`, `openai/gpt-oss-20b:free`, `cohere/north-mini-code:free`, and `poolside/laguna-s-2.1:free`.

Technically, you can rawdog `orq` as well by using it without parameters. In that case, the input is forwarded to the AI model without any specific context:

```bash
orq 'What ingredients do I need for banana bread?'
```

## Loading Prompt Files

orq loads prompts from a `prompts/` directory as `.md` or `.txt` files. For example, `prompts/academic.md` is invoked as `-p academic`.

Resolution order (first match wins):

1. `./prompts/[name].md`
2. `./prompts/[name].txt`
3. `[orq directory]/prompts/[name].md`
4. `[orq directory]/prompts/[name].txt`

This means a project-local `prompts/` folder overrides your global one.

## Auto-Loading Context

If `orq` finds a file named `AGENTS.md` in your current working directory (or any of its parent directories), its content is automatically prepended to the system prompt on every `orq` call made from that directory or subdirectory. (So, `orq` looks for `AGENTS.md` file in a similar way as git looks for `.git`.) So, you should use `AGENTS.md` for standing context for a given project (e.g., outline, terminology, citation rules, anything you would otherwise have to retype into every prompt).

## Editor Integration

### KDE Kate

Kate ships an External Tools plugin, no extra installation needed.

1. Open `Settings > Configure Kate > Plugins` and enable *External Tools*.
2. Open `Tools > External Tools > Configure > Add Tool` and fill in:

| Field | Value |
|---|---|
| Name | `orq` |
| Executable | `orq` |
| Working Directory | `%{Document:Path}` |
| Arguments | `--prompt academic-polishing "%{Document:Selection:Text}"` |
| Output | `Replace Selected Text` |

3. Open `Settings > Configure Shortcuts`, search for the tool by name (`orq`), and assign a key combination such as `Ctrl+Alt+A`.
4. Select text in the editor and press the shortcut. The selection is sent to `orq` and replaced in place with the model's output.

You can swap `academic-polishing` for any other prompt name to add more tools, e.g. one for `natural-writing` each bound to its own shortcut.

### VS Code

VS Code has no built-in way to pipe a selection through an external command, so this requires the `Edit with Shell` extension (`ryu1kn.edit-with-shell`).

1. Search for `Edit with Shell` in the Extensions marketplace and install it.
2. Select text, open the command palette (`Ctrl+Shift+P`) and run `Edit with Shell Command`. Enter:

```
orq --prompt academic-polishing
```

The selection is piped to `orq` via stdin and replaced with its output.

3. Register the command as one of the extension's quick commands, then add a keybinding in `keybindings.json`:

```json
{
  "key": "ctrl+alt+a",
  "command": "editWithShell.runQuickCommand1"
}
```

Set the corresponding quick command in your VS Code settings:

```json
"editWithShell.favoriteCommands": [
  { "id": "runQuickCommand1", "command": "orq --prompt academic-polishing" }
]
```

4. Select text and press the shortcut to run the bound command directly, skipping the command palette.
