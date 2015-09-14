import os
import subprocess
import sys

if len(sys.argv) < 3:
    print 'Usage: test_cl.py homework compile/run/check/grade'
    sys.exit()

notepad_file = 'C:/Program Files (x86)/Notepad++/notepad++.exe'
if sys.argv[2] == 'grade':
    if not os.path.isfile(notepad_file):
        print 'Please install Notepad++'
        sys.exit()

# compare the output of a student's program to the reference output, writing the results into a
# given result file
def compare(reference_output, student_output, result_file):
    pass # TODO

# count the number of compiler warnings and errors in the input file, and write the results to the
# output file
def count_warning_error(input_file, output_file):
    pass # TODO

print 'Grading', sys.argv[1]
main_dir = os.path.abspath('.')
homework_dir = os.path.abspath('./autograder/' + sys.argv[1])
for student_dir in os.walk(homework_dir).next()[1]:
    student_dir = os.path.abspath(homework_dir + '/' + student_dir)
    os.chdir(student_dir)
    print student_dir
    for file in os.walk(student_dir).next()[2]:
        base, ext = os.path.splitext(file)
        if ext == '.cpp' or ext == '.cc':
            cl_stdout_file = base + '_cl.txt'
            stdin_file = main_dir + '/' + base + '_stdin.txt'
            stdout_file = base + '_stdout.txt'
            ref_stdout_file = main_dir + '/' + base + '_stdout.txt'
            result_file = base + '_results.txt'
            grade_file = base + '_grade.txt'
            if (sys.argv[2] == 'compile'): # compile
                print 'Compiling ' + file
                with open(cl_stdout_file, 'w') as cl_stdout:
                    subprocess.Popen(['cl.exe', '/W4', '/EHsc', file], stdout=cl_stdout, universal_newlines=True)
            elif (sys.argv[2] == 'run'): # run
                print 'Running ' + base + '.exe'
                if (os.path.isfile(stdin_file)): # run with input
                    with open(stdin_file, 'r') as stdin_, open(stdout_file, 'w') as stdout_:
                        subprocess.Popen([base], stdin=stdin_, stdout=stdout_, universal_newlines=True)
                else: # run without input
                    if (os.path.isfile('./' + base + '.exe')):
                        with open(stdout_file, 'w') as stdout_:
                            subprocess.Popen([base + '.exe'], stdout=stdout_, universal_newlines=True)
            elif (sys.argv[2] == 'check'): # check outputs
                print 'Checking ' + base
                check_prog = main_dir + '/' + base + '_check.exe'
                if (os.path.isfile(check_prog)): # use the check program
                    with open(stdout_file, 'r') as stdout_, open(result_file, 'w') as result_:
                        subprocess.Popen([check_prog], stdin=stdout_, stdout=result_, universal_newlines=True)
                else: # simply compare output files
                    compare(ref_stdout_file, stdout_file, result_file)
                # count the number of warnings and errors
                count_warning_error(cl_stdout_file, result_file)
            elif (sys.argv[2] == 'grade'): # open the relevant text files to grade
                open(grade_file, 'a').close()
                if os.path.isfile(ref_stdout_file):
                    subprocess.call([notepad_file, file, result_file, stdout_file, grade_file])
                else:
                    subprocess.call([notepad_file, file, result_file, stdout_file, ref_stdout_file, grade_file])
