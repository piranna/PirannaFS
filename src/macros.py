'''
Created on 27/09/2010

@author: piranna

Functions to achieve metadata about the code
inspired in GCC prepocesor macros

Based on code from Kevil Little at
http://stackoverflow.com/questions/245304/how-do-i-get-the-name-of-a-function-or-method-from-within-a-python-function-or-me/245561#245561
'''


import sys
import os

def LINE(back=0):
    return sys._getframe(back + 1).f_lineno

def FILE(back=0):
    return sys._getframe(back + 1).f_code.co_filename

def FUNC(back=0):
    return sys._getframe(back + 1).f_code.co_name

def WHERE(back=0):
    frame = sys._getframe(back + 1)
    return "%s/%s %s()" % (os.path.basename(frame.f_code.co_filename),
                            frame.f_lineno, frame.f_code.co_name)