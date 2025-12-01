---
inclusion: always
---

# Python Environment Configuration

## Conda Environment

**IMPORTANT**: All Python commands MUST be executed using the `short-video` conda environment.

### Running Python Commands

Always use one of these patterns:

```bash
conda run -n short-video python script.py
```

Or activate the environment first:

```bash
conda activate short-video
python script.py
```

### Installing Packages

```bash
conda run -n short-video pip install package-name
```

### Running Tests

```bash
conda run -n short-video pytest
```

This ensures consistent Python environment across all operations.
