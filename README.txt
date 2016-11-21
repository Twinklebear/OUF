Requirements:
Python 3 or above
Visual Studio 2015
Vim or Notepad++

I. Setup

0. Put a .canvas-token file in C:/Users/<username>. The contents of this file
can be obtained from the Canvas website. It should look likes the following

self.CANVAS_API="https://utah.instructure.com/api/v1/"
self.CANVAS_TOKEN="2~FQzLuKLzmLJvy77LFafaaUcUxPw0PdfwpLvP6c3qLK2mgvkHMBaPZPF3uS3Rrmje"

II. How to download homework submissions and grade them

0. Create a directory named <homework> in ./reference, where <homework> is the
name of the current assignment, for example "homework3".

In this directory, create a file <homework>.json, with contents that look like
the following

{
    "ND_Box": {
        "points": 50,
        "files": ["ndbox.cpp"],
        "stdin": "ndbox_stdin.txt",
        "stdout": "ndbox_stdout.txt"
    },
    "GATTACA": {
        "points": 50,
        "files": ["gattaca.cpp"],
        "stdin": "gattaca_stdin.txt",
        "stdout": "gattaca_stdout.txt"
    }
}

Make sure the reference input and output files for all problems as specified in
the json file are present in ./reference/<homework>.

1. Put a autograde-config.json file in ./submissions. The contents of this file
look like the following

{
    "courseName":"ME EN 6250-001 Fall 2016 Programming for Engin",
    "assignmentName":"Homework 3",
    "subdirName":"homework3",
    "domainName":"https://utah.instructure.com",
    "emailSubject":"Homework 1: autograde results",
    "emailFrom":"user",
    "emailFromName":"Jane Doe",
    "emailPassword":"password",
    "emailSmtp":"smtp.gmail.com",
    "emailSmtpPort":"587"
}

Change assignmentName and subdirName to refer to the current homework assignment,
for example "homework3".

2. Download the submissions, run, and check them against the reference outputs
./set_cl_env.bat
./submissions/python ../ag.py download
./python test_cl.py <homework> compile
./python test_cl.py <homework> run
./python test_cl.py <homework> check

3. Grade the submissions
./python test_cl.py <homework> grade

4. Upload the scores
./python test_cl.py <homework> upload