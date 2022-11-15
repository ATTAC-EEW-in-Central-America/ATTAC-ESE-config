#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys, seiscomp.client
from seiscomp import core
import datetime
import fnmatch

arc_path = "/home/sysop/seiscomp/var/lib/archive"
link_path = "/home/sysop/CAM/scqcalert/archive"

time = core.Time.GMT()
fmt = '%Y-%m-%d %H:%M:%S.%f'
dt = datetime.datetime.strptime(str(time), fmt)
tt = dt.timetuple()
day_ini = tt.tm_yday-3
#jday = 174

os.system("rm -fr "+link_path+"/*")
for root, dirs, files in os.walk(arc_path):
        for day in range(day_ini, tt.tm_yday, +1):
                for item in fnmatch.filter(files, "*."+str(tt.tm_year)+"."+str(day).zfill(3)):
                        try:
                                link = ""
                                folder = item.split(".")[5]+"/"+item.split(".")[0]+"/"+item.split(".")[1]+"/"+item.split(".")[3]+"."+item.split(".")[4]+"/"
                                real_file = os.path.join(root, item)
                                link = os.path.join(link_path, folder)
                                link_file = link+item
                                if not os.path.exists(link):
                                        os.makedirs(link)
                                os.symlink(real_file, link_file)
                        except Exception as e:
                                print(e)

os.system("/home/sysop/seiscomp/bin/scardac -d mysql://sysop:sysop@192.168.2.244/seiscomp3 -a "+link_path)

