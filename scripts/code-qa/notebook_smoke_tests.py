import argparse
import glob
import subprocess
import sys
from datetime import datetime
from pprint import pprint

from colorama import Fore, Style
from rich.console import Console
from rich.table import Table


def parse_args(cmd_args):
    arg_parser = argparse.ArgumentParser(description='Smoke test a set of Jupyter notebook files')
    arg_parser.add_argument('-d',
                            '--notebook-directory',
                            help='the path to the directory containing the notebooks to test')
    arg_parser.add_argument('-k',
                            '--kernel-name',
                            action='append',
                            help='the name of an iPython kernel to install',
                            required=True)
    arg_parser.add_argument('-n',
                            '--notebook',
                            action='append',
                            help='an iPython notebook to execute - takes precedence over '
                                 '--notebook-directory if both are set')
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
        '--ExecutePreprocessor.timeout=120',
        '--to', 'notebook',
        '--execute', '"{}"'.format(notebook_path),
        '--output-dir=/tmp'
    ]
    return run_shell_command(execute_notebook_cmd)


def run_shell_command(shell_cmd):
    print(Fore.BLUE + ' '.join(shell_cmd))
    start_time = datetime.now()
    rc = subprocess.call(' '.join(shell_cmd), shell=True)
    running_time = datetime.now() - start_time
    print("{}Shell process return value was {}{}{}".format(Style.RESET_ALL, Fore.YELLOW, rc, Style.RESET_ALL))
    return rc, ' '.join(shell_cmd), running_time


def find_notebooks(notebook_dir):
    notebook_paths = glob.glob("{}/*.ipynb".format(notebook_dir))
    print("Found {}{}{} notebook files in {}{}{}".format(Fore.YELLOW,
                                                         len(notebook_paths),
                                                         Style.RESET_ALL,
                                                         Fore.YELLOW,
                                                         notebook_dir,
                                                         Style.RESET_ALL))
    if not notebook_paths:
        print("No notebooks to test - our work here is done. Double check the {}{}{} directory if this seems wrong."
              .format(Fore.YELLOW, notebook_dir, Style.RESET_ALL))
        sys.exit(0)
    notebook_paths.sort()
    return notebook_paths


def trim_time_delta(time_delta):
    return str(time_delta).split('.')[0]


def print_summary(notebook_results_dict):
    console = Console()
    console.print("")
    passes = [ret_code for ret_code, time in notebook_results.values() if ret_code == 0]
    failures = [ret_code for ret_code, time in notebook_results.values() if ret_code != 0]
    table_caption = "{} failed, {} passed in [yellow bold]{}[/yellow bold]" \
        .format(len(failures),
                len(passes),
                trim_time_delta(datetime.now() - start))
    results_table = Table(show_header=True,
                          header_style="bold magenta",
                          title="Smoke Test Summary",
                          caption=table_caption)
    results_table.add_column("Notebook", justify="left")
    results_table.add_column("Result", justify="left")
    results_table.add_column("Time", style="dim")
    for notebook_file, result in notebook_results_dict.items():
        short_name = notebook_file.split('/')[-1]
        exit_code, duration = result
        colour = "green" if exit_code == 0 else "red"
        outcome = "PASSED" if exit_code == 0 else "FAILED"
        results_table.add_row(short_name,
                              "[{}]{}[/{}]".format(colour, outcome, colour),
                              trim_time_delta(duration))
    console.print(results_table)
    console.print("")


def install_kernels(kernel_list):
    for kernel in kernel_list:
        exit_code, shell_cmd, exec_time = install_ipython_kernel(kernel)
        if exit_code:
            print("{}Warning: Kernel installation shell command did not exit normally for kernel '{}'"
                  " - this may cause problems later{}".format(Fore.RED, kernel, Style.RESET_ALL))


if __name__ == '__main__':
    start = datetime.now()
    command_args = parse_args(sys.argv[1:])
    print_banner()
    if command_args['notebook']:
        notebooks = command_args['notebook']
        notebooks.sort()
        print("Executing notebooks files {}{}{}".format(Fore.YELLOW,
                                                        notebooks,
                                                        Style.RESET_ALL))
    elif command_args['notebook_directory']:
        print("Smoke testing Jupyter notebooks in {}'{}'{} directory".format(Fore.YELLOW,
                                                                             command_args['notebook_directory'],
                                                                             Style.RESET_ALL))

        notebooks = find_notebooks(command_args['notebook_directory'])
        pprint(notebooks, width=120)
    print("")
    install_kernels(command_args['kernel_name'])
    print("")

    notebook_results = {}
    for notebook in notebooks:
        print('------------------------------------------------------')
        return_code, cmd, run_time = execute_notebook(notebook)
        notebook_results[notebook] = (return_code, run_time)

    print_summary(notebook_results)
    sys.exit(sum(ret_code for ret_code, time in notebook_results.values()))
