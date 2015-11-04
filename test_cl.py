import os
import subprocess
import sys
import difflib
import re
import shutil
import json
import canvas
import statistics
import grading
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
        grading.upload_grade(c)
        continue
    elif sys.argv[2] == 'stats':
        grade_stats.append(grading.compute_total_score(files, score_scales))
        continue

    for file in files:
        base, ext = os.path.splitext(file)
        if ext == '.cpp' or ext == '.cc':
            if len(sys.argv) > 3 and base != sys.argv[3]: # if a file name is provided, skip other files
                continue
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
                grading.compile(cl_stdout, file)
            # Run all student programs and save output results
            elif ((not os.path.isfile(stdout_file) or not os.path.getsize(stdout_file))\
					and sys.argv[2] == 'run') or (sys.argv[2] == 'rerun'):
                exe = base + '.exe'
                print('Running ' + exe)
                grading.run_student(exe, stdin_file, stdout_file, cl_stdout_file)
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
                    grading.compare(ref_stdout_file, stdout_file, result_file, reference_cpp_file)
                # count the number of warnings and errors
                grading.count_warnings_errors(cl_stdout_file, result_file)
            # Open the student programs and outputs for final grading
            elif (sys.argv[2] == 'grade' and not grading.check_grading(grade_file)) or sys.argv[2] == 'regrade':
                grading.grade(file, stdout_file, result_file, grade_file, ref_stdout_file, editor)
                # Check that a final grade for the assignment has been entered in the grade file
                if not grading.check_grading(grade_file):
                    print("Error! No grade assigned for " + file)

    if sys.argv[2] == 'grade' or sys.argv[2] == 'regrade':
        graded_files = [f for f in next(os.walk(student_dir))[2]]
        grading.build_final_score(graded_files, score_scales, editor)


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

