import os
import subprocess
import sys
import difflib
import re
import shutil
import json
import canvas
import statistics
import matplotlib.pyplot as plt

if len(sys.argv) < 3:
    print('Usage: test_cl.py homework compile/run/check/grade/stats/upload')
    sys.exit()

notepad_file = 'C:/Program Files (x86)/Notepad++/notepad++.exe'
vim_file = 'C:/Program Files (x86)/Vim/vim74/gvim.exe'
editor = vim_file
if sys.argv[2] == 'grade' or sys.argv[2] == 'regrade':
    if os.path.isfile(vim_file):
        editor = vim_file
    elif os.path.isfile(notepad_file):
        editor = notepad_file
    else:
        print('Please install either vim or notepad++')
        sys.exit()

# compare the output of a student's program to the reference output, writing the results into a
# given result file. we also need the name of the reference .cpp file, since this will tell us
# whether the student has named their file correctly
def compare(reference_output, student_output, result_file, reference_cpp_file):
    diff = ''
    case_failed_count = 0
    case_number = 0
    case_failed = False
    match_case_number = re.compile(" Case (\d+):")

    if os.path.isfile(reference_output):
        with open(reference_output, 'r') as ref_out, open(student_output, 'r') as student_out:
                reference = ref_out.readlines()
                student = student_out.readlines()
                # TODO: Strip leading/trailing whitespace and newlines from student solution
                # but don't strip the last newline character? Or strip all trailing and stick
                # the last newline character back on
                for line in difflib.unified_diff(reference, student, fromfile='reference', tofile='student'):
                    case_match = match_case_number.match(line)
                    if case_match:
                        case_number = int(case_match.group(1))
                        case_failed = False
                    if not case_failed and line.startswith('-') and not line.startswith('---'):
                        case_failed_count += 1
                        case_failed = True
                    diff += line
    elif not os.path.getsize(student_output): # student program produces no outputs (NOTE: this output
                                              # file is there even if the student program didn't run,
                                              # so we need to check for the size)
        case_failed_count = 1
    elif not os.path.isfile(reference_cpp_file): # student named their file wrongly
        case_failed_count = 1
    elif not os.path.isfile(reference_output): # this problem has no reference outputs, and no check
                                               # program, so we need to check manually
        case_failed_count = 0

    with open(result_file, 'w') as result_out:
        result_out.write(diff)
        result_out.write('\nCases Failed: ' + str(case_failed_count) + '\n')
        result_out.write('Total Cases: ' + str(case_number + 1) + '\n')

match_warning = re.compile('.* warning C\d+:')
match_error = re.compile('.* error C\d+:')
# count the number of compiler warnings and errors in the input file, and write the results to the
# output file
def count_warnings_errors(input_file, output_file):
    warnings = []
    errors = []
    with open(input_file, 'r') as f:
        content = f.readlines()
        for line in content:
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

match_score = re.compile("Grade: (\d+)")
# Open files for final grading
def grade(file, stdout_file, result_file, grade_file, ref_stdout_file):
    # Copy autograde summary (diff, warnings, failed case report) to the
    # final grade file
    if not check_grading(grade_file):
        shutil.copyfile(result_file, grade_file)
    if os.path.isfile(ref_stdout_file):
        subprocess.call([editor, file, stdout_file, ref_stdout_file, grade_file])
    else:
        print(grade_file)
        print(stdout_file)
        print(file)
        print(editor)
        subprocess.call([editor, file, stdout_file, grade_file])
        print('hello')

# Check that a score was correctly assigned to the problem
def check_grading(grade_file):
    if not os.path.isfile(grade_file):
        return False
    grade_content = open(grade_file, 'r').readlines()
    return not (match_score.match(grade_content[-1]) is None)

