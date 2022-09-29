"""
This file is part of the machine-ocean-satdata repository
<https://github.com/metno/machine-ocean-satdata>.
py-mmd-tools is licensed under the Apache License 2.0
<https://github.com/metno/machine-ocean-satdata/blob/main/LICENSE>
"""
import os
import shutil

import pytest

##
#  Directory Fixtures
##

@pytest.fixture(scope="session")
def rootDir():
    """The root folder of the repository."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))


@pytest.fixture(scope="session")
def tmpDir():
    """A temporary folder for the test session. This folder is
    presistent after the tests have run so that the status of generated
    files can be checked. The folder is instead cleared before a new
    test session.
    """
    testDir = os.path.dirname(__file__)
    theDir = os.path.join(testDir, "temp")
    if os.path.isdir(theDir):
        shutil.rmtree(theDir)
    if not os.path.isdir(theDir):
        os.mkdir(theDir)
    return theDir

@pytest.fixture(scope="session")
def filesDir():
    """A path to the reference files folder."""
    testDir = os.path.dirname(__file__)
    theDir = os.path.join(testDir, "files")
    return theDir


@pytest.fixture(scope="function")
def fncDir(tmpDir):
    """A temporary folder for a single test function."""
    fncDir = os.path.join(tmpDir, "f_temp")
    if os.path.isdir(fncDir):
        shutil.rmtree(fncDir)
    if not os.path.isdir(fncDir):
        os.mkdir(fncDir)
    return fncDir


##
#  Mock Files
##


##
#  Objects
##
