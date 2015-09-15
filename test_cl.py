import os
import subprocess
import sys
import difflib
import re
import shutil

if len(sys.argv) < 3:
    print('Usage: test_cl.py homework compile/run/check/grade')
    sys.exit()

notepad_file = 'C:/Program Files (x86)/Notepad++/notepad++.exe'
vim_file = 'C:/Program Files (x86)/Vim/vim74/gvim.exe'
editor = notepad_file
if sys.argv[2] == 'grade':
    if not os.path.isfile(editor):
        if editor == notepad_file:
            print('Please install Notepad++')
        else:
            print('Please install gvim')
        sys.exit()

# compare the output of a student's program to the reference output, writing the results into a
# given result file
def compare(reference_output, student_output, result_file):
    diff = ''
    case_failed_count = 0
    case_number = 0
    case_failed = False
    match_case_number = re.compile(" Case (\d+):")
    with open(reference_output, 'r') as ref_out:
        with open(student_output, 'r') as student_out:
            reference = ref_out.readlines()
            student = student_out.readlines()
            # TODO: Strip leading/trailing whitespace and newlines from student solution
            # but don't strip the last newline character? Or strip all trailing and stick
            # the last newline character back on
            for line in difflib.unified_diff(reference, student, fromfile='reference', tofile='student'):
                print(line)
                case_match = match_case_number.match(line)
                if case_match:
                    case_number = int(case_match.group(1))
                    case_failed = False
                if not case_failed and line.startswith('-') and not line.startswith('---'):
                    case_failed_count += 1
                    case_failed = True
                diff += line
    with open(result_file, 'w') as result_out:
        result_out.write(diff)
        result_out.write('\nCases Failed: ' + str(case_failed_count) + '\n')
        result_out.write('Total Cases: ' + str(case_number + 1) + '\n')

match_warning = re.compile('.*: warning C\d+:')
match_error = re.compile('.*: error C\d+:')
# count the number of compiler warnings and errors in the input file, and write the results to the
# output file
def count_warnings_errors(input_file, output_file):
    warnings = []
    errors = []
    with open(input_file, 'r') as f:
        content = f.readlines()
        for line in content:
            print(line)
            warning = match_warning.match(line)
            if warning:
                warnings.append(line)
            error = match_error.match(line)
            if error:
                errors.append(line)
    with open(output_file, 'a') as f:
        f.write('\n')
        f.write('Warnings: ' + str(len(warnings)) + '\n')
        f.write(''.join(warnings) + '\n')
        f.write('Errors: ' + str(len(errors)) + '\n')
        f.write(''.join(errors))

# Open files for final grading
def grade(file, stdout_file, result_file, grade_file, ref_stdout_file):
    # Copy autograde summary (diff, warnings, failed case report) to the
    # final grade file
    shutil.copyfile(result_file, grade_file)
    if os.path.isfile(ref_stdout_file):
        subprocess.call([editor, file, result_file, stdout_file, grade_file])
    else:
        subprocess.call([editor, file, result_file, stdout_file, ref_stdout_file,
            grade_file])

match_score = re.compile("Grade: (\d+)")
# Check that a score was correctly assigned to the problem
def check_grading(grade_file):
    grade_content = open(grade_file, 'r').readlines()
    return not (match_score.match(grade_content[-1]) is None)

print('Grading ' + sys.argv[1])
main_dir = os.path.abspath('.')
homework_dir = os.path.abspath('./submissions/' + sys.argv[1])
# Collect the list of all student directories
student_dirs = []
for _, s, _ in os.walk(homework_dir):
    student_dirs += s

for student_dir in student_dirs:
    student_dir = os.path.abspath(homework_dir + '/' + student_dir)
    os.chdir(student_dir)
    # Collect the list of all of the student's files
    files = []
    for _, _, f in os.walk(student_dir):
        files += f
    for file in files:
        base, ext = os.path.splitext(file)
        if ext == '.cpp' or ext == '.cc':
            cl_stdout_file = base + '_cl.txt'
            stdin_file = homework_dir + '/' + base + '_stdin.txt'
            stdout_file = base + '_stdout.txt'
            ref_stdout_file = homework_dir + '/' + base + '_stdout.txt'
            result_file = base + '_results.txt'
            grade_file = base + '_grade.txt'
            check_prog = homework_dir + '/' + base + '_check.exe'
            # Compile student's programs
            if sys.argv[2] == 'compile':
                print('Compiling ' + file)
                with open(cl_stdout_file, 'w') as cl_stdout:
                    subprocess.Popen(['cl.exe', '/W4', '/EHsc', file], stdout=cl_stdout,
                            universal_newlines=True)
            # Run all student programs and save output results
            elif sys.argv[2] == 'run':
                print('Running ' + base + '.exe')
                if os.path.isfile(stdin_file): # run with input
                    with open(stdin_file, 'r') as stdin_, open(stdout_file, 'w') as stdout_:
                        subprocess.Popen([base], stdin=stdin_, stdout=stdout_, universal_newlines=True)
                else: # run without input
                    if (os.path.isfile('./' + base + '.exe')):
                        with open(stdout_file, 'w') as stdout_:
                            subprocess.Popen([base + '.exe'], stdout=stdout_, universal_newlines=True)
            # Diff student outputs with the expected solution
            elif sys.argv[2] == 'check':
                print('Checking ' + base)
                if (os.path.isfile(check_prog)): # use the check program
                    with open(stdout_file, 'r') as stdout_, open(result_file, 'w') as result_:
                        subprocess.Popen([check_prog], stdin=stdout_, stdout=result_,
                                universal_newlines=True)
                else: # simply compare output files
                    compare(ref_stdout_file, stdout_file, result_file)
                # count the number of warnings and errors
                count_warnings_errors(cl_stdout_file, result_file)
            # Open the student programs and outputs for final grading
            elif sys.argv[2] == 'grade':
                grade(file, stdout_file, result_file, grade_file, ref_stdout_file)
                # Check that a final grade for the assignment has been entered in the grade file
                while not check_grading(grade_file):
                    print("Error! No grade assigned for " + file)
                    grade(file, stdout_file, result_file, grade_file, ref_stdout_file)

