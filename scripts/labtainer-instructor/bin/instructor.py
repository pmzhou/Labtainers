#!/usr/bin/env python
'''
This software was created by United States Government employees at 
The Center for the Information Systems Studies and Research (CISR) 
at the Naval Postgraduate School NPS.  Please note that within the 
United States, copyright protection is not available for any works 
created  by United States Government employees, pursuant to Title 17 
United States Code Section 105.   This software is in the public 
domain and is not subject to copyright. 
'''

# Instructor.py
# Description: * Read instructorlab.json and extract a zip file
#                containing the student lab work
#              * Call script to grade the student lab work

import copy
import json
import os
import sys
import zipfile
import time
import glob
import Grader
import GoalsParser
import ResultParser

UBUNTUHOME="/home/ubuntu"

def store_student_parameter(gradesjson, email_labname, student_parameter):
    #print('store_student_parameter email_labname %s student_parameter %s' % (email_labname, student_parameter))
    if email_labname not in gradesjson:
        gradesjson[email_labname] = {}
        gradesjson[email_labname]['parameter'] = copy.deepcopy(student_parameter)
        gradesjson[email_labname]['grades'] = {}
    else:
        if gradesjson[email_labname]['parameter'] != {}:
            # Already have that student's parameter stored
            print("instructor.py store_student_parameter: duplicate email_labname %s student_parameter %s" % (email_labname, student_parameter))
            exit(1)
        else:
            gradesjson[email_labname]['parameter'] = copy.deepcopy(student_parameter)

def store_student_grades(gradesjson, email_labname, grades):
    #print('store_student_grades email_labname %s grades %s' % (email_labname, grades))
    if email_labname not in gradesjson:
        gradesjson[email_labname] = {}
        gradesjson[email_labname]['parameter'] = {}
        gradesjson[email_labname]['grades'] = copy.deepcopy(grades)
    else:
        if gradesjson[email_labname]['grades'] != {}:
            # Already have that student's grades stored
            print("instructor.py store_student_grades: duplicate email_labname %s grades %s" % (email_labname, grades))
            exit(1)
        else:
            gradesjson[email_labname]['grades'] = copy.deepcopy(grades)

def printresult(gradesfile, LabIDStudentName, grades):
    gradesfile.write("%s" % LabIDStudentName)
    for (each_key, each_value) in grades.iteritems():
        #print "Current key is ", each_key
        #print "Current value is ", each_value
        if each_key.startswith('_'):
            # Skip, i.e., do not print if it starts with '_'
            continue
        else:
            if each_value:
                gradestring = '%s=%s' % (each_key, "P")
            else:
                gradestring = '%s=%s' % (each_key, "F")
            gradesfile.write('%s ' % gradestring)
    gradesfile.write('\n')

