__author__ = 'tyc85'

import re
import pdb
import python_antenna_pattern.config as config


def parse_freq_band(file_name):
    pattern = re.compile(r'''
        \s*                # skip the leading spaces
        (?P<leading>\S+?)_   
        (?P<ant_num>\S+?)_  # 0 or more digit non-greedy match: (e.g., ant1)
        .+?                # whatever that is in between, non greedy match
        (?P<band>\d+)      # the trailing band with 3 - 4 digits
        \S*                # rest of the string
    ''', re.VERBOSE)
    
    m = pattern.match(file_name)
    if m == None:
        print('matching frequency band failed\n')
        raise

    if config.VERBOSE is True:
        print('file name parsing yield:', 
              [m.group('leading'), m.group('ant_num'), m.group('band')])
    
    return m.group('band')
           