def build_final_score(student_files, score_scale):
    grade_files = [f for f in student_files if f.endswith("_grade.txt")]
    if len(grade_files) == 0:
        print('Error! Can\'t compute final grade for an graded student {}!'
                .format(os.getcwd()))
        #sys.exit(1)
        return

    grade_info = ['Total Score']
    grade_total = 0
    for f in grade_files:
        with open(f, 'r') as fg:
            grade_info.append('####### ' + f + ' ########\n')
            lines = fg.readlines()
            # Find the grade for this assignment and add it to the total
            assignment_score = match_score.match(lines[-1])
            if assignment_score:
                grade_total += int(assignment_score.group(1)) * score_scales[f]
            grade_info += lines
            grade_info.append('################################\n\n')

    grade_info[0] = 'Total Score: ' + str(grade_total) + '\n\n'
    grade_comment = ''.join(grade_info)
    with open('final_score.diff', 'w') as f:
        f.write(grade_comment)
    subprocess.call([editor, 'final_score.diff'])

# Compile all the *_grade.txt files for a student into a single one and
# compute the overall score. Then submit the grade for the assignment
# and post the compile grade files as a comment on it
def upload_grade(canvas):
    with open('AUTOGRADE.json', 'r') as f, open('final_score.diff', 'r') as fg:
        grade_comment = fg.readlines()
        grade_match = re.match('Total Score: (\d+)', grade_comment[0])
        if not grade_match:
            print('Error grading {}, no total score assigned'.format(os.getcwd()))
            sys.exit(1)
        grade_total = int(grade_match.group(1))
        student = json.load(f)
        canvas.gradeAndCommentSubmission(None, student['canvasSubmission']['assignment_id'],
            student['canvasStudent']['id'], grade_total, grade_comment)

# Compute the student's total score from their grade files
def compute_total_score(student_files, score_scale):
    grade_files = [f for f in student_files if f.endswith("_grade.txt")]
    if len(grade_files) == 0:
        print('Error! Can\'t get grade stats for an ungraded student!')
        sys.exit(1)

    grade_total = 0
    for f in grade_files:
        with open(f, 'r') as fg:
            lines = fg.readlines()
            # Find the grade for this assignment and add it to the total
            assignment_score = match_score.match(lines[-1])
            if assignment_score:
                grade_total += int(assignment_score.group(1)) * score_scales[f]
    return grade_total

print('Grading ' + sys.argv[1])
main_dir = os.path.abspath('.')
homework_dir = os.path.abspath('./submissions/' + sys.argv[1])
ref_homework_dir = os.path.abspath('./reference/' + sys.argv[1])
# Collect list of all program files we're expecting to find
ref_file_names = []
score_scales = {}
for f in next(os.walk(ref_homework_dir))[2]:
    base, ext = os.path.splitext(f)
    if not base.endswith('_check') and (ext == '.cpp' or ext == '.cc'):
        ref_file_names.append(f)
        with open(ref_homework_dir + '/' + f, 'r') as scale:
            score_scales[base + '_grade.txt'] = int(scale.readlines()[0]) / 10.0


if sys.argv[2] == 'upload':
    c = canvas.canvas()
    courses = c.getCourses()
    course_id = c.findCourseId(courses, 'CS 6962-001 Fall 2015 Programming for Engineers')
    c = canvas.canvas(courseId=course_id)

