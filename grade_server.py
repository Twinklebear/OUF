import os
import sys
import re
import shutil
import json
import canvas
import autograder

# Configure the server for the assignment we're checking
config = autograder.config()
settings = config.get()
homework_dir = settings['subdirName']
course_name = settings['courseName']
assignment_name = settings['assignmentName']

c = canvas.canvas()
courses = c.getCourses()
course_id = c.findCourseId(courses, 'CS 6962-001 Fall 2015 Programming for Engineers')
c = canvas.canvas(courseId=course_id)

students = c.downloadAssignment(courseName=course_name, assignmentName=assignment_name,
        subdirName=homework_dir)
print("Downloaded {}".format(students))

for student_id in students:
    student_dir = os.path.abspath(homework_dir + '/' + str(student_id))
    print('Processing student ' + student_dir)
    os.chdir(student_dir)
    files = [f for f in next(os.walk(student_dir))[2]]
    print("Student files: {}".format(files))

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

            # Compile the student's submission
            print('Compiling ' + file)
            grading.compile(cl_stdout, file)

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
                compare(ref_stdout_file, stdout_file, result_file, reference_cpp_file)
            # count the number of warnings and errors
            count_warnings_errors(cl_stdout_file, result_file)

        # Open the student programs and outputs for final grading
        grade(file, stdout_file, result_file, grade_file, ref_stdout_file)
        # Check that a final grade for the assignment has been entered in the grade file
        if not check_grading(grade_file):
            print("Error! No grade assigned for " + file)

        # Build the final score file
        graded_files = [f for f in next(os.walk(student_dir))[2]]
        build_final_score(graded_files, score_scales)
        # Upload their grade
        # upload_grade(c)


