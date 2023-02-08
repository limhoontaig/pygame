#!/usr/bin/env python  
# -*- coding: utf-8 -*-  
#  
  
  
import sys  
import getopt  
import logging    
import timeit  
import os  
import shutil  
import re  
from exifread.tags import DEFAULT_STOP_TAG, FIELD_TYPES  
from exifread import process_file  
  
def using():  
    print ("cmd src dest")  
  
def copyfile(dst, datefolder, orgfile):  
    dstfolder = os.path.join(dst, datefolder)  
    if not os.path.exists(dstfolder) :  
        os.makedirs(dstfolder)  
    shutil.copycopy(orgfile, dstfolder)  
    print ("Copy " + orgfile + " To " + dstfolder)  
  
  
def estimateDateByFileName(fname) :  
    #checker = re.compile(r'\d{4}\d{2}\d{2}')  
    checker = re.compile(r'(19|20\d\d)[-_ ]?(0[1-9]|1[012])[-_ ]?(0[1-9]|[12][0-9]|3[01])')  
    m = checker.search(fname)  
  
    if m  :  
        print (m.groups())  
        #print m.group(0)  
        return m.group(1)+"_"+m.group(2)+"_"+m.group(3)  
    else :  
        return "unknown"  
  
  
def main():  
    if len(sys.argv) < 3 :  
        using()  
        sys.exit(0)  
  
    src = sys.argv[1]  
    dst = sys.argv[2]  
  
    for f in os.listdir(src) :  
        print (f)  
        ff = os.path.join(src, f)  
        if os.path.isfile(ff) :  
            ef = open(ff, 'rb')  
            tags = process_file(ef, stop_tag = 'EXIF DateTimeOriginal')  
            if not tags :  
                datefolder = estimateDateByFileName(f)  
                copyfile(dst, datefolder, ff)  
                continue  
            """ 
            for tag in tags.keys(): 
                if tag not in ('JPEGThumbnail', 'TIFFThumbnail', 'Filename', 'EXIF MakerNote'): 
                    print "Key: %s, value %s" % (tag, tags[tag]) 
            """  
            try :  
                oriTime = str(tags["EXIF DateTimeOriginal"]).split(" ")[0].split(":")  
                print (oriTime[0], oriTime[1], oriTime[2])  
                datefolder = oriTime[0]+"_"+oriTime[1]+"_"+oriTime[2]  
                #print datefolder  
                copyfile(dst, datefolder, ff)  
                   
                ef.close()  
            except :  
                datefolder = estimateDateByFileName(f)  
                copyfile(dst, datefolder, ff)  
  
  
  
  
if __name__ == '__main__':  
    main()  