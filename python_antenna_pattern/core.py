__author__ = 'tchen'

'''
Description of the script:
0. used set_theta_offset() to rotate the polar axis so that 0 degree is on the top
1. Read the antenna gain vector in planet format
2. Parse the gain vector in polar coordinate for XY plan and vertical plane (not sure whether it's YZ or XZ plane yet)
3. Save a pdf or eps file with the same file name as the input file name but different extension, unless otherwise given
'''

import numpy as np
import matplotlib.pyplot as pyplot
import re
import sys
import glob
import os
try:
    import config
except ImportError:
    import python_antenna_pattern.config as config

def read_name_list(file_name):
    name_list = []
    try:
        with open(file_name, 'r') as fp:
            for line in fp:
                # strip the return character '\n'
                name_list.append(line.rstrip())
    #except FileNotFoundError:
    # to be python 2.7 compatible....
    except IOError:
        with open(file_name.replace('python_antenna_pattern/', ''), 'r') as fp:
            for line in fp:
                # strip the return character '\n'
                name_list.append(line.rstrip())
    return name_list




class AntennaPattern():
    def __init__(self, options=None):
        self.header_re_pattern = re.compile(r'''
            \s*                 # skip leading white spaces
            (?P<header>[\S]+)   # header name: everything other than white spaces
            \s*                 # white space
            (?P<value>[\S]+)    # value of the header entry
            *                   # rest of the line
        ''', re.VERBOSE)
        # should initialize whenever there's a call to parse_ant_by_*
        self.vertical_flag = False
        self.horizontal_flag = False
        self.counter = 0
        self.rho_v = [0.0]*360
        self.rho_h = [0.0]*360
        self.pattern_dict = {} 
        self.max_gain_db = 0
        self.max_gain_db_str = '0'
        self.frequency = 0

    def parse_line(self, line):
        m = self.header_re_pattern.match(line)

        if m is None:
            if line == '':
                return
            else:
                print('no matching for line:\n', line)
            return

        # First horizontal then vertical
        if self.horizontal_flag and self.counter < 360:
            self.rho_h[self.counter] = float(m.group('value'))
            self.counter += 1

        if self.vertical_flag and self.counter < 360:
            self.rho_v[self.counter] = float(m.group('value'))
            self.counter += 1
        # TODO: need to make the labels for pattern general
        if m.group('header').lower() == 'horizontal':
            self.counter = 0
            self.pattern_dict['horizontal'] = self.rho_h
            self.horizontal_flag = True
            self.vertical_flag = False

        elif m.group('header').lower() == 'vertical':
            self.counter = 0
            self.pattern_dict['vertical'] = self.rho_v
            self.vertical_flag = True
            self.horizontal_flag = False

        elif m.group('header').lower() == 'frequency':
            self.frequency = int(m.group('value'))

        elif m.group('header').lower() == 'gain':
            self.max_gain_db = float(m.group('value'))
            # Parse the max gain in string so that tht title can be set accordingly
            # m = header_re_pattern.match(line)
            self.max_gain_db_str = str(self.max_gain_db)

    def parse_data(self, file_name, parse_by='cut'):
        if parse_by == 'cut':
            return self.parse_data_by_cut(file_name)
        else:
            return self.parse_data_by_ant(file_name)

    def parse_data_by_ant(self, file_name):
        if config.VERBOSE is True:
            print('opening file ', file_name)
    
        try:
            with open(file_name, 'r') as fp:
                for line in fp:
                    self.parse_line(line) 
        except IOError:
            # try path without the project name 
            with open(file_name.replace('python_antenna_pattern/', ''), 'r') as fp:
                for line in fp:
                    self.parse_line(line) 

        return True
