# How to Grade
For each compiler warning, deduct one point. Any errors will result in the program
failing to compile and will result in no points for the problem.

## Downloading Assignments
To download the assignments follow the instructions for the original repo in the README.

## Compiling
This part **must** be run from the old Windows Command Prompt. Run `cl_grader.bat <homework dir> compile`,
it will set up the MSVC environment and use `cl.exe` to compile the student's code.

The reference submissions should also be built at this point and can be run with their output
piped to a file. Note that this file should be ASCII encoded, if running in the command prompt
then `./exe > out.txt` should work but in powershell you must use:

```powershell
./exe | out-file out.txt -encoding ascii
```

since powershell defaults to UTF-16.

## Running
To run the student's programs on the test cases use `test_cl.py <homework dir> run`. The input for
each problem will be pulled from `problem_name_stdin.txt`, stdout from the student's program
will be written to `problem_name_stdout.txt` in their folder.

## Checking
To check student's output run `test_cl.py <homework dir> check`, this will diff their output
against the expected output and track how many test cases they failed. Additionally any
compile warnings and errors will be placed in the file `problem_name_results.txt` in
the student's directory.

## Grading
To grade the student's programs run `test_cl.py <homework dir> grade`. Notepad++ or gVim
is required for this part. For each problem the student's code, stdout, results and
reference stdout file (if one exists) will be opened. Another file to output the grade,
`problem_name_grade.txt` will be opened containing the content of the results file.
You should add a line at the end of this file containing the score for the problem,
written as `Grade: XX`.

## Uploading
The upload process takes all the grade files from the grading step, parses the total score
and uploads it to canvas. The contents of the grade files are uploaded as a text comment
so the student can view where they differed along with any warnings and errors.

## Directory Structure
A reference of what the structure of the grading folders looks like is shown below

```
autograder\
    ag.py
    ag-grade.py
    autograder.py
    canvas.py
    cl_grader.bat /* use to compile student's submission */
    test_cl.py /* grade student's programs, run, check, upload scores */
    submissions\
        homework1\ /* we need one sub-directory for each homework */
            compound_interest.cpp /* this is the reference solution */
            compound_interest.exe
            compound_interest_stdin.txt /* this is the standard input */
            compound_interest_stdout.txt /* this is the standard output */
            frame_a_name.cpp
            frame_a_name.exe
            /* if the input is missing, just run the program without input */
            /* if the output is missing, this problem requires manually grading */
            frame_a_name_check.exe /* if this file exists, the problem requires special checking (ie. not simple comparison of output files) */
            preventing_overflow.cpp
            preventing_overflow.exe
            XXXXX\ /* student id */
                AUTOGRADE.json
                compound_interest.cpp
                compound_interest.exe
                compound_interest_stdin.txt
                compound_interest_stdout.txt
                compound_interest_cl.txt /* compiler output */
                compound_interest_results.txt /* which test failed/passed */
                compound_interest_grade.txt /* grade and comments */
                frame_a_name.cpp
                frame_a_name.exe
                frame_a_name_cl.txt
                preventing_overflow.cpp
                preventing_overflow.exe
                preventing_overflow_cl.txt
```

