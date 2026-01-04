# Pipely Project Scaffolder

Pipely now focuses on one task: creating a tidy project folder structure. Artists answer two questions and get a ready-to-use directory tree.

## Command

```sh
pipely init
```

Prompts for:
1. Project name
2. Project type (`animation`, `game`, `art`)

## Templates

### Animation
```
01_ADMIN/
02_PREPRO/
03_ASSETS/
04_SHOTS/
05_WORK/
06_DELIVERY/
z_TEMP/
```

### Game Development
```
01_DESIGN/
02_ART/
03_TECH/
04_AUDIO/
05_QA/
06_RELEASE/
z_TEMP/
```

### Generic Art
```
01_REFERENCE/
02_WIP/
03_EXPORTS/
04_DELIVERY/
z_TEMP/
```

## Notes

- No files are created.
- Defaults to the current working directory; override with `--root` or `PIPELY_ROOT`.
- Works the same on Windows, macOS, and Linux thanks to `pathlib` + safe slugification.
