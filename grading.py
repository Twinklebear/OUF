import os
import subprocess
import sys
import difflib
import re
import shutil
import json
import canvas
import logging

match_case_number = re.compile("[ -]Case (\d+):")
# compare the output of a student's program to the reference output, writing the results into a
# given result file. we also need the name of the reference .cpp file, since this will tell us
# whether the student has named their file correctly
def compare(reference_output, student_output, result_file):
    diff = ''
    case_failed_count = 0
    total_cases = 0
    case_failed = False

    if os.path.isfile(reference_output):
        with open(reference_output, 'r', encoding='utf8') as ref_out, \
             open(student_output, 'r', encoding='utf8', errors='replace') as student_out:
                reference = [l.strip() + "\n" for l in ref_out.readlines() if l.strip()]
                student = [l.strip() + "\n" for l in student_out.readlines() if l.strip()]
                for line in reference:
                    total_cases += line.count('Case')
                for line in difflib.unified_diff(reference, student, fromfile='reference', tofile='student'):
                    case_match = match_case_number.match(line)
                    if case_match:
                        case_number = int(case_match.group(1))
                        case_failed = False
                    if not case_failed and ((line.startswith('-') and \
                        not line.startswith('---')) or (line.startswith('+') and \
                        not line.startswith('+++'))):
                           case_failed_count += 1
                           case_failed = True
                    diff += line
    # student program produces no outputs (NOTE: this output
    # file is there even if the student program didn't run,
    # so we need to check for the size)
    elif not os.path.getsize(student_output):
        case_failed_count = 1
     # this problem has no reference outputs, and no check
    # program, so we need to check manually
    elif not os.path.isfile(reference_output):
        case_failed_count = 0

    with open(result_file, 'w', encoding='utf8', errors='replace') as result_out:
        result_out.write(diff)
        result_out.write('\nCases Failed: ' + str(case_failed_count) + '\n')
        result_out.write('Total Cases: ' + str(total_cases) + '\n')

match_warning = re.compile('.* warning C\d+:')
match_error = re.compile('.* error C\d+:')
match_link_error = re.compile('.* LNK\d+:')
match_runtime_error = re.compile('^Process Status:.*')
# count the number of compiler warnings and errors in the input file, and write the results to the
# output file
def count_warnings_errors(input_file, output_file):
    warnings = []
    errors = []
    link_errors = []
    runtime_error_msg = "Process ran successfully"
    with open(input_file, 'r') as f:
        content = f.readlines()
        for line in content:
            warning = match_warning.match(line)
            if warning:
                warnings.append(line)
            error = match_error.match(line)
            if error:
                errors.append(line)
            link_error = match_link_error.match(line)
            if link_error:
                link_errors.append(line)
            runtime_error = match_runtime_error.match(line)
            if runtime_error:
                runtime_error_msg = line
    with open(output_file, 'a') as f:
        f.write('\n')
        f.write('Warnings: ' + str(len(warnings)) + '\n')
        f.write(''.join(warnings) + '\n')
        f.write('Compilation Errors: ' + str(len(errors)) + '\n')
        f.write(''.join(errors) + '\n')
        f.write('Linker Errors: ' + str(len(link_errors)) + '\n')
        f.write(''.join(link_errors) + '\n')
        f.write('Runtime Results:\n' + runtime_error_msg + '\n')

match_score = re.compile("Grade: (\d+\.*\d*)")
# Open files for final grading
def grade(problem, stdout_file, result_file, grade_file, ref_stdout_file, editor):
    # Copy autograde summary (diff, warnings, failed case report) to the
    # final grade file
    if os.path.isfile(result_file):
        grade_contents = ""
        start_copy = False
        if check_grading(grade_file):
            with open(grade_file, "r") as in_file:
                for line in in_file:
                    if start_copy:
                        grade_contents = grade_contents + line
                    if line.startswith("Errors:"):
                        start_copy = True
        shutil.copyfile(result_file, grade_file)
        with open(grade_file, "a") as out_file:
            out_file.write(grade_contents)
    if editor:
        editor_action = [editor] + problem["files"]
        editor_action.append(stdout_file)
        if os.path.isfile(ref_stdout_file):
            editor_action.append(ref_stdout_file)
        editor_action.append(grade_file)
        subprocess.call(editor_action)

