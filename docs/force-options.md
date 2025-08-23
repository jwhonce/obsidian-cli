# Force Options and Data Safety

Several commands in obsidian-cli include a `--force` (or `-f`) option to override default safety behaviors. This document explains when and how to use these options.

## Commands with Force Options

### add-uid

```bash
obsidian-cli add-uid PAGE_OR_FILE --force
```

By default, the `add-uid` command will not modify files that already have a UID in their frontmatter. The `--force` option allows you to replace an existing UID with a new one.

**Use with caution**: Replacing UIDs may break links or references to the page within your vault.

### new

```bash
obsidian-cli new PAGE_OR_FILE --force
```

By default, the `new` command will not overwrite existing files. The `--force` option allows you to overwrite an existing file with a new one.

**Use with caution**: This will completely replace the contents of the existing file without confirmation.

### rm

```bash
obsidian-cli rm PAGE_OR_FILE --force
```

By default, the `rm` command will prompt for confirmation before deleting a file. The `--force` option bypasses this confirmation and deletes the file immediately.

**Use with caution**: There is no way to recover files deleted with this command unless you have a backup or version control.

## Best Practices

1. **Use verbose mode**: Combine the force option with verbose mode (`--verbose`) to get additional information about what's being changed:

   ```bash
   obsidian-cli --verbose new "My Note" --force
   ```

2. **Backup your vault**: Before performing batch operations with force flags, consider backing up your vault.

3. **Test on a sample**: When writing scripts that use force options, test on a small subset of files first.

4. **Automation**: Force options are particularly useful in automated scripts where interactive confirmation isn't possible.
