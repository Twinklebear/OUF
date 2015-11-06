#!/usr/bin/env python3
# Author: Scott Kuhl
import json
import os
import urllib.request
import urllib.parse
import textwrap
import sys,shutil,os,time,hashlib,re
from pprint import pprint
import argparse
import requests

# To use this Python class, you should create a file named
# .canvas-token in your home directory. It should contain the lines:
#
# self.CANVAS_API="https://canvas.instructure.com/api/v1/"
# self.CANVAS_TOKEN="token-generated-in-canvas"
#
# The first line should be the URL for the Canvas API. For Michigan
# Tech, for example, this URL should be
# "https://mtu.instructure.com/api/v1". The second line should contain
# a token that you must generate in Canvas and will be a string of
# characters and numbers. To generate one, login to Canvas, go to
# "Settings" and click on the "New Access Token" button.


# The canvas object will remember the courseId you use in the
# constructor and use that if you don't provide a courseId to the
# other functions that you call. Or, you can manually override the
# courseId in your calls to specific functions.


class canvas():
    CANVAS_API = ""
    CANVAS_TOKEN = None
    courseId = 0;

    def __init__(self, token=None, courseId=None):
        canvasTokenFile = os.path.expanduser("~/.canvas-token")
        if token:
            self.CANVAS_TOKEN = str(token)
        else:
            with open(canvasTokenFile) as f:
                exec(f.read())

        if not self.CANVAS_TOKEN:
            print("Canvas token not found.")
            exit()
        if not self.CANVAS_API:
            print("URL for Canvas API not found.")
            exit()
        self.courseId = courseId

    def makeRequest(self,url):
        """Makes the given request (passes token as header)"""
        try:
            # Tack on http://.../ to the beginning of the url if needed
            if self.CANVAS_API not in url:
                urlString = self.CANVAS_API+url
            else:
                urlString = url
        
            print("Getting: " +urlString)
            request = urllib.request.Request(urlString)
            request.add_header("Authorization", "Bearer " + self.CANVAS_TOKEN)
            response = urllib.request.urlopen(request)
            json_string = response.read().decode('utf-8');
            retVal = json.loads(json_string)

            # Deal with pagination:
            # https://canvas.instructure.com/doc/api/file.pagination.html
            #
            # Load the next page if needed and tack the results onto
            # the end.
            response_headers = dict(response.info())
            if "Link" not in response_headers:
                return retVal
            link_header = response_headers['Link']
            link_header_split = link_header.split(",")
            for s in link_header_split:
                match = re.match('<(.*)>; rel="next"', s)
                if not match:
                    continue
                else:
                    retVal.extend(self.makeRequest(match.group(1)))

            return retVal
        except:
            e = sys.exc_info()[0]
            print(e)
            raise

    def makePut(self,url):
        """Puts data to Canvas (passes token as header)"""
        try:
            # Tack on http://.../ to the beginning of the url if needed
            if self.CANVAS_API not in url:
                urlString = self.CANVAS_API+url
            else:
                urlString = url
        
            print("Putting: " +urlString)
            request = urllib.request.Request(urlString, method='PUT')
            request.add_header("Authorization", "Bearer " + self.CANVAS_TOKEN)
            response = urllib.request.urlopen(request)
            #print(response.readall().decode('utf-8'))
            # json_string = response.readall().decode('utf-8');
            # retVal = json.loads(json_string)
            if(response.status == 200):
                return True
            else:
                return False
        except:
            e = sys.exc_info()[0]
            print(e)
            raise

    def makePost(self, url, params):
        """Post data to Canvas, returns the response"""
        try:
            # Tack on http://.../ to the beginning of the url if needed
            if self.CANVAS_API not in url:
                urlString = self.CANVAS_API+url
            else:
                urlString = url
        
            print("Posting: " + urlString)
            data = urllib.parse.urlencode(params).encode("utf-8")
            request = urllib.request.Request(urlString, data)
            request.add_header("Authorization", "Bearer " + self.CANVAS_TOKEN)
            response = urllib.request.urlopen(request)
            json_string = response.read().decode('utf-8')
            return json.loads(json_string)
        except:
            e = sys.exc_info()[0]
            print(e)
            raise

    def postFile(self, url, params, commentFile):
        """Post file to an external service, like the external Canvas file host"""
        try:
            print("Posting: " + url)
            request = requests.post(url, data=params, files={"file": commentFile})
        except:
            e = sys.exc_info()[0]
            print(e)
            raise


    def prettyPrint(self,data):
        print(json.dumps(data, sort_keys=True, indent=4))

    def getCourses(self):
        """Gets course objects"""
        allCourses = self.makeRequest("courses?"+
                                      urllib.parse.urlencode({"per_page":"100",
                                                              "page": "1"}))
        return allCourses

    def getStudents(self, courseId=None):
        """Gets list of students in a course."""
        courseId = courseId or self.courseId
        if courseId == None:
            print("Can't getStudents without a courseId.")
            exit()
        students = self.makeRequest("courses/"+str(courseId)+"/students?"+
                                     urllib.parse.urlencode({"per_page":"100",
                                                             "page": "1"}))
        # Filter out students who are still "pending".
        # These "pending" students do not have a id, which some of this code relies on
        nonPendingStudents = []
        for s in students:
            if 'id' in s:
                nonPendingStudents.append(s)
        return nonPendingStudents

    def getAssignments(self, courseId=None):
        """Gets list of assignments in a course."""
        courseId = courseId or self.courseId
        allAssignments = self.makeRequest("courses/"+str(courseId)+"/assignments?"+
                                          urllib.parse.urlencode({"per_page":"100",
                                                                  "page": "1"}))
        return allAssignments

    def uploadSubmissionCommentFile(self, courseId, assignmentId, studentId, commentFile):
        courseId = courseId or self.courseId
        if courseId == None:
            print("Can't comment on submissions without a courseId.")
            exit(1)
        if assignmentId == None or studentId == None:
            printf("Can't comment on a submission without a assignment ID and a student ID.")
            exit(1)

        fileSize = os.path.getsize(commentFile)
        params = { "name": commentFile,
                "size": fileSize,
                "content_type": "text/plain",
                "parent_folder_path": "homework_comments" }

        # See Canvas API Doc on file uploading to find out why this is such a mess
        # File Uploads: https://canvas.instructure.com/doc/api/file.file_uploads.html
        # Submission Comment Files: https://canvas.instructure.com/doc/api/submission_comments.html
        # Step 1: Tell Canvas we're going to upload a file and have it tell us where to actually upload it
        response = self.makePost("courses/" + str(courseId) + "/assignments/" + str(assignmentId) +
                "/submissions/" + str(studentId) + "/comments/files", params)
        # Step 2: Using the information from step 1 about where to send the file and auth info to do so,
        # actually upload the file
        with open(commentFile, 'rb') as f:
            self.postFile(response["upload_url"], response["upload_params"], f)
            # If we uploaded successfully this will tell us the actual file ID we can reference when making the
            # comment on the student's submission
            success = self.makePost(response["upload_params"]["success_action_redirect"], {"Content-Length": 0})

        # Now comment on the student's submission to attach the file
        self.makePut("courses/" + str(courseId) +
                "/assignments/" + str(assignmentId) +
                "/submissions/" + str(studentId) + "?" +
                urllib.parse.urlencode({"comment[file_ids][]" : success["id"],
                    "comment[text_comment]": "Please see the attached file for your grading summary"}))


    def commentOnSubmission(self, courseId, assignmentId, studentId, comment):
        courseId = courseId or self.courseId
        if courseId == None:
            print("Can't get comment on submissions without a courseId.")
            exit(1)
        if assignmentId == None or studentId == None:
            printf("Can't comment on a submission without a assignment ID and a student ID.")
            exit(1)

        self.makePut("courses/"+str(courseId)+
                     "/assignments/"+str(assignmentId)+
                     "/submissions/"+str(studentId)+"?"+
                     urllib.parse.urlencode({"comment[text_comment]" : comment}))

    # Upload the score for a student's submission and comment on it with our grading summary file
    def gradeAndCommentSubmission(self, courseId, assignmentId, studentId, points, comment):
        courseId = courseId or self.courseId
        if courseId == None:
            print("Can't comment on submissions without a courseId.")
            exit(1)
        if assignmentId == None or studentId == None:
            printf("Can't comment on a submission without a assignment ID and a student ID.")
            exit(1)
        
        self.makePut("courses/"+str(courseId)+
                     "/assignments/"+str(assignmentId)+
                     "/submissions/"+str(studentId)+"?"+
                     urllib.parse.urlencode({"submission[posted_grade]": str(points),
                         "comment[text_comment]": comment}))
    
    # Upload the score for a student's submission and comment on it with our grading summary file
    def gradeAndCommentSubmissionFile(self, courseId, assignmentId, studentId, points, commentFile):
        courseId = courseId or self.courseId
        if courseId == None:
            print("Can't comment on submissions without a courseId.")
            exit(1)
        if assignmentId == None or studentId == None:
            printf("Can't comment on a submission without a assignment ID and a student ID.")
            exit(1)
        
        # Post the student's score if the assignment was graded. We have a negative grade
        # when running from the grading server since it doesn't score students
        if points >= 0:
            self.makePut("courses/" + str(courseId) +
                    "/assignments/" + str(assignmentId) +
                    "/submissions/" + str(studentId) + "?" +
                    urllib.parse.urlencode({"submission[posted_grade]": str(points)}))
        # Upload the score summary file
        self.uploadSubmissionCommentFile(courseId, assignmentId, studentId, commentFile)

    def getSubmissions(self, courseId=None, assignmentId=None, studentId=None):
        """Gets all submissions for a course, all submissions for a student in a course, or all submissions for a specific assignment+student combination."""
        courseId = courseId or self.courseId
        if courseId == None:
            print("Can't get submissions without a courseId.")
            exit()
        commonargs="grouped=true&include[]=submission_history"
        if studentId == None:
            commonargs+="&student_ids[]=all"
        else:
            commonargs+="&student_ids[]="+str(studentId)
        commonargs+="&"
        commonargs+=urllib.parse.urlencode({"per_page":"100",
                                            "page": "1"})


        if assignmentId == None:
            return self.makeRequest("courses/"+str(courseId)+"/students/submissions?"+commonargs)
        else:
            return self.makeRequest("courses/"+str(courseId)+"/students/submissions?assignment_ids[]="+str(assignmentId)+"&"+commonargs)

    
    def findStudent(self, students, searchString):
        """Returns a student object that matches the students name, username, or ID. The searchString must match one of the fields in the student object exactly!"""
        searchString = str(searchString).lower()
        #print("Looking for student " + searchString)
        #self.prettyPrint(students)
        #exit(1)
        for s in students:
            if s['name'].lower()          == searchString or \
               s['short_name'].lower()    == searchString or \
               s['sortable_name'].lower() == searchString or \
               s['id']                    == int(searchString):
                return s

        # print("Failed to find student: " + searchString)
        return None

    def findAssignment(self, assignments, searchString):
        """Returns an assignment object that matches the assignment name out of a list of assignment objects."""
        searchString = searchString.lower()
        for a in assignments:
            if a['name'].lower() == searchString or \
               str(a['id']) == searchString:
                return a
        return None

    def findCourse(self, courses, searchString):
        """Returns an course object that matches the course name out of a list of course objects."""
        searchString = searchString.lower()
        for c in courses:
            if c['name'].lower() == searchString or \
               str(c['id'])      == searchString:
                return c
        return None

    def findStudentId(self, students, searchString):
        """Returns the ID of the student by looking for a match in the list of students."""
        if type(searchString) == int: # assume that this is a correct id they are looking for
            return searchString
        student = self.findStudent(students, searchString)
        if student:
            return int(student['id'])
        return None

    def findAssignmentId(self, assignments, searchString):
        """Returns the ID of the assignment by looking for a match in the list of assignments."""
        if type(searchString) == int: # assume that this is a correct id they are looking for
            return searchString
        assignment = self.findAssignment(assignments, searchString)
        if assignment:
            return int(assignment['id'])
        return None

    def findCourseId(self, courses, searchString):
        """Returns the ID of the course by looking through a list of courses."""
        if type(searchString) == int: # assume that this is a correct id they are looking for
            return searchString
        course = self.findCourse(courses, searchString)
        if course:
            return int(course['id'])
        return None

    def isSubmissionLate(self, submission):
        #if submission['late']:
        #    return True
        #else:
            return False

    def isSubmissionNewest(self, submission, submission_history):
        for s in submission_history:
            if s['attempt'] > submission['attempt']:
                return False
        return True

    def isSubmissionNewestNonLate(self, submission, submission_history):
        #if submission['late']:
        #    return False
        return True

        # Look for a non-late submission in the history with a greater
        # attempt number.
        for s in submission_history:
            #if s['late']:
            #    continue
            if s['attempt'] > submission['attempt']:
                return False
        return True
    
    def findSubmissionsToGrade(self, submissions, attempt=-1):
        """Returns newest non-late submissions. If attempt is set, only return the submissions with that attempt number."""
        goodSubmissions = []

        # submissions must be grouped by student and include submission history

        # For each student, get the student submission history.
        for studentSubmit in submissions:
            # self.prettyPrint(studentSubmit)
            allHistory = []
            if len(studentSubmit['submissions']) > 0:
                allHistory = studentSubmit['submissions'][0]['submission_history']

            toGrade = None
            for hist in allHistory:
                # hist['attempt'] is set to null if we have already
                # graded something that hasn't been submitted.
                if not hist['attempt']:
                    continue
                if attempt <= 0:
                    if self.isSubmissionNewestNonLate(hist, allHistory):
                        toGrade = hist
                else:
                    if attempt == hist['attempt']:
                        toGrade = hist

            # Add the submission for this student that we want to
            # grade to the list.
            if toGrade:
                goodSubmissions.append(toGrade)

        if len(goodSubmissions) == 0:
            print("WARNING: Unable to find any matching submissions.")
        return goodSubmissions


    def printSubmissionSummary(self, submissions, students):
        """Prints a summary of all of the submissions."""
        fmtStr = "%4s %5s %4s %12s %s"
        print(fmtStr%("pts", "late", "atmpt", "login", "name"))
        for student in students:
            studentSubmissionHist = []
            for submission in submissions:
                if submission['user_id'] == student['id']:
                    if 'submissions' in submission:
                        if len(submission['submissions']) > 0:
                            # Assuming submissions is what canvas.getSubmissions() returns
                            studentSubmissionHist = submission['submissions'][0]['submission_history']
                    else: # Assuming submissions is what canvas.findSubmissionsToGrade() returns
                        studentSubmissionHist = [ submission ]

