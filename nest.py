#!/usr/bin/env python
# coding: utf-8

import yaml
import sys
import shutil
import re
import urllib.request
import zipfile
from contextlib import contextmanager
import os
import pathlib
import subprocess
from datetime import datetime

if not (sys.version_info > (3, 0)):
   raise RuntimeError("We are using too many python 3 constructs, so this is only working with python 3")

class ChecksumError(Exception):
    """ Raised when a checksum is violated. """
    pass

def convert_date(date_str):
    objDate = datetime.strptime(date_str, '%Y-%m-%d')
    return datetime.strftime(objDate,'%d %b %Y')

def md5(path):
    """ Compute the MD5 hash of a path and return it as a string. """
    import hashlib
    if not isinstance(path,str):
        raise TypeError("path should be a string")
    BUF_SIZE = 65536  # lets read stuff in 64kb chunks!
    md5 = hashlib.md5()
    with open(path, 'rb') as f:
        while True:
            data = f.read(BUF_SIZE)
            if not data:
                break
            md5.update(data)
    return md5.hexdigest()

def gzip(path):
    """ Gzip a path (very much like command line gzip does) """
    import gzip as gz
    with open(path, 'rb') as f_in:
        with gz.open(path + '.gz', 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    os.remove(path)

def get_reference(doi):
    # check if unpublished/submitted
    if(doi.lower()=="unpublished" or doi.lower()=="submitted"): return doi.lower()
    # retrieve citation
    cit = subprocess.check_output('curl -LH "Accept: text/bibliography; style=science" http://dx.doi.org/'+doi, shell=True).decode('utf-8').strip()
    if("DOI Not Found" in cit):
      reference="DOI not found"
    else:
      reference=cit[3:len(cit)]
    return reference
 
def get_short_name_ini(lname, length):
    if(len(lname)>length): sname = lname[0:length]+"..."
    else: sname = lname
    return sname

def get_short_name_end(lname, length):
    l=len(lname)
    if(l>length): sname = "..."+lname[l-length:l]
    else: sname = lname
    return sname

def plumed_format(source,global_header=None,header=None,docbase=None):
    """ Format plumed input file.

    source: path to master input file
    global_header: header added to all the (recursively) converted files.
    run_header: header added only to the master file.

    """
    suffix="md"
    if not docbase:
        docbase="https://plumed.github.io/doc-master/user-doc/html/"
    # list of generated files, returned
    lista=[]
    with open(source) as f:
        destination=source + "." + suffix
        lista.append(destination)
        with open(destination,"w") as o:
            lines = f.read().splitlines()
            continuation=False
            action=""
            endplumed=False
            action_next_line=False
            if global_header:
                 print(global_header,file=o)
            print("**Source:** " + re.sub("^data/","",source)+"  ",file=o)
            if header:
                 print(header,file=o)
            # make sure Jekyll does not interfere with format
            # <pre> marks a preformatted block
            print("{% raw %}<pre>",file=o)
            for line in lines:
                words=re.sub("#.*","",line).split()
                if endplumed:
                    line="<span style=\"color:blue\">" + line + "</span>"
                else:
                    if continuation:
                        if len(words)>0:
                            if words[0]=="...":
                                # end of continuation
                                continuation=False
                            if action_next_line:
                                # action was not in first line, thus it is here
                                action=words[0]
                                action_next_line=False
                    else:
                        action=""
                        action_next_line=False
                        if len(words)>0:
                            if len(words)>1 and words[-1]=="...":
                                # first line of multiline action:
                                continuation=True
                                if re.match("^.*:$",words[0]):
                                    if len(words)>2:
                                        # first word is the label
                                        action=words[1]
                                    else:
                                        # first word of next nonempty line will be the action
                                        action_next_line=True
                                else:
                                    action=words[0]
                            else:
                                # single line action, easy to parse:
                                if re.match("^.*:$",words[0]):
                                    action=words[1]
                                else:
                                    action=words[0]
                    if len(action)>0:
                        und_action = ''
                        for ch in action:
                            und_action = und_action + '_' + ch
                        action_url="<a href=\"" + docbase + re.sub('___+', '__', und_action.lower()) + ".html\">" + action + "</a>"
                        # only replace first instance
                        line=re.sub(action,action_url,line,count=1)
                    
                    if action=="ENDPLUMED":
                        endplumed=True
                    
                    if action=="INCLUDE":
                        # for now only oneline INCLUDE statements are supported. Could be extended later
                        if len(words)>1 and re.match("^FILE=.*",words[1]):
                            file=re.sub("^FILE=","",words[1])
                            try:
                                lista+=plumed_format(str(pathlib.PurePosixPath(source).parent)+"/"+file,global_header=global_header)
                                # we here link with html suffix (even if we generated md files) otherwise links to do work after rendering
                                file_url="<a href=\"" + file + ".html\">" + file + "</a>" 
                                line=re.sub(" FILE=[^ ]*"," FILE=" + file_url,line)
                            except FileNotFoundError:
                                # if file is not found, do not replace the link and do not append lista
                                pass
                            
                # mark comments as such
                line=re.sub("(#.*$)","<span style=\"color:blue\">\\1</span>",line)    

                # store special links here to make it easier to change them later if we modify the manual:
                links={"vim":"_vim_syntax.html",
                       "replicas":"special-replica-syntax.html",
                       "groups":"_group.html",
                       "molinfo":"_m_o_l_i_n_f_o.html"}

                # list of special atom selections. only those that are not for a specific residue are needed.
                # the others are found searching the dash (s)
                keys={"groups":["mdatoms","allmdatoms"],
                      "molinfo":["nucleic","protein","water","ions","hydrogens","nonhydrogens"]
                     }

                # link to vim:ft=plumed
                line=re.sub("(vim: *ft=plumed)","<a href=\"" + docbase + links["vim"] +"\">\\1</a>",line)

                # @ is kept out of the link so that the following substitutions do not find it
                line=re.sub("@(replicas):","@<a href=\"" + docbase + links["replicas"]+"\">\\1</a>:",line)
                for w in keys["groups"]:
                    line=re.sub("@("+w+")([^0-9A-Za-z_]|$)","@<a href=\"" + docbase + links["groups"]+"\">\\1</a>\\2",line)
                for w in keys["molinfo"]:
                    line=re.sub("@("+w+")([^0-9A-Za-z_]|$)","@<a href=\"" + docbase + links["molinfo"]+"\">\\1</a>\\2",line)
                # this is generic MOLINFO substitution: @anything followed by -
                line=re.sub("@([^ ,{}<-]+-[0-9A-Za-z_-]+)","@<a href=\"" + docbase + links["molinfo"] + "\">\\1</a>",line)

                print(line,file=o)
                
            print("</pre>{% endraw %}",file=o)
            # convert to set to remove duplicates
            return list(set(lista))


def plumed_input_test(exe,source,global_header,natoms,nreplicas):
    run_folder = str(pathlib.PurePosixPath(source).parent)
    plumed_file = os.path.basename(source)
    outfile=source + "." + exe + ".stdout.txt"
    errfile=source + "." + exe + ".stderr.md"
    with open(errfile,"w") as stderr:
        print(global_header,file=stderr)
        print("Stderr for source: ",re.sub("^data/","",source),"  ",file=stderr)
        print("(download [gzipped raw stdout](" + plumed_file + "." + exe + ".stdout.txt.gz))  ",file=stderr)
        print("{% raw %}\n<pre>",file=stderr)
    with open(outfile,"w") as stdout:
        with open(errfile,"a") as stderr:
            with cd(run_folder):
                options=[exe, 'driver', '--natoms', str(natoms), '--parse-only', '--kt', '2.49', '--plumed', plumed_file]
                #if nreplicas>0:
                #    options=['mpiexec', '-np', str(nreplicas)] + options + ['--multi', str(nreplicas)]
                child = subprocess.Popen(options, stdout=stdout, stderr=stderr)
                child.communicate()
                rc = child.returncode
    with open(errfile,"a") as stderr:
        print("</pre>\n{% endraw %}",file=stderr)
    gzip(outfile)
    return rc

def add_readme(file, tested, success, exe):
    with open("README.md","a") as o:
        badge = ''
        for i in range(len(tested)):
            badge = badge + ' [![tested on ' + tested[i] + '](https://img.shields.io/badge/' + tested[i] + '-'
            if success[i]==0: 
                badge = badge + 'passing-green.svg'
            else:
                badge = badge + 'failed-red.svg'
            badge = badge + ')](' + file + '.' +  exe[i] + '.stderr)'
        print("| [" + get_short_name_end(re.sub("^data/","",file), 50) + "](./"+file+".md"+") | " + badge + " |" + "  ", file=o)


@contextmanager
def cd(newdir):
    prevdir = os.getcwd()
    os.chdir(os.path.expanduser(newdir))
    try:
        yield
    finally:
        os.chdir(prevdir)

def process_egg(path,eggdb=None):

    if not eggdb:
        eggdb=sys.stdout

    with cd(path):

        stram = open("nest.yml", "r")
        config=yaml.load(stram,Loader=yaml.BaseLoader)
        # check fields
        for field in ("url","pname","category","keyw","contributor","doi","history"):
            if not field in config:
               raise RuntimeError(field+" not found")
        print(path,config)

        # allow using a dictionary. We might enforce a dictionary here if we prefer this syntax.
        if isinstance(config["history"],dict):
           h=[]
           for k in sorted(config["history"]):
              h.append([k,config["history"][k]])
           config["history"]=h

        if re.match("^.*\.zip$",config["url"]):
            if os.path.exists("download"):
               shutil.rmtree("download")
            os.mkdir("download")
            urllib.request.urlretrieve(config["url"], 'file.zip')
            if "md5" in config:
                md5_=md5("file.zip")
                if md5_ != config["md5"] :
                   raise ChecksumError("md5 not matching " + md5_)
            zf = zipfile.ZipFile("file.zip", "r")
            root=list(set([ x.split("/")[0] for x in zf.namelist()]))
            # there is a main root directory
            if(len(root)==1): root="download/" + root[0]
            # there is not
            else:        root="download/"
            zf.extractall(path="download")
            if os.path.exists("data"):
               shutil.rmtree("data")
            shutil.move(root,"data")
        else:
            raise RuntimeError("cannot interpret url " + config["url"])

        if not "plumed_input" in config:
            # discover path relative to data dir
            with cd("data"):
                config["plumed_input"]=sorted(pathlib.Path('.').glob('**/plumed*.dat'))
                config["plumed_input"]=[ {"path":str(v)} for v in config["plumed_input"]]
        else:
            conf=config["plumed_input"]
            for k in range(len(conf)):
                if not isinstance(conf[k],dict):
                    conf[k]={"path":conf[k]}

        # prepend data to all paths
        for f in config["plumed_input"]:
            f["path"]="data/" + f["path"]

        egg_id=path[5:7] + "." + path[8:11]
        global_header="**Project ID:** [plumID:" + egg_id+"]({{ '/' | absolute_url }}" + path + ")  "

        with open("badge.svg","w") as badge:
            print("<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"120\" height=\"20\">", file=badge)
            print("<linearGradient id=\"a\" x2=\"0\" y2=\"100%\">", file=badge)
            print("<stop offset=\"0\" stop-color=\"#bbb\" stop-opacity=\".1\"/>", file=badge)
            print("<stop offset=\"1\" stop-opacity=\".1\"/></linearGradient>", file=badge)
            print("<rect rx=\"3\" width=\"120\" height=\"20\" fill=\"#555\"/>", file=badge)
            print("<rect rx=\"3\" x=\"67\" width=\"53\" height=\"20\" fill=\"#155799\"/>", file=badge)
            print("<path fill=\"#155799\" d=\"M67 0h4v20h-4z\"/>", file=badge)
            print("<rect rx=\"3\" width=\"120\" height=\"20\" fill=\"url(#a)\"/>", file=badge)
            print("<g fill=\"#fff\" text-anchor=\"middle\" font-family=\"DejaVu Sans,Verdana,Geneva,sans-serif\" font-size=\"11\">", file=badge)
            print("<text x=\"34.5\" y=\"15\" fill=\"#010101\" fill-opacity=\".3\">plumID</text>", file=badge)
            print("<text x=\"34.5\" y=\"14\">plumID</text>", file=badge)
            print("<text x=\"92.5\" y=\"15\" fill=\"#010101\" fill-opacity=\".3\">"+egg_id+"</text>", file=badge)
            print("<text x=\"92.5\" y=\"14\">"+egg_id+"</text></g></svg>", file=badge)

        with open("README.md","w") as o:
            print(global_header, file=o)
            print("**Name:** ",config["pname"]+"  ", file=o)
            print("**Archive:** [",config["url"]+"]("+config["url"]+")  ", file=o)
            if "md5" in config:
                print("**Checksum (md5):**",config["md5"]+"  ", file=o)
            print("**Category:** ",config["category"]+"  ", file=o)
            print("**Keywords:** ",config["keyw"]+"  ", file=o)
            if "plumed_version" in config:
                print("**PLUMED version:** ",config["plumed_version"]+"  ", file=o)
            print("**Contributor:** ",config["contributor"]+"  ", file=o)
            print("**Submitted on:** "+convert_date(config["history"][0][0])+"  ", file=o)
            if(len(config["history"])>1):
              print("**Last revised:** "+convert_date(config["history"][-1][0])+"  ", file=o)
            # retrieve reference
            reference = get_reference(config["doi"]) 
            if(reference=="unpublished" or reference=="submitted" or reference=="DOI not found"):
              print("**Publication:** " + reference + "  ", file=o)
            else:
              print("**Publication:** [" + reference + "](http://dx.doi.org/"+config["doi"]+")  ", file=o)
            print("  ", file=o)
            print("**PLUMED input files**  ", file=o)
            print("  ", file=o)
            print("| File     | Compatible with |  ", file=o) 
            print("|:--------:|:--------:|  ", file=o)

        for file in config["plumed_input"]:

            if "natoms" in file:
                natoms = int(file["natoms"])
            elif "natoms" in config:
                natoms = int(config["natoms"])
            else:
                natoms = 100000

            if "nreplicas" in file:
                nreplicas = int(file["nreplicas"])
            elif "nreplicas" in config:
                nreplicas = int(config["nreplicas"])
            else:
                nreplicas = 0 # 0 means do not use mpiexec

            if "plumed_version" in file:
                plumed_version=file["plumed_version"]
            elif "plumed_version" in config:
                plumed_version=config["plumed_version"]
            else:
                plumed_version="not specified"

            header="**Originally used with PLUMED version:** " + plumed_version + "  \n"
            header+= "**Stable:** [raw gzipped stdout]("+ re.sub(".*/","",file["path"]) +".plumed.stdout.txt.gz) - [stderr]("+ re.sub(".*/","",file["path"]) +".plumed.stderr)  \n"
            header+= "**Master:** [raw gzipped stdout]("+ re.sub(".*/","",file["path"]) +".plumed_master.stdout.txt.gz) - [stderr]("+ re.sub(".*/","",file["path"]) +".plumed_master.stderr)  \n"
# in principle returns the list of produced files, not used yet:
            plumed_format(file["path"],global_header=global_header,header=header)
            success=plumed_input_test("plumed",file["path"],global_header,natoms,nreplicas)
            #success_master=plumed_input_test("plumed_master",file["path"],global_header,natoms,nreplicas)
            success_master=plumed_input_test("plumed",file["path"],global_header,natoms,nreplicas)
            stable_version='v' + subprocess.check_output('plumed info --version', shell=True).decode('utf-8').strip()
            add_readme(file["path"], (stable_version,"master"), (success,success_master),("plumed","plumed_master"))

        # print instructions, if present
        with open("README.md","a") as o:
             print("  ", file=o)
             print("**Project description and instructions**  ", file=o)
             try:
               print(config["instructions"], file=o)
             except KeyError:
               print("*Description and instructions not provided*  ",file=o)
             print("  ", file=o)
             print("**Submission history**  ", file=o)
             for i,h in enumerate(config["history"]): 
                 print("**[v"+str(i+1)+"]** "+convert_date(h[0])+": "+h[1]+"  ", file=o)
             #print("[![plumeDnest:" + egg_id +"](./badge.svg)](./badge.svg) ", file=o)
             print("<img src=\"./badge.svg\" alt=\"plumeDnest:" + egg_id + "\" id=\"myBtn\"/>", file=o)
             print("<div id=\"myModal\" class=\"modal\">", file=o)
             print("  <div class=\"modal-content\">", file=o)
             print("    <span class=\"close\">&times;</span>", file=o)
             print("    Markdown<pre>[![plumID:" + egg_id + "](https://www.plumed-nest.org/eggs-" + path[5:7] + "/" + path[8:11] + "/badge.svg)](https://www.plumed-nest.org/test-site/eggs-" + path[5:7] + "/" + path[8:11] + "/)</pre>", file=o)
             print("    HTML<pre>&lt;a href=\"https://www.plumed-nest.org/test-site/eggs-" + path[5:7] + "/" + path[8:11] + "\"&gt;&lt;img src=\"https://www.plumed-nest.org/eggs-" + path[5:7] + "/" + path[8:11] + "/badge.svg\" alt=\"plumID:" + egg_id + "\"&gt;&lt;/a&gt;</pre>", file=o)
             print("  </div>", file=o)
             print("</div>", file=o)

# quote around id is required otherwise Jekyll thinks it is a number
        print("- id: '" + egg_id + "'",file=eggdb)
        print("  name: " + config["pname"],file=eggdb)
        print("  shortname: " + get_short_name_ini(config["pname"],15),file=eggdb)
        print("  category: " + config["category"],file=eggdb)
        print("  keywords: " + config["keyw"],file=eggdb)
        print("  shortkeywords: " + get_short_name_ini(config["keyw"],25),file=eggdb)
        print("  contributor: " + config["contributor"],file=eggdb)
        print("  doi: " + config["doi"],file=eggdb)
        print("  path: " + path,file=eggdb)
        print("  reference: '" + reference +"'",file=eggdb)

    eggdb.flush()

if __name__ == "__main__":
    with open("_data/eggs.yml","w") as eggdb:
        print("# file containing egg database.",file=eggdb)

        # list of paths - not ordered
        pathlist=list(pathlib.Path('.').glob('eggs*/*/nest.yml'))
        # cycle on ordered list
        for path in sorted(pathlist, reverse=True, key=lambda m: str(m)):

            process_egg(re.sub("nest.yml$","",str(path)),eggdb)

