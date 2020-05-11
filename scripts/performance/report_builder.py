import argparse

from jinja2 import Environment, FileSystemLoader, select_autoescape


def parse_mprof_file(mprof_file_path):
    with open(mprof_file_path) as prof_file:
        prof_lines = prof_file.readlines()
        prof_cmd = prof_lines[0].split('CMDLINE')[1].strip()
        start_time = float(prof_lines[1].split(" ")[2])
        end_time = float(prof_lines[-1].split(" ")[2])
        running_time = end_time - start_time
        running_time = float("{:.2f}".format(running_time))
        max_mem = 0
        for profile_line in prof_lines[1:]:
            tokens = profile_line.split(" ")
            mem_level = float(tokens[1])
            if mem_level > max_mem:
                max_mem = mem_level
        max_mem = float("{:.2f}".format(max_mem))
    return prof_cmd, running_time, max_mem


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(
        description='Generate a profiling report from a template file and some parameters')
    arg_parser.add_argument('-t',
                            '--template-file',
                            help='the path to the Jinja template report file',
                            required=True)
    arg_parser.add_argument('-p',
                            '--profile-file',
                            help='the mprof file for the process being profiled',
                            required=True)
    arg_parser.add_argument('-ppl',
                            '--profile-plot',
                            help='the mprof plot image for the process being profiled',
                            required=True)
    arg_parser.add_argument('-bp',
                            '--benchmark-profile-file',
                            help='the mprof file for the benchmark to compare the process against')
    arg_parser.add_argument('-bpl',
                            '--benchmark-profile-plot',
                            help='the mprof plot image for benchmark to compare the process against',
                            required=True)
    arg_parser.add_argument('-mt',
                            '--memory-tolerance',
                            help='the tolerance value in MB for memory footprint',
                            required=True)
    arg_parser.add_argument('-rt',
                            '--run-time-tolerance',
                            help='the tolerance value in seconds for running time',
                            required=True)
    args = vars(arg_parser.parse_args())

    template_file = args['template_file']
    profile_file = args['profile_file']
    benchmark_profile_file = args['benchmark_profile_file']
    print("Creating performance report for data in {} (benchmark {}) using template {}".format(profile_file,
                                                                                               benchmark_profile_file,
                                                                                               template_file))
    prof_cmd, running_time, max_mem = parse_mprof_file(profile_file)
    benchmark_prof_cmd, benchmark_running_time, benchmark_max_mem = parse_mprof_file(benchmark_profile_file)

    env = Environment(loader=FileSystemLoader('.'), autoescape=select_autoescape(['html', 'xml']))
    template = env.get_template(template_file)
    html_report = template.render(command=prof_cmd,
                                  benchmark_command=benchmark_prof_cmd,
                                  running_time=running_time,
                                  benchmark_running_time=benchmark_running_time,
                                  max_mem=max_mem,
                                  benchmark_max_mem=benchmark_max_mem,
                                  profile_file=profile_file,
                                  benchmark_profile_file=benchmark_profile_file,
                                  profile_plot=args['profile_plot'],
                                  benchmark_profile_plot=args['benchmark_profile_plot'],
                                  mem_tolerance=float(args['memory_tolerance']),
                                  run_time_tolerance=float(args['run_time_tolerance']))

    with open('pam-performance-report.html', 'w') as report:
        report.write(html_report)
    print("Performance report written to {}".format('pam-performance-report.html'))
