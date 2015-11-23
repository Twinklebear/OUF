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
import atexit
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask

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
ref_homework_dir = os.path.abspath('../reference/' + homework_dir_name)
# Collect list of all program files we're expecting to find
reference_soln = None
with open(ref_homework_dir + "/" + homework_dir_name + ".json", "r") as ref:
    reference_soln = json.load(ref)

c = canvas.canvas()
courses = c.getCourses()
course_id = c.findCourseId(courses, 'CS 6962-001 Fall 2015 Programming for Engineers')
c = canvas.canvas(courseId=course_id)

# A dict of the students that have submitted so far, and the number of times
# they've submitted
student_submission_count = {}

# Check for new submissions and grade them
def grade_new_submissions():
    print("Checking for new submissions")
    students = c.downloadAssignment(courseName=course_name, assignmentName=assignment_name,
            subdirName=homework_path)
    print("Downloaded new submissions from {}".format(students))

    for student_id in students:
        student_dir = os.path.abspath(homework_path + "/" + str(student_id))
        print('Processing student ' + student_dir)
        os.chdir(student_dir)

        for name, problem in reference_soln.items():
            cl_stdout_file = name + '_cl.txt'
            stdin_file = ref_homework_dir + '/' + problem["stdin"]
            stdout_file = name + "_stdout.txt"
            ref_stdout_file = ref_homework_dir + '/' + problem["stdout"]
            result_file = name + '_results.txt'
            grade_file = name + '_grade.txt'

            # Compile the student's submission
            print('Compiling ' + name)
            grading.compile(cl_stdout_file, problem, name)

            # Run the student's submission
            exe = name + '.exe'
            print('Running ' + exe)
            grading.run_student(exe, stdin_file, stdout_file, cl_stdout_file)

            # Check the student's submision
            print('Checking ' + name)
            # Compare the student's output to our expected output
            grading.compare(ref_stdout_file, stdout_file, result_file)
            # count the number of warnings and errors
            grading.count_warnings_errors(cl_stdout_file, result_file)

            # Compile the grading document but don't assign a grade to the student
            # since the server has no idea what grade to assign
            grading.grade(problem, stdout_file, result_file, grade_file, ref_stdout_file, None)

        # Build the final score file
        print("Building final score for " + student_dir)
        graded_files = [f for f in next(os.walk(student_dir))[2]]
        grading.build_final_score(graded_files, reference_soln, None)
        # Upload their grade
        grading.upload_grade(c)
        # CD back up out of the student's directory
        os.chdir("..")
        if student_id not in student_submission_count:
            student_submission_count[student_id] = 1
        else:
            student_submission_count[student_id] += 1

    now = datetime.datetime.now()
    print("Students graded for {}".format(now))
    # If we actually graded any students send the TAs mail on canvas with the
    # list of students that were graded
    if len(students) > 0:
        c.sendMail([1319338, 1324900], "Students Graded",
                "Students that submitted by {}:\n{}".format(now, students))

# Setup the background scheduler to run the grading job
scheduler = BackgroundScheduler()

# Setup the Flask server
app = Flask("Grading Server")

@app.route("/")
def show_status():
    return "Grading Server is running, submissions so far: <pre>{}</pre>".format(
            json.dumps(student_submission_count, indent=4))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Running grading server")
        scheduler.start()
        scheduler.add_job(grade_new_submissions, "interval", minutes=15)
        atexit.register(lambda: scheduler.shutdown(wait=False))
        app.run(host="0.0.0.0", port=80)
    elif sys.argv[1] == "single":
        grade_new_submissions()

