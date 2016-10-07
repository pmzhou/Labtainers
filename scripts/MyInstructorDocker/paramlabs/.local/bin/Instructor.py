#!/usr/bin/env python

# Instructor.py
# Description: * Read instructorlab.json and extract a zip file
#                containing the student lab work
#              * Call script to grade the student lab work

import json
import os
import sys
import zipfile
import Grader
import AnswerParser
import GoalsParser
import ResultParser

UBUNTUHOME="/home/ubuntu/"

def printresult(gradesfile, LabIDStudentName, SaveDirName, grades):
    gradesfile.write("%s" % LabIDStudentName)
    #for dirname in SaveDirName:
    #    for grade in grades:
    #        if dirname in grade:
    #            gradesfile.write(grade)
    #gradesfile.write("")
    for gradestring in grades:
        gradesfile.write('%s ' % gradestring)
    gradesfile.write('\n')

# Usage: Instructor.py
# Arguments: None
def main():
    #print "Running Instructor.py"
    if len(sys.argv) != 1:
        sys.stderr.write("Usage: Instructor.py\n")
        return 1

    studentjsonfname = '%s/.local/config/%s' % (UBUNTUHOME, "studentlab.json")
    studentconfigjson = open(studentjsonfname, "r")
    studentconfig = json.load(studentconfigjson)
    studentconfigjson.close()
    instructorjsonfname = '%s/.local/config/%s' % (UBUNTUHOME, "instructorlab.json")
    instructorconfigjson = open(instructorjsonfname, "r")
    instructorconfig = json.load(instructorconfigjson)
    instructorconfigjson.close()

    # Output grades.txt
    gradesfilename = '%s/%s' % (UBUNTUHOME, "grades.txt")
    gradesfile = open(gradesfilename, "w")
    gradesfile.write("\n")
    #print "Student JSON config is"
    #print studentconfig
    StudentName = studentconfig['studentname']
    StudentHomeDir = studentconfig['studenthomedir']
    LabName = studentconfig['labname']
    LabIDName = studentconfig['labid']
    SaveDirName = studentconfig['savedirectory']
    InstructorName = instructorconfig['instructorname']
    InstructorHomeDir = instructorconfig['instructorhomedir']
    InstructorBaseDir = instructorconfig['instructorbasedir']
    NumStudent = int(instructorconfig['numstudent'])
    GraderScript = instructorconfig['graderscript']

    # Call AnswerParser script to parse 'answer'
    AnswerParser.ParseAnswer()

    # Call GoalsParser script to parse 'goals'
    GoalsParser.ParseGoals()

    index=0
    while index < NumStudent:
        #print "Current index is %d" % index
        index = index + 1

        ZipFileName = 'student%d.%s.zip' % (index, LabIDName)
        DestinationDirName = 'student%d.%s' % (index, LabIDName)
        OutputName = '%s%s' % (InstructorHomeDir, ZipFileName)
        DestDirName = '%s%s' % (InstructorHomeDir, DestinationDirName)
        InstDirName = '%s%s' % (InstructorBaseDir, DestinationDirName)

        #print "Current ZipFilename is %s" % ZipFileName
        #print "Current DestinationDirName is %s" % DestinationDirName
        #print "Current DestDirName is %s" % DestDirName
        #print "Current InstDirName is %s" % InstDirName

        if os.path.exists(DestDirName):
            #print "Removing %s" % DestDirName
            os.system('rm -rf %s' % DestDirName)

        zipoutput = zipfile.ZipFile(OutputName, "r")
        zipoutput.extractall(DestDirName)
        zipoutput.close()

        # Call ResultParser script to parse students' result
        #command = 'ResultParser.py %s %s %s' % (DestDirName, InstDirName, LabIDName)
        #print "About to do (%s)" % command
        #os.popen(command)
        ResultParser.ParseStdinStdout(DestDirName, InstDirName, LabIDName)

        # Call grader script 
        #command = '%s %s %s %s' % (GraderScript, DestDirName, InstDirName, LabIDName)
        #print "About to do (%s)" % command
        #grades = os.popen(command).read().splitlines()
        grades = Grader.ProcessStudentLab(DestDirName, InstDirName, LabIDName)
        #print "After ProcessStudentLab Instructor, grades is "
        #print grades

        LabIDStudentName = '%s : student%d : ' % (LabIDName, index)
        printresult(gradesfile, LabIDStudentName, SaveDirName, grades)

    gradesfile.write("\n")
    gradesfile.close()
    return 0

if __name__ == '__main__':
    sys.exit(main())

