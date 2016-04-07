#! /usr/bin/env python3

"""setup.py - setup script for bassclef."""

import sys
from sys import stdout
import os, os.path
import pip
import subprocess
import textwrap
import urllib
import zipfile
import argparse

SUBMODULES = ['font-awesome', 'html5shiv', 'open-sans', 'skeleton']

URLS = ['https://github.com/' + path for path in
        ['tomduck/bassclef-font-awesome/archive/master.zip',
         'aFarkas/html5shiv/archive/master.zip',
         'tomduck/bassclef-open-sans/archive/gh-pages.zip',
         'dhg/Skeleton/archive/master.zip']]

PYTHON3 = sys.executable
if os.name == 'nt': # Cygwin specialization
    PYTHON3 = os.path.splitext(PYTHON3)[0]  # Remove extension
    PYTHON3 = PYTHON3.replace('\\', '/').replace(' ', '\\ ')

PANDOC = None
    
CONVERT = None
    
# pylint: disable=invalid-name
parser = argparse.ArgumentParser(description='Sets up bassclef.')
parser.add_argument('--test', help='Tests installation by running make.',
                    action='store_true')
args = parser.parse_args(sys.argv[1:])

TEST = args.test

#----------------------------------------------------------------------------
# Utility functions

def which(name):
    """Locates a program name on the user's path."""
    # Don't use shutil.which() here.  Shell out so that we see the same
    # thing as the Makefile.  This is essential for cygwin installs.
    try:
        output = subprocess.check_output(['which', name])
        return output.decode(encoding='UTF-8').strip()
    except subprocess.CalledProcessError as e:
        return None

def print(msg):
    """Prints a message to stdout and flushes the buffer."""
    stdout.write(msg)
    stdout.flush()

def error(msg, errno):
    """Writes an error message to stdout and exits."""
    print(textwrap.dedent(msg) + '\n')
    sys.exit(errno)

#----------------------------------------------------------------------------

def check_python():
    """Checks python."""

    global PYTHON3  # pylint: disable=global-statement

    print('Checking python... ')

    # Check the python version
    if sys.version_info < (3, ):
        msg = """

        Python < 3 detected.  Please upgrade and/or call this script
        using Python 3.
        
        """
        error(msg, 1)

    # Test python from the shell
    try:
        subprocess.check_output([PYTHON3, '--version'])
    except subprocess.CalledProcessError as e:
        msg = """

        Python failed with error code %d.  Please submit an Issue to
        https://github.com/tomduck/bassclef.

        """ % e.returncode
        error(msg, 2)

    print('OK.\n')

#----------------------------------------------------------------------------

def check_make():
    """Checks make."""

    print("Checking make... ")
    if which('make') is None:
        msg = """

        Cannot find 'make'.  Please ensure that 'make' is available from
        the command line.

        """
        error(msg, 3)

    print('OK.\n')

#----------------------------------------------------------------------------

def check_pandoc():
    """Checks pandoc."""

    global PANDOC  # pylint: disable=global-statement

    print("Checking pandoc... ")

    PANDOC = which('pandoc')

    if PANDOC:
        try:
            subprocess.check_output([PANDOC, '--version'])
        except (subprocess.CalledProcessError, AssertionError) as e:
            pass

    if not PANDOC:            
        msg = """

        Cannot find 'pandoc'.  Please ensure that 'pandoc' is available from
        the command line.

        To download pandoc, see:

            https://github.com/jgm/pandoc/releases/latest

        """
        error(msg, 4)

    print('OK.\n')

#----------------------------------------------------------------------------

def check_convert():
    """Checks ImageMagick convert."""

    global CONVERT  # pylint: disable=global-statement
    
    print("Checking convert... ")

    # Find a working version of ImageMagick convert.  Note that Windows has
    # a separate convert utility that we have to watch out for.
    paths = [which('convert'), '/usr/bin/convert', '/usr/local/bin/convert']
    for path in paths:
        if path:
            try:
                output = subprocess.check_output([path, '--version'])
                output = output.decode(encoding='UTF-8')
                assert 'ImageMagick' in output
            except (FileNotFoundError, subprocess.CalledProcessError,
                    AssertionError) as e:
                pass
            else:
                CONVERT = path
                
    if not CONVERT:
            
        msg = """

        Cannot find ImageMagick 'convert'.  Please ensure that 'convert' is
        available from the command line.

        To download ImageMagick, see:

            https://www.imagemagick.org/script/binary-releases.php

        """
        error(msg, 5)

    print('OK.\n\n')

