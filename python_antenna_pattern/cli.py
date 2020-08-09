#!/usr/bin/env python

#  Entry point for default function. If executed directly, use the default directory path
from python_antenna_pattern.core import AntennaPattern 
from python_antenna_pattern.core import read_name_list 
from optparse import OptionParser
from argparse import ArgumentParser
import sys

try:
    import config
except ImportError:
    import python_antenna_pattern.config as config

class Pyap:
    def __init__(self, file_list=''):
        self.single_file_flag = False
        self.parser = OptionParser()
        self.argparser = ArgumentParser()
        
        self.parser.add_option(
            '-v', '--verbose', action='store_true', dest='verbose', default=False, 
            help='generates all information [default: %default]'
        )
        self.parser.add_option(
            '-s', '--show-fig', action='store_true', dest='show_fig', default=False, 
            help='Show figure (will pause after each figure is generated) [default: %default]'
        )
        self.parser.add_option(
            '-g', '--show-legend', action='store_true', dest='show_legend', default=False, 
            help='Show legend [default: %default]'
        )
        # TODO: deprecate file list approach, simply use input file directory
        self.parser.add_option(
            '-l', '--file-list', action="store", type='string', dest='file_list', 
            default=config.DEFAULT_FILE_LIST,
            help='Use specified file that lists the location of '
                 'the planet files [default: %default]'
        )
        self.parser.add_option(
            '-f', '--file', action='store', type='string', dest='filename', default=None,
            help='Use specified file to plot antenna pattern [default: %default]'
        )
        self.parser.add_option(
            '-r', '--rotation-offset', type='int', dest='rotation_offset', default=0,
            help='Rotational offset when plotting the polar pattern [default: %default]'
        )
        self.parser.add_option(
            '-d', '--directory', type='string', dest='directory', 
            default='python_antenna_pattern/data/test_dir',
            help='Plot the files in the specified directory [default: %default]'
        )
        self.parser.add_option(
            '-F', '--filetype', choices=['eps', 'pdf'], dest='filetype', default='pdf', 
            help='file type of the output figure, either pdf or eps [default: %default]'
        )
        self.parser.add_option(
            '--fontsize', type='int', dest='fontsize', default='7', 
            help='Font size in the legend and the title [default: %default]'
        )
        self.parser.add_option(
            '-n', '--file-name-prefix', type='string', 
            dest='file_name_prefix', default='SCRN_',
            help='prefix of the filename [default: %default]'
        )
        

    def polar_pattern(self, arg_input=''):
        #from config import *
        # manually adjust parameters
        import shlex 
        (options, args) = self.parser.parse_args(shlex.split(arg_input))

        self.plot_pattern(options)

    
    def wrapper(self, argv):
        (options, args) = self.parser.parse_args()
        self.plot_pattern(options)



    # TODO: use optparse to add optinos rather than using config.py
    def plot_pattern(self, options, save_file=True):
        import python_antenna_pattern.config as config
        import numpy as np
        import matplotlib.pyplot as plt
        import os
        import glob
        fontsize = options.fontsize
        file_name_prefix=options.file_name_prefix
        file_format=options.filetype
        if options.directory is not None:
            import os
            path = '{}/{}/*.txt'.format(os.getcwd(), options.directory)
            src_files = glob.glob(path)
            if len(src_files) == 0:
                print('No files in directory {}'.format(path))
                path = '{}/*.txt'.format(options.directory)
                print('trying in directory {}'.format(path))
                src_files = glob.glob(path)
                if len(src_files) == 0:
                    print('No files found')
                    return
            print('Converting files mathcing {}'
                  ' (non-recursive)'.format(path))

            print('Files to be converted: {}'.format(src_files))
        elif options.filename is not None:
            print('Converting file {}'.format(options.filename))
            src_files = [options.filename]
        elif options.file_list is not None:
            print('Converting files in the following list: {}'.format(options.file_list))
            src_files = read_name_list(options.file_list)
        else:
            print('Please provide a file name, list of files, or a directory')
            return 1

        degree = np.arange(0, 360, 1)
        theta = degree*2*np.pi/360
        p_list = []
        file_name = []
        dir_path = []
        band = []
        clipping = config.MAX_GAIN_CLIPPING
        loc=config.LOC
        tick_start=config.TICK_START
        tick_stop=config.TICK_STOP
        tick_spacing=config.TICK_SPACING
        tick_stop_shift=0.2
        lw=2
        rlim_shift=4

        for file_path in src_files:
            antenna_pattern = AntennaPattern()
            # parse the antenna gains by cut or by antenna
            antenna_pattern.parse_data(file_path, config.PARSE_BY)
            split_name = file_path.rsplit('/')
            file_name = split_name[-1]
            # temp now is a dictionary of the two antenna pattern in a file
            p_list.append(antenna_pattern)

            #b = parse_freq_band(file_name)
            band.append(antenna_pattern.frequency)
            # all but last element in the list
            dir_path.append('/'.join(split_name[0:-1]) + '/')

        if len(src_files) > 2:
            print('Currently does not support more than a pair of file in file_list')
            raise

        if len(src_files) < 2:
            self.single_file_flag = True

        if len(band) > 1:
            print('frequency band list: ', band)
            if band[0] != band[1]:
                print('freq band not match: ', band)
                #raise
    
        max_gain_db_slist = []
        rho = {}
        counter = 0
        path_counter = 0
        max_list = []
    
        for pval in p_list:
            labels = list(pval.pattern_dict.keys()) # in python 3.x keys() return a set-like object
            # clip the small values here
            for i in range(0, 360):
                # clip the horizontal and the vertical vectors
                for key in labels:
                    if pval.pattern_dict[key][i] > clipping:
                        pval.pattern_dict[key][i] = clipping
    
            # the vertical/horizontal antenna patterns across two files, i.e., two antennas, are aggregated here
            # the way we aggregate is that the vertial antenna pattern for the first file, is in rho[0:360] and 
            # the antenna pattern for the second file is in rho[360:720], and so on. 
            # Number of antenna to consider
            for key in list(pval.pattern_dict.keys()):
                if key in rho:
                    rho[key] = np.append(rho[key], pval.max_gain_db - np.asarray(pval.pattern_dict[key]))
                # initialize rho dictionary as empty lists
                else:
                    rho[key] = pval.max_gain_db - np.asarray(pval.pattern_dict[key])
    
        size = 7
        for key in list(pval.pattern_dict.keys()):
            max_gain_db = max(rho[key])
            max_list.append(max_gain_db)
            max_gain_db_str = 'Peak Gain: {:.2f} dBi.'.format(max_gain_db)
            max_gain_db_slist.append(max_gain_db_str)
            fig = plt.figure(figsize=(size, size))
            plot_title = 'Frequency: ' + str(band[0]) + ' MHz. ' + max_gain_db_str
            fig.suptitle(plot_title, fontsize=fontsize)
            ax = plt.subplot(111, polar=True, projection='polar')
            ax.set_rlim(min(rho[key]), max(rho[key]) + rlim_shift)
            # set where the zero location is
            ax.set_theta_zero_location('N')
            # set the angle to be increasing clockwise or counterclockwise
            ax.set_theta_direction(-1)
            ax.tick_params(axis='y', which='major', labelsize=10)
    
            # long/right antenna is always red, and is always in second file??
            temp1 = rho[key][360:720]
            temp2 = rho[key][0:360]
            buf1 = [0]*360
            buf2 = [0]*360
    
            # a hack for C250 planet files where the angle is rotated by 90 degree
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
                plt.polar(theta, temp2, label='Antenna 1', color='blue', ls='-', lw=lw)
            else:
                plt.polar(theta, temp2, label='Antenna 1', color='blue', ls='-', lw=lw)
                plt.polar(theta, temp1, label='Antenna 2', color='red', ls='--', lw=lw)
                # short/left is always blue
            
            # not working well with python 2.7
            if options.show_legend is True:
                plt.legend(loc=3)
            tick_stop = max_gain_db + tick_stop_shift
            #tick_spacing = max(1, (tick_stop - tick_start)/5)
            tick_range = np.arange(np.floor(tick_start),
                                   np.ceil(tick_stop)+0.1,
                                   np.floor(tick_spacing) )

            ax.set_yticks(tick_range)
            # counter is used to label every other ticks
            counter = 0
            # only show every other ticks
            tick_label = []
            try:
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
            except IndexError as e:
                print('Index error occur during assigning tick labels') 
                raise
            # show full ticks
            tick_label_full = []
            for x in tick_range:
                tick_label_full.append('%1.1f dBi' % x)
            ax.set_yticklabels(tick_label_full)
            if save_file:
                try:
                    file_path = dir_path[path_counter] + file_format + '/'
                    if not os.path.exists(file_path):
                        os.makedirs(file_path)

                    output_name = (dir_path[0] + file_format + '/' + file_name_prefix
                                   + key + '_' + str(band[0]) + '.' + file_format)
                    plt.savefig(output_name, format=file_format)
                    print('{} file saved at {}'.format(file_format, output_name)) 
                except PermissionError:
                    print('No permission to create a director {}'.format(output_name))
                    raise
                except:
                    print('Exception raise during file saving')
                    raise

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