grade_stats = []
# Collect the list of all student directories
for dir in next(os.walk(homework_dir))[1]:
    student_dir = os.path.abspath(homework_dir + '/' + dir)
    print('Processing student ' + student_dir)
    os.chdir(student_dir)
    files = [f for f in next(os.walk(student_dir))[2]]
    # Collect the list of all of the student's files if we're uploading their
    # total score
    if sys.argv[2] == 'upload':
        upload_grade(c)
        continue
    elif sys.argv[2] == 'stats':
        grade_stats.append(compute_total_score(files, score_scales))
        continue

    for file in files:
        base, ext = os.path.splitext(file)
        if ext == '.cpp' or ext == '.cc':
            # Skip incorrectly named files
            if not (file in ref_file_names):
                print('Skipping incorrectly named encountered: ' + file)
                continue

            cl_stdout_file = base + '_cl.txt'
            stdin_file = ref_homework_dir + '/' + base + '_stdin.txt'
            stdout_file = base + '_stdout.txt'
            ref_stdout_file = ref_homework_dir + '/' + base + '_stdout.txt'
            result_file = base + '_results.txt'
            grade_file = base + '_grade.txt'
            check_prog = ref_homework_dir + '/' + base + '_check.exe'
            reference_cpp_file = ref_homework_dir + '/' + file
            # Compile student's programs
            if sys.argv[2] == 'compile':
                print('Compiling ' + file)
                with open(cl_stdout_file, 'w') as cl_stdout:
                    build = subprocess.Popen(['cl.exe', '/W4', '/EHsc', file], stdout=cl_stdout,
                        universal_newlines=True)
                    build.wait()
            # Run all student programs and save output results
            elif ((not os.path.isfile(stdout_file) or not os.path.getsize(stdout_file))\
					and sys.argv[2] == 'run') or (sys.argv[2] == 'rerun'):
                exe = base + '.exe'
                print('Running ' + exe)
                prog = None
                if os.path.isfile(stdin_file): # run with input
                    with open(stdin_file, 'r') as stdin_, open(stdout_file, 'w') as stdout_:
                        try:
                            prog = subprocess.Popen([exe], stdin=stdin_, stdout=stdout_, universal_newlines=True)
                            prog.wait(5)
                        except subprocess.TimeoutExpired:
                            print('Time out')
                            prog.kill()
                        except:
                            print('Exception!')
                else: # run without input
                    with open(stdout_file, 'w') as stdout_:
                        try:
                            prog = subprocess.Popen([exe], stdout=stdout_, universal_newlines=True)
                            prog.wait(5)
                        except subprocess.TimeoutExpired:
                            print('Time out')
                            prog.kill()
                        except:
                            print('Exception!')
            # Diff student outputs with the expected solution
            elif sys.argv[2] == 'check':
                print('Checking ' + base)
                if (os.path.isfile(check_prog)): # use the check program
                    print('Using ' + check_prog)
                    with open(stdout_file, 'r') as stdout_, open(result_file, 'w') as result_:
                        check = subprocess.Popen([check_prog], stdin=stdout_, stdout=result_,
                            universal_newlines=True)
                        check.wait()
                else: # simply compare output files
                    compare(ref_stdout_file, stdout_file, result_file, reference_cpp_file)
                # count the number of warnings and errors
                count_warnings_errors(cl_stdout_file, result_file)
            # Open the student programs and outputs for final grading
            elif (sys.argv[2] == 'grade' and not check_grading(grade_file)) or sys.argv[2] == 'regrade':
                if sys.argv[2] == 'regrade':
                    os.remove(grade_file)
                grade(file, stdout_file, result_file, grade_file, ref_stdout_file)
                # Check that a final grade for the assignment has been entered in the grade file
                if not check_grading(grade_file):
                    print("Error! No grade assigned for " + file)

    if sys.argv[2] == 'grade' or sys.argv[2] == 'regrade':
        graded_files = [f for f in next(os.walk(student_dir))[2]]
        build_final_score(graded_files, score_scales)


# Compute final score statistics and log them
if sys.argv[2] == 'stats':
    print("Score Summary:\n\tMean = {}\n\tStd dev = {}\n\tMedian = {}\n\tMax = {}\n\tMin = {}\n"
            .format(statistics.mean(grade_stats), statistics.stdev(grade_stats),
                statistics.median(grade_stats), max(grade_stats), min(grade_stats)))
    plt.hist(grade_stats, bins=20)
    plt.title("Histogram")
    plt.xlabel("Value")
    plt.ylabel("Frequency")
    plt.show()
