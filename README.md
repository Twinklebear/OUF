OUF - Optional Useless Feedback
==========

This collection of scripts implements an feedback system for MSVC that can be used to
grade programming assignments written in C++. It also includes scripts to interact with Canvas.

Getting started
==============

* This code requires MSVC.
* If you are using Canvas, create a file named ".canvas-token" in your home directory that contains:

```
self.CANVAS_API="https://canvas.instructure.com/api/v1/"
self.CANVAS_TOKEN="token-generated-in-canvas"
```

The first line should be the URL for the Canvas API. For Michigan Tech, for example, this URL should be "https://mtu.instructure.com/api/v1". The second line should contain a token that you must generate in Canvas and will be a string of characters and numbers. To generate one, login to Canvas, go to "Settings" and click on the "New Access Token" button.

* Next, make a file named "autograde-config.json" in the folder where you want to accept submissions that contains the following:

```
{                                                 // REMOVE THESE COMMENTS!
    "courseName":"CS4461 Networks - Spring 2015", // name of course on Canvas
    "assignmentName":"HW5: HTTP server",          // name of assignment on Canvas
    "subdirName":"autograder",                    // subdirectory to place submissions in
    "domainName":"mtu.edu",                       // domain name to use for email messages
    "emailSubject":"HW5: autograde results",      // subject line to use for email messages
    "emailFrom":"user",                           // email address of sender
    "emailFromName":"Jane Doe",                   // name of sender
    "emailPassword":"password",                   // email password for sender
    "emailSmtp":"smtp.gmail.com",                 // smtp server
    "emailSmtpPort":"587"                         // smtp port
}
```