# Usage: Instructor.py
# Arguments: None
def main():
    #print "Running Instructor.py"
    if len(sys.argv) != 1:
        sys.stderr.write("Usage: Instructor.py\n")
        return 1

    instructorjsonfname = '%s/.local/instr_config/%s' % (UBUNTUHOME, "instructorlab.json")
    instructorconfigjson = open(instructorjsonfname, "r")
    instructorconfig = json.load(instructorconfigjson)
    instructorconfigjson.close()

    StudentHomeDir = '/home/ubuntu'
    lab_name_dir = '/home/ubuntu/.local/.labname'
    if not os.path.isfile(lab_name_dir):
        print('ERROR: no file at %s, perhaps running instructor script on wrong containers?')
        exit(1)

    with open(lab_name_dir) as fh:
        LabIDName = fh.read().strip()

    # Output <labname>.grades.txt
    gradesfilename = '%s/%s.%s' % (UBUNTUHOME, LabIDName, "grades.txt")
    gradesfile = open(gradesfilename, "w")
    gradesfile.write("\n")

    InstructorName = instructorconfig['instructorname']
    InstructorHomeDir = instructorconfig['instructorhomedir']
    InstructorBaseDir = instructorconfig['instructorbasedir']
    GraderScript = instructorconfig['graderscript']

    ''' dictionary of container lists keyed by student email_labname '''
    student_list = {}
   
    ''' remove zip files in /tmp directory '''
    # /tmp will be used to store temporary zip files
    TMPDIR = "/tmp"
    for tmpzip in glob.glob("%s/*.zip" % TMPDIR):
        os.remove(tmpzip)
    
    ''' unzip everything ''' 
    ''' First level unzip '''
    zip_files = glob.glob(InstructorHomeDir+'/*.zip')
    first_level_zip = []
    for zfile in zip_files:
        ZipFileName = os.path.basename(zfile)
        first_level_zip.append(ZipFileName)
        OutputName = '%s%s' % (InstructorHomeDir, ZipFileName)
        zipoutput = zipfile.ZipFile(OutputName, "r")
        ''' retain dates of student files '''
        for zi in zipoutput.infolist():
            zipoutput.extract(zi, TMPDIR)
            date_time = time.mktime(zi.date_time + (0, 0, -1))
            dest = os.path.join(TMPDIR, zi.filename)
            os.utime(dest, (date_time, date_time))
        zipoutput.close()

    ''' Second level unzip '''
    zip_files = glob.glob(TMPDIR+'/*.zip')
    for zfile in zip_files:
        ZipFileName = os.path.basename(zfile)
        # Skip first level zip files
        if ZipFileName in first_level_zip:
            continue
        #print('zipfile is %s' % ZipFileName)
        DestinationDirName = os.path.splitext(ZipFileName)[0]
        if '=' in DestinationDirName:
            # NOTE: New format has DestinationDirName as:
            #       e-mail+labname '=' containername
            # get email_labname and containername
            email_labname, containername = DestinationDirName.rsplit('=', 1)
            # Replace the '=' to '/'
            DestinationDirName = '%s/%s' % (email_labname, containername)
            #print email_labname
        else:
            # Old format - no containername
            sys.stderr.write("ERROR: Instructor.py old format (no containername) no longer supported!\n")
            return 1
        student_id = email_labname.rsplit('.', 1)[0]
        #print "student_id is %s" % student_id
        if email_labname not in student_list:
            student_list[email_labname] = []
        student_list[email_labname].append(containername) 
        #print('append container %s for student %s' % (containername, email_labname))
        OutputName = '%s/%s' % (TMPDIR, ZipFileName)
        LabDirName = '%s%s' % (InstructorHomeDir, email_labname)
        DestDirName = '%s%s' % (InstructorHomeDir, DestinationDirName)
        InstDirName = '%s%s' % (InstructorBaseDir, DestinationDirName)

        #print "Student Lab list : "
        #print studentslablist

        if os.path.exists(DestDirName):
            #print "Removing %s" % DestDirName
            os.system('rm -rf %s' % DestDirName)

        zipoutput = zipfile.ZipFile(OutputName, "r")
        ''' retain dates of student files '''
        for zi in zipoutput.infolist():
            zipoutput.extract(zi, DestDirName)
            date_time = time.mktime(zi.date_time + (0, 0, -1))
            dest = os.path.join(DestDirName, zi.filename)
            os.utime(dest, (date_time, date_time))

        zipoutput.close()

    # Store grades, goals, etc
    gradesjson = {}

    ''' create per-student goals.json and process results for each student '''
    for email_labname in student_list:
        # GoalsParser is now tied per student - do this after unzipping file
        # Call GoalsParser script to parse 'goals'
        ''' note odd hack, labinstance seed is stored on container, so need to fine one, use first '''
        DestinationDirName = '%s/%s' % (email_labname, student_list[email_labname][0])
        DestDirName = '%s%s' % (InstructorHomeDir, DestinationDirName)
        student_parameter = GoalsParser.ParseGoals(DestDirName)

        # Call ResultParser script to parse students' result
        LabDirName = '%s%s' % (InstructorHomeDir, email_labname)
        #print('call ResultParser for %s %s' % (email_labname, student_list[email_labname]))
        ResultParser.ParseStdinStdout(LabDirName, student_list[email_labname], InstDirName, LabIDName)

        # Add student's parameter
        store_student_parameter(gradesjson, email_labname, student_parameter)

    ''' assess the results and generate simple report '''
    for email_labname in student_list:
        LabDirName = '%s%s' % (InstructorHomeDir, email_labname)
        grades = Grader.ProcessStudentLab(LabDirName, LabIDName)
        student_id = email_labname.rsplit('.', 1)[0]
        LabIDStudentName = '%s : %s : ' % (LabIDName, student_id)
        printresult(gradesfile, LabIDStudentName, grades)

        # Add student's grades
        store_student_grades(gradesjson, email_labname, grades)

    gradesfile.write("\n")
    gradesfile.close()

    #print "grades (in JSON) is "
    #print gradesjson

    # Output <labname>.grades.json
    gradesjsonname = '%s/%s.%s' % (UBUNTUHOME, LabIDName, "grades.json")
    gradesjsonoutput = open(gradesjsonname, "w")
    try:
        jsondumpsoutput = json.dumps(gradesjson, indent=4)
    except:
        print('json dumps failed on %s' % gradesjson)
        exit(1)
    #print('dumping %s' % str(jsondumpsoutput))
    gradesjsonoutput.write(jsondumpsoutput)
    gradesjsonoutput.write('\n')
    gradesjsonoutput.close()

    # Inform user where the 'grades.txt' are created
    print "Grades are stored in '%s'" % gradesfilename
    return 0

if __name__ == '__main__':
    sys.exit(main())