#----------------------------------------------------------------------------

def install_pyyaml():
    """Installs pyyaml."""
    try:
        import yaml  # pylint: disable=unused-variable
        print('PyYAML found.\n')
    except ImportError:
        print('Installing pyyaml... ')
        ret = pip.main('install --quiet pyyaml --user'.split())

        if ret != 0:

            msg = """

            Could not install PyYAML. Please submit an Issue to
            https://github.com/tomduck/bassclef.

            """
            error(msg, 6)
        
        print('Done.\n\n')

#----------------------------------------------------------------------------

def has_submodule(name):
    """Returns True if the submodule appeaers to be installed."""
    return os.listdir(os.path.join('submodules', name))

def install_submodules():
    """Installs submodules aggregated with bassclef."""

    # Print out a message
    flag = True
    for submodule in SUBMODULES:
        if not has_submodule(submodule):
            print('\nInstalling submodules:\n')
            flag = False
            break
    if flag:
        print('Submodules found.\n')
        return

    # Is this a git repository?
    is_repo = os.path.exists('.git')

    # Install the submodules
    if is_repo:   # Assume user has git installed

        if subprocess.call('git submodule update --init'.split()) != 0:
            msg = """

            Error installing submodules with git.  Please submit an Issue to
            https://github.com/tomduck/bassclef.

            """
            error(msg, 7)

    else:  # Download zips and unpack them into submodules/

        def prog(n=0):
            """Progress meter."""
            while True:
                if n%20 == 0:
                    print('.')
                yield
                n += 1
        report = prog().__next__

        for submodule, url in zip(SUBMODULES, URLS):
            if not has_submodule(submodule):

                # Set up
                print('Downloading/installing %s...'%submodule)
                os.chdir('submodules')

                # Download zip
                urllib.request.urlretrieve(url, 'download.zip',
                                           lambda x, y, z: report())

                # Unpack
                z = zipfile.ZipFile('download.zip', 'r')
                dirname = os.path.commonprefix(z.namelist())
                z.extractall()
                z.close()

                # Install
                os.rmdir(submodule)
                os.rename(dirname, submodule)

                # Clean up
                os.remove('download.zip')
                os.chdir('..')
                print(' Done.\n')

#----------------------------------------------------------------------------

def generate_makefile():
    """Generates Makefile from Makefile.in"""

    print('\nGenerating Makefile... ')

    # Read Makefile.in
    with open('Makefile.in') as f:
        lines = f.readlines()

    # Write Makefile.  Perform replacements as necessary.
    with open('Makefile', 'w') as f:
        for line in lines:
            if line.startswith('PYTHON3 ='):
                line = 'PYTHON3 = ' + PYTHON3 + '\n'
            if line.startswith('PANDOC ='):
                line = 'PANDOC = ' + PANDOC + '\n'
            if line.startswith('CONVERT ='):
                line = 'CONVERT = ' + CONVERT + '\n'

            f.write(line)

    print('Done.\n')

#----------------------------------------------------------------------------

def test():
    """Tests the install."""

    print('\nTesting install... ')

    try:
        subprocess.check_output('make')
        print('OK.\n')

    except subprocess.CalledProcessError as e:

        msg = """

        'make' failed (error code %d).  Please submit an Issue to
         https://github.com/tomduck/bassclef.

        """ % e.returncode
        error(msg, 8)

#----------------------------------------------------------------------------

def finish():
    """Finishes up."""
    msg = """
    Bassclef setup complete.  You may run this script again if your system
    configuration changes.

    """
    print(textwrap.dedent(msg))

#----------------------------------------------------------------------------

def main():
    """Main program."""

    print('\n')

    check_python()
    check_make()
    check_pandoc()
    check_convert()

    install_pyyaml()
    install_submodules()

    generate_makefile()

    if TEST:
        test()

    finish()

if __name__ == '__main__':
    main()