#            if 'id' not in student or 'name' not in student:
#                print("ERROR processing student: ")
#                self.prettyPrint(student)
#                return
                        
            if len(studentSubmissionHist) == 0:
                print(fmtStr%("", " none", 0, str(student['id']), student['name']))
            for hist in studentSubmissionHist:
                late = ""
                graded = ""
                if hist['late']:
                    late = " late"
                if hist['grade']:
                    graded = str(hist['grade'])
                print(fmtStr%(graded, late, str(hist['attempt']), str(student['id']), student['name']))


    @classmethod
    def prettyDate(obj, d, now):
        import datetime
        diff = now - d
        s = diff.seconds
        if diff.days > 7 or diff.days < 0:
            local = d.astimezone(None)
            return local.strftime('%Y-%m-%d')
        elif diff.days == 1:
            return ' 1 day ago'
        elif diff.days > 1:
            return '{:2d} days ago'.format(int(diff.days))
        elif s <= 1:
            return 'just now'
        elif s < 60:
            return '{:2d} seconds ago'.format(int(s))
        elif s < 120:
            return ' 1 minute ago'
        elif s < 3600:
            return '{:2d} minutes ago'.format(int(s/60))
        elif s < 7200:
            return ' 1 hour ago'
        else:
            return '{:2d} hours ago'.format(int(s/3600))

    def downloadSubmission(self, submission, student, directory, group_memberships={}):
        """Downloads a specific submission from a student into a directory."""

        attachment = submission['attachments'][0]
        filename = attachment['filename']
        exten = os.path.splitext(filename)[1] # get filename extension
        import datetime
        utc_dt = datetime.datetime.strptime(submission['submitted_at'], '%Y-%m-%dT%H:%M:%SZ')
        utc_dt = utc_dt.replace(tzinfo=datetime.timezone.utc)

        # Create a new metadata record to save
        metadataNew = {
            "canvasSubmission":submission,
            "canvasStudent":student }

        # Figure out if the name of the downloaded file/subdirectory
        # should be based on their username or group name (if there is
        # a set of groups associated with this assignment.)
        login = student['id']
        if student['id'] in group_memberships:
            (group, usersInGroup) = group_memberships[student['id']]
            metadataNew['canvasGroup'] = group
            metadataNew['canvasStudentsInGroup'] = usersInGroup
            login = group['name']

        # Look for an existing metadata file
        metadataFile = None;
        metadataFiles = [ os.path.join(directory, str(login) + ".AUTOGRADE.json"),
                          os.path.join(directory, str(login),"AUTOGRADE.json") ]
        for mdf in metadataFiles:
            if os.path.exists(mdf):
                metadataFile = mdf

        # Check if we need to download file based on metadata
        metadataCache = {}
        if metadataFile:
            with open(metadataFile,"r") as f:
                metadataCache = json.load(f)

        # Gather metadata and make assumptions if metadata file is missing:
        if "locked" not in metadataCache:
            print("%-12s Assuming cached copy is unlocked." % login)
        locked = metadataCache.get("locked", 0)

        if 'canvasSubmission' not in metadataCache or \
           'attempt' not in metadataCache['canvasSubmission']:
            print("%-12s Assuming cached submission is attempt 0" % login)
            cachedAttempt = 0
        else:
            cachedAttempt = metadataCache['canvasSubmission']['attempt']
        newAttempt = metadataNew['canvasSubmission']['attempt']

        # Determine if we should download the submission or not
        if locked:
            print("%-12s skipping download because submission is locked." % login)
            return False
        if newAttempt <= cachedAttempt:
            print("%-12s is up to date" % login)
            return False

        archiveFile  = os.path.join(directory,str(login) + exten)

        # Delete existing archive if it exists.
        toDelete = metadataFiles
        toDelete.append(archiveFile)
        for f in toDelete:
            if os.path.exists(archiveFile):
                os.unlink(archiveFile)
        # Download the file
        print("%-12s downloading attempt %d submitted %s" % (login, newAttempt, 
              self.prettyDate(utc_dt, datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc))))
        try:
            urllib.request.urlretrieve(attachment['url'], directory+"/" + str(login) + exten)
        except:
            print("ERROR: Failed to download "+attachment['url'])
            import traceback
            traceback.print_exc()
            pass

        # Write the new metadata out to a file
        metadataNew['locked']=0
        with open(metadataFiles[0], "w") as f:
            metadata_string = json.dump(metadataNew, f, indent=4)
        return True
        
        

    def downloadSubmissions(self, submissions, students, dir=None, group_memberships={}):
        """Downloads submissions each of the students. Assumes that students submit one file
           (tgz.gz, zip, whatever is allowed). Files will be downloaded into the given subdirectory.
           Returns the list of student IDs that submissions were downloaded for
        """
        if not dir:
            dir = "."
        if not os.path.exists(dir):
            os.makedirs(dir)
        students_downloaded = []
        # require one attachment
        for i in submissions:
            if i != None and 'attachments' in i and len(i['attachments']) == 1 and \
               i['attachments'][0]['url'] and \
               i['attachments'][0]['filename']:
                student = self.findStudent(students, i['user_id'])
                if student:
                    if self.downloadSubmission(i, student, dir, group_memberships):
                        students_downloaded.append(student["id"])
        return students_downloaded


    def get_immediate_files(self, dir):
        """Returns an alphabetical list of all files in the current directory (non-recursive)."""
        onlyfiles = [ f for f in os.listdir(dir) if os.path.isfile(os.path.join(dir,f)) ]
        onlyfiles.sort()
        return onlyfiles

    def extractAllFiles(self, dir=".", newSubdir=False):
        print("Extracting all files into: " + dir)
        files = self.get_immediate_files(dir)
        for f in files:
            if not f.endswith(".AUTOGRADE.json"):
                self.extractFile(dir+"/"+f, dir, newSubdir)

    def extractFile(self, filename, dir, newSubdir=False):
        """Extracts filename into dir. If newSubdir is set, create an additional subdirectory inside of dir to extract the files into."""
        import tarfile,zipfile
        destDir = dir
        if newSubdir:
            # If using newSubdir, make a directory with the same
            # name as the file but without the extension.
            destDir = os.path.splitext(filename)[0]

        # Calculate md5sum
        md5sum = ""
        with open(filename, 'rb') as fh:
            m = hashlib.md5()
            while True:
                data = fh.read(8192)
                if not data:
                    break
                m.update(data)
            md5sum = m.hexdigest()


        # TODO: I think this is where we crash. Is it becauase the program
        # crashed dialog stays open?
        if os.path.exists(destDir):
            shutil.rmtree(destDir)
        try:
            # tarfile.is_tarfile() and zipfile.is_zipfile() functions
            # are available, but sometimes it misidentifies files (for
            # example .docx files are zip files.
            if filename.endswith(".tar") or \
               filename.endswith(".tar.gz") or  \
               filename.endswith(".tgz") or \
               filename.endswith(".tar.bz2") or \
               filename.endswith(".tbz") or \
               filename.endswith(".tbz2") or \
               filename.endswith(".tb2"):
                tar = tarfile.open(filename)
                tar.extractall(path=destDir)
                tar.close()
                os.remove(filename)
                print(destDir + ": Extracted " + filename + " into " + destDir);
            elif filename.endswith(".zip"):
                z = zipfile.ZipFile(filename)
                z.extractall(path=destDir)
                z.close()
                os.remove(filename)
                print(destDir + ": Extracted " + filename + " into " + destDir);
            else:
                # Comment out the following lines to prevent single
                # file submissions from getting put into
                # subdirectories. Removing this line may break a
                # variety of different elements of the autograder.
                os.mkdir(destDir)
                shutil.move(filename, destDir)
                print(destDir + ": No need to extract " + filename);
        except:
            print(destDir + ": Failed to extract file: "+filename)

        # Get a copy of the metadata for this file
        metadataFile = destDir+".AUTOGRADE.json"
        metadata = {}
        if os.path.exists(metadataFile):
            with open(metadataFile, "r") as f:
                metadata = json.load(f)
        # add md5sum to metadata
        metadata['md5sum']=md5sum
        
        # If subdirectory wasn't created, overwrite existing metadata file
        if not os.path.exists(destDir):
            with open(metadataFile, "w") as f:
                json.dump(metadata, f, indent=4)
        else: # If we did extract files into a subdirectory
            # Remove unnecessary subdirectories
            onlyfiles = [ f for f in os.listdir(destDir) if os.path.isfile(os.path.join(destDir,f)) ]
            onlydirs = [ f for f in os.listdir(destDir) if os.path.isdir(os.path.join(destDir,f)) ]
            print(destDir + ": Contains %d file(s) and %d dir(s)"%(len(onlyfiles), len(onlydirs)))
            # If submission included all files in a subdirectory, remove the subdirectory
            if len(onlyfiles) == 0 and len(onlydirs) > 0:
                for subdir in onlydirs:
                    print(destDir + ": Removing unnecessary subdirectory " + subdir)
                    # Move the files in the subdirectory into the destination directory
                    for f in next(os.walk(destDir + "/" + subdir))[2]:
                        print(destDir + ": Moving up '" + f + "'")
                        shutil.move(destDir + "/" + subdir + "/" + f, destDir)
                    # Remove the directory
                    shutil.rmtree(destDir + "/" + subdir, ignore_errors=True)

            # Remove original metadata file, write one out in the
            # subdirectory.
            metadataFileDestDir = os.path.join(destDir,"AUTOGRADE.json")
            os.remove(metadataFile)
            with open(metadataFileDestDir, "w") as f:
                json.dump(metadata, f, indent=4)


    def printCourseIds(self, courses):
        for i in courses:
            print("%10s \"%s\""%(str(i['id']), i['name']))

    def printAssignmentIds(self, assignments):
        for i in assignments:
            print("%10s %s"%(str(i['id']), i['name']))
  
    def printStudentIds(self, students):
        for i in students:
            print("%10s %10s %s"%(str(i['id']), i['id'], i['name']))

    def setDefaultCourseId(self, courseId):
        if courseId == None:
            print("Warning: You are setting the default courseId to None.")
        self.courseId = courseId;

    def downloadAssignment(self, courseName, assignmentName, subdirName, userid=None, attempt=-1):
        """Download the latest submissions for the course and return the list of IDs that
           we downloaded submissions for
        """
        # Find the course
        courses = self.getCourses()
        courseId = self.findCourseId(courses, courseName)
        if courseId == None:
            print("Failed to find course " + courseName);
            exit(1)

        # Get a list of assignments
        assignments = self.getAssignments(courseId=courseId)
        
        # Get a list of the students in the course
        students = self.getStudents(courseId=courseId)
        # Filter that list down to the requested student
        if userid:
            students = [ student for student in students if userid==student['id']]
            if len(students) == 0:
                print("No matching student for userid %s" % userid)
                exit(1)

        #self.printCourseIds(courses)
        #self.printAssignmentIds(assignments)
        #self.printStudentIds(students)

        # Find the assignment in the list of assignments
        assignmentId = self.findAssignmentId(assignments, assignmentName)
        if assignmentId == None:
            self.printAssignmentIds(assignments)
            print("Failed to find assignment " + assignmentName);
            exit(1)

        # Crate a dictionary to map usernames to (group, usersInGroup)
        group_memberships = {}
        assignment = self.findAssignment(assignments, assignmentName)
        assignmentGroupCat = assignment['group_category_id']
        if assignmentGroupCat:
            assignmentGroups = self.makeRequest("group_categories/"+str(assignmentGroupCat)+"/groups")
            for g in assignmentGroups:
                usersInGroup = self.makeRequest("groups/"+str(g['id'])+"/users")
                for u in usersInGroup:
                    if 'id' in u: # Filter out pending students in a group
                        group_memberships[u['id']] = (g, usersInGroup);

        # Get the submissions for the assignment
        if userid:
            studentId = students[0]['id']
        else:
            studentId = None
        
        submissions = self.getSubmissions(courseId=courseId, assignmentId=assignmentId, studentId=studentId)

        # Filter out the submissions that we want to grade (newest, non-late submission)
        submissionsToGrade = self.findSubmissionsToGrade(submissions, attempt)

        # Download the submissions
        students_downloaded = self.downloadSubmissions(submissionsToGrade, students, subdirName, group_memberships)

        # Assuming zip, tgz, or tar.gz files are submitted, extract
        # them into subdirectories named after the student usernames.
        if subdirName:
            self.extractAllFiles(dir=subdirName,newSubdir=True)
        else:
            self.extractAllFiles()
        return students_downloaded



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Download assignments from Canvas')
    parser.add_argument('action', type=str, metavar="ACTION", nargs=1, help="assignmentStatus, assignmentDownload, studentList, assignmentList, courseList")
    parser.add_argument('-c', '--course', required=False, help="Name of course on Canvas.")
    parser.add_argument('-a', '--assignment', required=False, help="Name of assignment on Canvas.")
    args = parser.parse_args()


    canvas = canvas()
    courses = canvas.getCourses()

    for action in args.action:

        if action == "download" and not args.assignment:
            print("Assignment name required when downloading an assignment.")
            parser.print_help()
            exit(1)

        if action != "courseList" and not args.course:
            print("Course name required (unless using courseList action)")
            parser.print_help()
            exit(1)

        if action == "assignmentList":
            courseId = canvas.findCourseId(courses, args.course)
            canvas.setDefaultCourseId(courseId)

            assignments = canvas.getAssignments()
            canvas.printAssignmentIds(assignments)

        elif action == "courseList":
            canvas.printCourseIds(courses)

        elif action == "studentList":
            courseId = canvas.findCourseId(courses, args.course)
            canvas.setDefaultCourseId(courseId)

            students = canvas.getStudents()
            canvas.printStudentIds(students)

        elif action == "assignmentStatus":
            courseId = canvas.findCourseId(courses, args.course)
            canvas.setDefaultCourseId(courseId)

            assignments = canvas.getAssignments()
            students = canvas.getStudents()
            assignmentId = canvas.findAssignmentId(assignments, args.assignment)
            submissions = canvas.getSubmissions(assignmentId=assignmentId)
            canvas.printSubmissionSummary(submissions, students)
    #        submissionsToGrade = canvas.findSubmissionsToGrade(submissions)
    #        canvas.printSubmissionSummary(submissionsToGrade, students)


        elif action == "assignmentDownload":
            canvas.downloadAssignment(args.course, args.assignment, "canvas-submissions")

        else:
            print("Unknown action: " + action)
            parser.print_help()
            exit(1)
