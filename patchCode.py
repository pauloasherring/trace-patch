#!/usr/bin/env python
# Developement: Paulo Sherring
# Based on cppclean, by Neal Norwitz.
# This tool will patch the functions it find with:
#     A macro call at the begining (see 'inprint' below);
#     A macro call at each return point, either because of a return clause or because a void function came to an end (see 'ouprint' below). 
#
# Usage: 
#       patchCode file1.cpp file2.c 
#       This causes the patchCode to patch enlisted files.
#
#       patchCode
#       This causes patchCode to find *.c, *.cpp and *.cc in the current folder and process them.
#
# Original cppclean copyright notice:
# Copyright 2007 Neal Norwitz
# Portions Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

outprint = 'TRACE_ME_OUT;\n'
inprint = 'TRACE_ME_IN;\n'

import argparse
import fnmatch
import os
import sys
import glob
import re

from cpp import __version__
from cpp import ast
from cpp import tokenize
from cpp import utils


def insert (source_str, insert_str, pos):
    return source_str[:pos] + insert_str + source_str[pos:]

def remove_lines (source_str, remove_lines):
    for rem_line in remove_lines:
        rem_line = rem_line.strip()
        rem_line = f'(^.*?{rem_line}.*?\n)'
        mat = re.findall(rem_line,source_str, flags=re.M)
        if mat is not None:
            match_cnt = len(mat)
            for it in mat:
                source_str = source_str.replace(it,'',1)
    return source_str

def calc_ident(source, offset):
    initOffset = offset
    while source[offset] != '\n' and offset != 0:
        cc = source[offset-10:offset+10]
        ccc = source[offset]
        offset -= 1
    return initOffset - offset

def calc_start_of_line(source, bodylist):

    if bodylist[-1].name == ';':
        item_count = len(bodylist) - 2
    else:
        item_count = len(bodylist) - 1
    
    while item_count != 0:
        if bodylist[item_count].name == ';':
            break
        item_count -= 1
    return item_count + 1

def match_file(filename, exclude_patterns):
    """Return True if file is a C++ file or a directory."""
    base_name = os.path.basename(filename)
    if base_name.startswith('.'):
        return False
    for pattern in exclude_patterns:
        if fnmatch.fnmatch(base_name, pattern):
            return False
    if os.path.isdir(filename):
        return True
    return False

def find_files(filenames, exclude_patterns):
    """Yield filenames."""
    while filenames:
        name = filenames.pop(0)
        if os.path.isdir(name):
            for root, directories, children in os.walk(name):
                filenames += [os.path.join(root, f) for f in sorted(children)
                              if match_file(os.path.join(root, f),
                                            exclude_patterns)]
                directories[:] = [d for d in directories
                                  if match_file(os.path.join(root, d),
                                                exclude_patterns)]
        else:
            yield name

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('files', nargs='*', default=[])
    parser.add_argument('--unpatch', action='store_true', default=False, help='removes patching from patched files.')
    parser.add_argument('--verbose', action='store_true', help='print verbose messages')
    parser.add_argument('--version', action='version', version='%(prog)s ' + __version__)
    parser.add_argument('--quiet', '-q', action='store_true', help='ignore parse errors')
    args = parser.parse_args()
    if len(args.files ) == 0 :
        filelist = glob.glob('.\\*.c')
        filelist += glob.glob('.\\*.cpp')
        filelist += glob.glob('.\\*.cc')
    else:
        # For Python 2 where argparse does not return Unicode.
        args.files = [filename.decode(sys.getfilesystemencoding())
                    if hasattr(filename, 'decode') else filename
                    for filename in args.files]
        filelist = ( sorted(find_files(args.files, exclude_patterns=[])))
        if (len(filelist) == 1 and isinstance(filelist, list)):
            mat = re.match('.+?\..{1,3}\s.+',filelist[0])
            if mat is not None:
                split_file_list = list()
                for item in filelist:
                    for subitem in item.split(' '):
                        split_file_list.append(subitem)
                filelist = split_file_list
    
    status = 0
    for filename in filelist:
        if args.verbose:
            print('Processing', filename, file=sys.stderr)
        try:
            source = utils.read_file(filename)
            if source is None:
                continue
            builder = ast.builder_from_source(source, filename, list(), list(), quiet=args.quiet)
            entire_ast = list([_f for _f in builder.generate() if _f])
            rev_entire_ast = reversed(entire_ast)
            for item in rev_entire_ast:
                if (isinstance( item, ast.Method) or isinstance( item, ast.Function) and (item.body is not None)) :
                    revbody = reversed(item.body)
                    if item.return_type is not None:
                        if 'void' in item.return_type.name:
                            if 'return' not in item.body[-2].name:
                                source = insert(source, '\n'+ ' '*4 + outprint  , item.body[-1].end)
                    for part in revbody:
                        if 'return' in part.name:
                            source = insert(source, outprint + ' '*(calc_ident(source, part.start)-1), part.start)
                    source = insert(source, inprint + ' '*(calc_ident(source, item.body[0].start)-1), part.start)
        except tokenize.TokenError as exception:
            if args.verbose:
                print('{}: token error: {}'.format(filename, exception),
                      file=sys.stderr)
            continue
        except (ast.ParseError, UnicodeDecodeError) as exception:
            if not args.quiet:
                print('{}: parsing error: {}'.format(filename, exception), file=sys.stderr)
            continue
        if args.unpatch == True: 
            source = remove_lines(source, [inprint, outprint])
        fp = open(filename+'.trk', 'w')
        fp.write(source)
        fp.close()
    return status
try:
    sys.exit(main())
except KeyboardInterrupt:
    sys.exit(1)
