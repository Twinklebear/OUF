import os
import sys
import re
import shutil
import json
import subprocess
import datetime
import canvas
import autograder
import grading
from time import sleep

# Check that cl.exe is accessible
try:
    subprocess.Popen(['cl.exe'], universal_newlines=True).wait()
except:
    print("Fatal Error! cl.exe is not available, did you setup your environment?")
    sys.exit(1)

# Configure the server for the assignment we're checking
config = autograder.config()
settings = config.get()
homework_dir_name = settings['subdirName']
homework_path = os.path.abspath(homework_dir_name)
course_name = settings['courseName']
assignment_name = settings['assignmentName']

# Collect list of all program files we're expecting to find
ref_homework_path = os.path.abspath('../reference/' + homework_dir_name)
ref_file_names = []
score_scales = {}
for f in next(os.walk(ref_homework_path))[2]:
    base, ext = os.path.splitext(f)
    if not base.endswith('_check') and (ext == '.cpp' or ext == '.cc'):
        ref_file_names.append(f)
        with open(ref_homework_path + '/' + f, 'r') as scale:
            score_scales[base + '_grade.txt'] = int(scale.readlines()[0]) / 10.0

c = canvas.canvas()
courses = c.getCourses()
course_id = c.findCourseId(courses, 'CS 6962-001 Fall 2015 Programming for Engineers')
c = canvas.canvas(courseId=course_id)

while True:
    print("Checking for new submissions")
    students = c.downloadAssignment(courseName=course_name, assignmentName=assignment_name,
            subdirName=homework_path)
    print("Downloaded new submissions from {}".format(students))
    for student_id in students:
        student_dir = os.path.abspath(homework_path + "/" + str(student_id))
        print('Processing student ' + student_dir)
        os.chdir(student_dir)
        files = [f for f in next(os.walk(student_dir))[2]]

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
                stdin_file = ref_homework_path + '/' + base + '_stdin.txt'
                stdout_file = base + '_stdout.txt'
                ref_stdout_file = ref_homework_path + '/' + base + '_stdout.txt'
                result_file = base + '_results.txt'
                grade_file = base + '_grade.txt'
                check_prog = ref_homework_path + '/' + base + '_check.exe'
                reference_cpp_file = ref_homework_path + '/' + file

                # Compile the student's submission
                print('Compiling ' + file)
                grading.compile(cl_stdout_file, file)

                # Run the student's submission
                exe = base + '.exe'
                print('Running ' + exe)
                prog = None
                if os.path.isfile(stdin_file): # run with input
                    with open(stdin_file, 'r') as stdin_, open(stdout_file, 'w') as stdout_:
                        try:
                            prog = subprocess.Popen([exe], stdin=stdin_, stdout=stdout_, universal_newlines=True)
                            prog.wait(5)
                            if prog.returncode != 0:
                                with open(cl_stdout_file, "a") as f:
                                    f.write("\nProcess Status: terminated in error, return code: {}\n"
                                            .format(prog.returncode))
                        except subprocess.TimeoutExpired:
                            print('Time out')
                            prog.kill()
                            with open(cl_stdout_file, "a") as f:
                                f.write("\nProcess Status: Timed Out\n")
                        except:
                            print('Exception!')
                else: # run without input
                    with open(stdout_file, 'w') as stdout_:
                        try:
                            prog = subprocess.Popen([exe], stdout=stdout_, universal_newlines=True)
                            prog.wait(5)
                            if prog.returncode != 0:
                                with open(cl_stdout_file, "a") as f:
                                    f.write("\nProcess Status: terminated in error, return code: {}\n"
                                            .format(prog.returncode))
                        except subprocess.TimeoutExpired:
                            print('Time out')
                            prog.kill()
                            with open(cl_stdout_file, "a") as f:
                                f.write("\nProcess Status: Timed Out\n")
                        except:
                            print('Exception!')

                # Check the student's submision
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

                # Compile the grading document but don't assign a grade to the student
                # since the server has no idea what grade to assign
                grading.grade(file, stdout_file, result_file, grade_file, ref_stdout_file, None)

        # Build the final score file
        print("Building final score for " + student_dir)
        graded_files = [f for f in next(os.walk(student_dir))[2]]
        grading.build_final_score(graded_files, score_scales, None)
        # Upload their grade
        grading.upload_grade(c)

    # Sleep for 1 hour to poll again
    print("Students graded for {}".format(datetime.datetime.now()))
    sleep(60 * 60)

