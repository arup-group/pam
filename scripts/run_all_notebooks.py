import glob
import subprocess


def find_notebooks():
    paths = glob.glob("examples/*.ipynb")
    paths.sort()
    return paths

def execute(path):
    shell_cmd = [
            "jupyter",
            "nbconvert",
            "--to",
            "notebook",
            "--execute",
            f"'{path}'",
            "--inplace"
        ]
    subprocess.call(' '.join(shell_cmd), shell=True)


if __name__ == "__main__":
    notebooks = find_notebooks()
    for notebook in notebooks:
        execute(notebook)


