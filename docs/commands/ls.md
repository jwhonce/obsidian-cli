# ls

List all markdown files in the vault, respecting the blacklist.

## Synopsis

```bash
obsidian-cli --vault /path/to/vault ls
obsidian-cli --vault /path/to/vault --blacklist "Templates/:Archive/" ls
```

## Description

The `ls` command prints the relative path of each `*.md` file found under the configured vault
directory. Paths are printed one per line. Files in blacklisted directories are skipped.

## Blacklist

You can control which directories are excluded via a blacklist of path prefixes. Matching is
prefix-based and case-sensitive.

- Defaults: `Assets/`, `.obsidian/`, `.git/`
- Configure via any of:
  - CLI: `--blacklist "Assets/:.obsidian/:.git/"`
  - Environment: `OBSIDIAN_BLACKLIST="Assets/:.obsidian/:.git/"`
  - Config file (obsidian-cli.toml):

    ```toml
    blacklist = ["Assets/", ".obsidian/", ".git/"]
    ```

Examples of matches:

- `Assets/image.png` -> excluded (matches `Assets/`)
- `.obsidian/config.json` -> excluded (matches `.obsidian/`)
- `Notes/topic.md` -> included (no match)

## Examples

- List all markdown files

  ```bash
  obsidian-cli --vault ~/Vault ls
  ```

- List while excluding additional directories

  ```bash
  obsidian-cli --vault ~/Vault --blacklist "Templates/:Archive/" ls
  ```

## Exit codes

- 0: Success
- Non-zero: Errors such as missing `--vault` or inaccessible vault
