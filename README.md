# trace-patch
A Simple C/C++ Function Tracing Patching tool.

# Dependecies:
- Python3
- pip
- cppclean

Ensure you have python3 and pip on your system.
To install cppclean: `python -m pip install cppclean`

# Usage

python3 patchCode.py [--unpatch --recursive] [filename1 filename2]

If no filename is given, it will glob all the \*.c, \*.cpp, and \*.cc files in the current folder.

Flags:
--unpatch: flag to remove the tracing calls;
--recursive: flag to recurse through the current directory;

# Tweaking the script's code

If you need to patch files with extensions such as \*.cc or any C/C++ not covered, you can edit the variable `fileExts` to include whatever you see fit.

If you need to edit the entry or exit macro names, go for `inprint` and `outprint` variables.

If you need a custom macro implementation, edit `defprint` variable.
