#!/usr/bin/python

import sys, os, shutil, tarfile
import os.path as path
import lxml.etree as et


# print helpful message
if len(sys.argv) != 3:
    print "[info] usage: python olxupdate.py [unzipped course folder] [olx-format update folder]"
    sys.exit(0)


# grab the directory of course and update
course = sys.argv[1]
update = sys.argv[2]


# check if the directory exists
if not path.exists(course) or not path.isdir(course):
    print "Course folder [" + course + "] does not exist"
    sys.exit(0)
elif not path.exists(update) or not path.isdir(update):
    print "Update folder [" + update + "] does not exist"
    sys.exit(0)


# define the error used later
class FileExistsError(Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return self.msg + " already exists"   


class CorruptionError(Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return self.msg + " is a corrupted file"      


# specify olx-format file hierarchy
parent = {
    "chapter": "course",
    "sequential": "chapter",
    "vertical": "sequential",
    "video": "vertical",
    "problem": "vertical",
    "html": "vertical",
    "discussion": "vertical"
}


def list_xml(directory):
    """ List all the xml files in this @directory """
    return filter(lambda f: f[0] != "." and f[-4:] == ".xml", os.listdir(directory))


def scan(document):
    """ Scan the xml @document and return a tuple of its directory and url/id """
    result = ""
    with open(document, "r") as f:
        data = f.read()
        start = data.find("display_name=\"")
        if data == -1:
            raise CorruptionError(document)
        start = data.find("\"", start) + 1
        end = data.find("\"", start)
        result = data[start:end]
    return (document, result)


def scan_xml(directory):
    """ Use @scan and @list_xml to scan all the xml files in this @directory and return a list of tuple """
    return [scan(path.join(directory, document)) for document in list_xml(directory)]


def modify_xml(section, documents):
    """ Modify the parent document of @section in course """
    if section not in parent:
        raise ImportError("cannot import a " + section)
    print "[info] update folder contains a complete", section
    parent_section = parent[section]
    parents = scan_xml(path.join(course, parent_section))
    print "Please select one of the", parent_section, "with its index to insert this", section, ":"
    for i, p in enumerate(parents):
        print i, ":", p[1]
    which = parents[int(raw_input("choose> "))][0]
    root = None
    with open(which, "r") as f:
        xmlstr = f.read()
        root = et.fromstring(xmlstr)
        for document in documents:
            url_name = document[:-4]
            elem = et.SubElement(root, section)
            elem.set("url_name", url_name)
    with open(which, "w") as f:
        f.write(et.tostring(root, pretty_print=True))


# Copy all the files from update to course and call modify_xml only once
first_nonempty_folder = True
for section in ["chapter", "sequential", "vertical", "video", "problem", "html", "discussion"]:
    course_section_path = path.join(course, section)
    update_section_path = path.join(update, section)
    if path.exists(update_section_path):
        documents = list_xml(update_section_path)
        if first_nonempty_folder and len(documents) != 0:
            first_nonempty_folder = False
            modify_xml(section, documents)
        for document in documents:
            if path.exists(path.join(course_section_path, document)):
                raise FileExistsError(document)
            if not path.exists(course_section_path):
                os.mkdir(course_section_path)
            shutil.copyfile(path.join(update_section_path, document), path.join(course_section_path, document))


# Generate the tar.gz file and complete
tgz = path.join(os.getcwd(), path.split(course)[1] + ".tar.gz")
with tarfile.open(tgz, "w:gz") as tar:
    tar.add(course, arcname=path.basename(course))
print "[info] Generated course file:", tgz

    
