#!/usr/bin/env python

"""Tests for `python_antenna_pattern` package."""

import pytest
import subprocess as sp
import shlex


from python_antenna_pattern import python_antenna_pattern


@pytest.fixture
def response():
    """Sample pytest fixture.

    See more at: http://doc.pytest.org/en/latest/fixture.html
    """
    # import requests
    # return requests.get('https://github.com/audreyr/cookiecutter-pypackage')


def test_content(response):
    """Sample pytest test function with the pytest fixture as an argument."""
    # from bs4 import BeautifulSoup
    # assert 'GitHub' in BeautifulSoup(response.content).title.string

def test_cli_help():
    proc = sp.Popen(
        shlex.split('./python_antenna_pattern/cli.py --help'),
        stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.PIPE,
        bufsize=-1
    )
    proc.communicate()
    assert proc.returncode == 0

def test_cli_convert_single_planet_file():
    # TODO: make input file a fixture
    cmd = './python_antenna_pattern/cli.py -v python_antenna_pattern/data/B800A065-18-4E.pln'
    proc = sp.Popen(
        shlex.split(cmd),
        stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.PIPE,
        bufsize=-1
    )
    proc.communicate()
    assert proc.returncode == 0
