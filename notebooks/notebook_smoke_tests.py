import argparse
import glob
import subprocess
import sys

from datetime import datetime
from pprint import pprint

from colorama import Fore, Style

TICK_SYMBOL = u'\u2713'
CROSS_SYMBOL = u'\u274C'


def parse_args(cmd_args):
    arg_parser = argparse.ArgumentParser(description='Smoke test a set of Jupyter notebook files')
    arg_parser.add_argument('-d',
                            '--notebook-directory',
                            help='the path to the directory containing the notebooks to test',
                            required=True)
    arg_parser.add_argument('-k',
                            '--kernel-name',
                            action='append',
                            help='the name of an iPython kernel to install',
                            required=True)
    return vars(arg_parser.parse_args(cmd_args))


def print_banner():
    banner = '''
 a,  8a
 `8, `8)                            ,adPPRg,
  8)  ]8                        ,ad888888888b
 ,8' ,8'                    ,gPPR888888888888
,8' ,8'                 ,ad8""   `Y888888888P
8)  8)              ,ad8""        (8888888""
8,  8,          ,ad8""            d888""
`8, `8,     ,ad8""            ,ad8""
 `8, `" ,ad8""            ,ad8""
    ,gPPR8b           ,ad8""
   dP:::::Yb      ,ad8""
   8):::::(8  ,ad8""
   Yb:;;;:d888""
    "8ggg8P"
 _   _ ____    ____  __  __  ___  _  _______   _____ _____ ____ _____
| \ | | __ )  / ___||  \/  |/ _ \| |/ / ____| |_   _| ____/ ___|_   _|
|  \| |  _ \  \___ \| |\/| | | | | ' /|  _|     | | |  _| \___ \ | |
| |\  | |_) |  ___) | |  | | |_| | . \| |___    | | | |___ ___) || |
|_| \_|____/  |____/|_|  |_|\___/|_|\_\_____|   |_| |_____|____/ |_|
    '''
    print("{}{}{}".format(Fore.CYAN, banner, Style.RESET_ALL))


def install_ipython_kernel(kernel_name):
    print("Making sure we have an iPython kernel called {}{}{} installed...".format(Fore.YELLOW,
                                                                                    kernel_name,
                                                                                    Style.RESET_ALL))
    kernel_install_cmd = [
        'ipython', 'kernel', 'install',
        '--name', '"{}"'.format(kernel_name),
        '--user'
    ]
    return run_shell_command(kernel_install_cmd)


def execute_notebook(notebook_path):
    print("Executing notebook '{}{}{}'...".format(Fore.YELLOW, notebook_path, Style.RESET_ALL))
    execute_notebook_cmd = [
        'jupyter', 'nbconvert',
        '--to', 'notebook',
        '--execute', '"{}"'.format(notebook_path),
        '--output-dir=/tmp'
    ]
    return run_shell_command(execute_notebook_cmd)


def run_shell_command(shell_cmd):
    print(Fore.BLUE + ' '.join(shell_cmd))
    rc = subprocess.call(' '.join(shell_cmd), shell=True)
    print("{}Shell process return value was {}{}{}".format(Style.RESET_ALL, Fore.YELLOW, rc, Style.RESET_ALL))
    return rc, ' '.join(shell_cmd)


def find_notebooks(notebook_dir):
    notebook_paths = glob.glob("{}/*.ipynb".format(notebook_dir))
    notebook_paths.sort()
    return notebook_paths


def print_summary(notebook_results_dict):
    print("\n                     Summary")
    print("-------------------------------------------------------------")
    for notebook_file, result in notebook_results_dict.items():
        short_name = notebook_file.split('/')[-1]
        colour = Fore.GREEN if result == 0 else Fore.RED
        result_symbol = TICK_SYMBOL if result == 0 else CROSS_SYMBOL
        print("{}: {}{}{}".format(short_name, colour, result_symbol, Style.RESET_ALL))


if __name__ == '__main__':
    print_banner()
    start = datetime.now()
    command_args = parse_args(sys.argv[1:])
    print("Smoke testing Jupyter notebooks in {}'{}'{} directory".format(Fore.YELLOW,
                                                                         command_args['notebook_directory'],
                                                                         Style.RESET_ALL))
    notebooks = find_notebooks(command_args['notebook_directory'])
    print("Found {}{}{} notebooks files in {}{}{}".format(Fore.YELLOW,
                                                          len(notebooks),
                                                          Style.RESET_ALL,
                                                          Fore.YELLOW,
                                                          command_args['notebook_directory'],
                                                          Style.RESET_ALL))
    if not notebooks:
        print("No notebooks to test - our work here is done. Double check the {}{}{} directory if this seems wrong."
              .format(Fore.YELLOW, command_args['notebook_directory'], Style.RESET_ALL))
        sys.exit(0)

    pprint(notebooks, width=120)
    for kernel in command_args['kernel_name']:
        return_code, cmd = install_ipython_kernel(kernel)
        if return_code:
            print("{}Warning: Kernel installation shell command did not exit normally"
                  " - this may cause problems later{}".format(Fore.RED, Style.RESET_ALL))

    notebook_results = {}
    for notebook in notebooks:
        print('------------------------------------------------------')
        return_code, cmd = execute_notebook(notebook)
        notebook_results[notebook] = return_code

    print('------------------------------------------------------')
    print("\nFinished the smoke test in {}{}{}".format(Fore.YELLOW, datetime.now() - start, Style.RESET_ALL))
    print_summary(notebook_results)
    sys.exit(sum(notebook_results.values()))
