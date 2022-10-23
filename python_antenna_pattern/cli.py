#!/usr/bin/env python
import argparse
import numpy as np
import logging
import matplotlib.pyplot as plt
import os
from optparse import OptionParser
import glob
import sys
try:
  import python_antenna_pattern.config as config
  from python_antenna_pattern.core import AntennaPattern
  from python_antenna_pattern.core import read_name_list
except ModuleNotFoundError:
  import config
  from core import *
  
logger = logging.getLogger(__name__)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# formatter = logging.Formatter('%(asctime)s - %(name)s - [%(levelname)s] %(message)s')
formatter = logging.Formatter('[%(levelname)s] %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

class Pyap:
    def __init__(self, file_list=''):
        self.single_file_flag = False
        #self.parser = OptionParser()
        self.arg_parser = argparse.ArgumentParser(
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        )

        self.arg_parser.add_argument(
            '-v',
            '--verbose',
            action='store_true',
            dest='verbose',
            default=False,
            help='Show all logs when running the commands.'
        )
        self.arg_parser.add_argument(
            '-s',
            '--show-fig',
            action='store_true',
            dest='show_fig',
            default=False,
            help='Show figure. This will pause after each figure is generated.'
        )
        self.arg_parser.add_argument(
            '-g',
            '--show-legend',
            action='store_true',
            dest='show_legend',
            default=False,
            help='Show legend'
        )
        self.arg_parser.add_argument(
            type=str,
            dest='target',
            help=(
                'Use specified file, list of files, or a directory containing '
                'planet files to plot antenna pattern'
            )
        )
        self.arg_parser.add_argument(
            '-r',
            '--rotation-offset',
            type=int,
            dest='rotation_offset',
            default=0,
            help='Rotational offset when plotting the polar pattern'
        )
        self.arg_parser.add_argument(
            '-f',
            '--filetype',
            choices=['eps', 'pdf'],
            dest='filetype',
            default='pdf',
            help='File type of the output figure, either pdf or eps'
        )
        self.arg_parser.add_argument(
            '--fontsize',
            type=int,
            dest='fontsize',
            default=7,
            help='Font size in the legend and the title'
        )
        self.arg_parser.add_argument(
            '-n',
            '--file-name-prefix',
            type=str,
            dest='file_name_prefix',
            default='PYAP_',
            help='Prefix of the generated filename'
        )


    def polar_pattern(self, args):
        #from config import *
        # manually adjust parameters
        # import shlex
        # (options, args) = self.arg_parser.parse_args(shlex.split(arg_input))

        self.plot_pattern(args)


    def wrapper(self, argv):
        # (options, args) = self.arg_parser.parse_args()
        args = self.arg_parser.parse_args()
        if args.verbose is True:
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)
        logger.debug('args is %s', args)
        self.plot_pattern(args)



    # TODO: use optparse to add optinos rather than using config.py
    def plot_pattern(self, options, save_file=True):

        fontsize = options.fontsize
        file_name_prefix=options.file_name_prefix
        file_format=options.filetype
        if os.path.isdir(options.target):
            src_files = glob.glob(options.directory)
            if len(src_files) == 0:
                print(
                    'No files in directory {}'.format(options.target),
                    file=sys.stderr
                )
                sys.exit(os.EX_NOTFOUND)
            else:
                print('Files to be converted: {}'.format(src_files))

        elif os.path.isfile(options.target):
            print('Converting file {}'.format(options.target))
            src_files = [options.target, ]
        else:
            print('Cannot find file or director {}'.format(options.target))
            sys.exit(os.EX_SOFTWARE)


        degree = np.arange(0, 360, 1)
        theta = degree*2*np.pi/360
        p_list = []
        dir_path = []
        band = []
        # TODO: syncup cli args and these configs. or at least be able to pass
        # the config file
        clipping = config.MAX_GAIN_CLIPPING
        loc = config.LOC
        tick_start = config.TICK_START
        tick_stop = config.TICK_STOP
        tick_spacing = config.TICK_SPACING
        tick_stop_shift = 0.2
        lw = 2
        rlim_shift=4

        for file_path in src_files:
            antenna_pattern = AntennaPattern()
            # parse the antenna gains by cut or by antenna
            antenna_pattern.parse_data(file_path, config.PARSE_BY)
            split_name = file_path.rsplit('/')
            file_name = split_name[-1]
            print('processing {}'.format(file_name))
            # temp now is a dictionary of the two antenna pattern in a file
            p_list.append(antenna_pattern)

            #b = parse_freq_band(file_name)
            band.append(antenna_pattern.frequency)
            # all but last element in the list
            dir_path.append('/'.join(split_name[0:-1]) + '/')

        if len(src_files) > 2:
            print(
                'PYAP currently does not support more than a pair of file',
                file=sys.stderr
            )
            sys.exit(os.EX_SOFTWARE)

        if len(src_files) < 2:
            self.single_file_flag = True

        if len(band) > 1:
            print('Frequency band list: {}'.format(band), file=sys.stderr)
            if band[0] != band[1]:
                print(
                    'Frequency band not match: {}'.format(band),
                    file=sys.stderr
                )
                sys.exit(os.EX_SOFTWARE)

        max_gain_db_slist = []
        rho = {}
        counter = 0
        path_counter = 0
        max_list = []

        for pval in p_list:
            # in python 3.x keys() return a set-like object
            labels = list(pval.pattern_dict.keys())
            # clip the small values here
            for i in range(0, 360):
                # clip the horizontal and the vertical vectors
                for key in labels:
                    if pval.pattern_dict[key][i] > clipping:
                        pval.pattern_dict[key][i] = clipping

            # the vertical/horizontal antenna patterns across two files, i.e.,
            # two antennas, are aggregated here the way we aggregate is that
            # the vertial antenna pattern for the first file, is in rho[0:360]
            # and the antenna pattern for the second file is in rho[360:720],
            # and so on. Number of antenna to consider
            for key in list(pval.pattern_dict.keys()):
                if key in rho:
                    rho[key] = np.append(
                        rho[key],
                        pval.max_gain_db - np.asarray(pval.pattern_dict[key])
                    )
                # initialize rho dictionary as empty lists
                else:
                    rho[key] = (
                        pval.max_gain_db - np.asarray(pval.pattern_dict[key])
                    )

        for key in list(pval.pattern_dict.keys()):
            max_gain_db = max(rho[key])
            max_list.append(max_gain_db)
            max_gain_db_str = 'Peak Gain: {:.2f} dBi.'.format(max_gain_db)
            max_gain_db_slist.append(max_gain_db_str)
            fig = plt.figure(figsize=(fontsize, fontsize))
            plot_title = (
                'Frequency: ' + str(band[0]) + ' MHz. ' + max_gain_db_str
            )
            fig.suptitle(plot_title, fontsize=fontsize)
            ax = plt.subplot(111, polar=True, projection='polar')
            ax.set_rlim(min(rho[key]), max(rho[key]) + rlim_shift)
            # set where the zero location is
            ax.set_theta_zero_location('N')
            # set the angle to be increasing clockwise or counterclockwise
            ax.set_theta_direction(-1)
            ax.tick_params(axis='y', which='major', labelsize=10)

            # long/right antenna is always red, and is always in second file
            temp1 = rho[key][360:720]
            temp2 = rho[key][0:360]
            buf1 = [0]*360
            buf2 = [0]*360

            # a hack for C250 planet files where the angle is rotated by 90
            # degree
            if key == 'horizontal' and config.C250_FLAG is True:
                rotation_offset = config.C250_ROTATION_OFFSET
                for l in range(0, 360):
                    buf1[(l + rotation_offset) % 360] = temp1[l]
                    buf2[(l + rotation_offset) % 360] = temp2[l]
                temp1 = buf1
                temp2 = buf2

            if options.rotation_offset > 0:
                rotation_offset = options.rotation_offset
                for l in range(0, 360):
                    buf1[(l + rotation_offset) % 360] = temp1[l]
                    buf2[(l + rotation_offset) % 360] = temp2[l]
                temp1 = buf1
                temp2 = buf2

            if self.single_file_flag is True:
                plt.polar(
                    theta,
                    temp2,
                    label='Antenna 1',
                    color='blue',
                    ls='-',
                    lw=lw
                )
            else:
                plt.polar(
                    theta,
                    temp2,
                    label='Antenna 1',
                    color='blue',
                    ls='-',
                    lw=lw
                )
                plt.polar(
                    theta,
                    temp1,
                    label='Antenna 2',
                    color='red',
                    ls='--',
                    lw=lw
                )
                # short/left is always blue

            # not working well with python 2.7
            if options.show_legend is True:
                plt.legend(loc=3)
            tick_stop = max_gain_db + tick_stop_shift
            #tick_spacing = max(1, (tick_stop - tick_start)/5)
            tick_range = np.arange(
                np.floor(tick_start),
                np.ceil(tick_stop)+0.1,
                np.floor(tick_spacing)
            )

            ax.set_yticks(tick_range)
            # counter is used to label every other ticks
            counter = 0
            # only show every other ticks
            tick_label = []
            for x in tick_range:
                if counter % 2 == 1:
                    tick_label.append('%1.1f dBi' % x)
                    counter += 1
                else:
                    if tick_spacing == 1:
                        tick_label.append('%1.1f dBi' % x)
                    else:
                        tick_label.append('')
                    counter += 1

            # show full ticks
            tick_label_full = []
            for x in tick_range:
                tick_label_full.append('%1.1f dBi' % x)
            ax.set_yticklabels(tick_label_full)
            if save_file:
                file_path = dir_path[path_counter] + file_format + '/'
                if not os.path.exists(file_path):
                    os.makedirs(file_path)

                output_name = (
                    dir_path[0] + file_format + '/' + file_name_prefix
                    + key + '_' + str(band[0]) + '.' + file_format
                )
                plt.savefig(output_name, format=file_format)
                print(
                    '{} file saved at {}'.format(file_format, output_name)
                )

            if options.show_fig:
                plt.draw()

        if options.show_fig:
            plt.show()
        plt.close(fig)

def main():
    pyap = Pyap()
    pyap.wrapper(sys.argv)


if __name__=='__main__':
    sys.exit(main()) # pragma: no cover
