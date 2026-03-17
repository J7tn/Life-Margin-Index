# Install Guide (Like You Are 5)

Imagine this program is a toy box.

We need to do three tiny things:

1. go to the toy box folder,
2. tell Python to set up the toy labels,
3. try one toy command.

## Step 1: Open the project folder

Open your terminal and go to this folder:

`c:\Users\jntn\Documents\GitHub\Life Margin Index`

If you are in PowerShell:

`cd "c:\Users\jntn\Documents\GitHub\Life Margin Index"`

## Step 2: Install the program tools

Type this:

`pip install -e .`

What this means in kid words:

- `pip` = helper robot for Python tools
- `install` = put tools where Python can find them
- `-e .` = use this folder directly, so changes update right away

## Step 3: Check that it worked

Type this:

`lmi --help`

If you see help text, you did it right.

## Step 4: Try the first real command

Type this:

`lmi validate --input examples/sample_dataset.csv`

If it prints a little result dictionary, it is working.

## Step 5: Make results

Compute file:

`lmi compute --input examples/sample_dataset.csv --output analysis/output/lmi_output.csv`

Summary file:

`lmi report --input analysis/output/lmi_output.csv --output analysis/output/lmi_summary.json`

Now you have:

- `analysis/output/lmi_output.csv`
- `analysis/output/lmi_summary.json`

## If `lmi` says "not recognized"

No worries. Use Python directly:

- `python src/lmi_tool.py validate --input examples/sample_dataset.csv`
- `python src/lmi_tool.py compute --input examples/sample_dataset.csv --output analysis/output/lmi_output.csv`
- `python src/lmi_tool.py report --input analysis/output/lmi_output.csv --output analysis/output/lmi_summary.json`

That does the same thing.