# Check that a score was correctly assigned to the problem
def check_grading(grade_file):
    if not os.path.isfile(grade_file):
        return False
    grade_content = open(grade_file, 'r', encoding='utf8', errors='replace').readlines()
    return not (match_score.match(grade_content[-1]) is None)

def build_final_score(student_files, problems, editor):
    grade_files = [f for f in student_files if f.endswith("_grade.txt")]
    if len(grade_files) == 0:
        print('Error! Can\'t compute final grade for an ungraded student {}!'
                .format(os.getcwd()))
        return

    grade_info = ['Total Score']
    grade_total = 0
    was_graded = False
    for f in grade_files:
        with open(f, 'r', encoding='utf8', errors='replace') as fg:
            grade_info.append('####### ' + f[:-10] + ' ########\n')
            lines = fg.readlines()
            # Find the grade for this assignment and add it to the total
            assignment_score = match_score.match(lines[-1])
            if assignment_score:
                grade_total += float(assignment_score.group(1)) * problems[f[:-10]]["points"] / 10
                was_graded = True
            grade_info += lines
            grade_info.append('################################\n\n')
    if not was_graded:
        grade_total = -1
    grade_info[0] = 'Total Score: ' + str(grade_total) + '\n\n'
    grade_comment = ''.join(grade_info)
    with open('final_score.diff', 'w', encoding='utf8', errors='replace') as f:
        f.write(grade_comment)
    if editor:
        subprocess.call([editor, 'final_score.diff'])

# Compile all the *_grade.txt files for a student into a single one and
# compute the overall score. Then submit the grade for the assignment
# and post the compile grade files as a comment on it
def upload_grade(canvas):
    try:
        fg = open('final_score.diff', 'r', encoding='utf8', errors='replace')
    except:
        print("Warning: No final score diff file found, creating a default error report")
        with open('final_score.diff', 'w') as fg:
            fg.write("No files were found for your assignment. Are they the right files and named properly?\n")

    logging.basicConfig(filename="D:/Classes/Programming for Engineers/autograder/error.log", level=logging.DEBUG)
    log = logging.getLogger("ex")
    try:
        with open('AUTOGRADE.json', 'r') as f, \
            open('final_score.diff', 'r', encoding='utf8', errors='replace') as fg:
                grade_comment = fg.readlines()
                grade_match = re.match('Total Score: (-?\d+\.*\d*)', grade_comment[0])
                grade_total = -1
                if not grade_match:
                    print('Error grading {}, no total score assigned'.format(os.getcwd()))
                else:
                    grade_total = float(grade_match.group(1))
                student = json.load(f)
                canvas.gradeAndCommentSubmissionFile(None, student['canvasSubmission']['assignment_id'],
                        student['canvasStudent']['id'], grade_total, 'final_score.diff')
    except Exception as err:
        log.exception(err)
        print('Cannot upload score for student without AUTOGRADE.json')

# Compute the student's total score from their grade files
def compute_total_score(student_files, problems):
    grade_files = [f for f in student_files if f.endswith("_grade.txt")]
    if len(grade_files) == 0:
        print('Error! Can\'t get grade stats for an ungraded student! Giving a 0 for now')
        return 0

    grade_total = 0
    for f in grade_files:
        with open(f, 'r', encoding='utf8', errors='replace') as fg:
            lines = fg.readlines()
            # Find the grade for this assignment and add it to the total
            assignment_score = match_score.match(lines[-1])
            if assignment_score:
                grade_total = grade_total + float(assignment_score.group(1)) * problems[f[:-10]]["points"] / 10.0
    return grade_total

# Compile the student's submission and record compilation errors
# Will abort if cl.exe is not available
def compile(cl_stdout_file, problem, name):
    with open(cl_stdout_file, 'w') as cl_stdout:
        try:
            subprocess.Popen(['cl.exe', '/W4', '/EHsc', '/Fe' + name] + problem["files"],
                    stdout=cl_stdout, universal_newlines=True).wait()
        except:
            print("Fatal Error! cl.exe is not available, did you setup your environment?")
            sys.exit(1)

# Run the student's program and save the output
def run_student(exe, stdin_file, stdout_file, cl_stdout_file):
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
                with open(cl_stdout_file, "a") as f:
                    f.write("\nProcess Status: Other Exception\n")
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
                with open(cl_stdout_file, "a") as f:
                    f.write("\nProcess Status: Other Exception\n")

