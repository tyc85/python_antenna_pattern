import unittest
import python_antenna_pattern.core as core
from python_antenna_pattern.pyap import Pyap

class TestParser(unittest.TestCase):
    def setUp(self):
        self.header_str = (
            'NAME   B800A065-18-0E\n'
            'MAKE    Amphenol\n'
            'FREQUENCY   851\n'
            'H_WIDTH 65\n'
            'V_WIDTH 11.2\n'
            'FRONT_TO_BACK   -30.1\n'
            'GAIN    13.6 dBd\n'
            'TILT    ELECTRICAL\n'
            'COMMENT None\n'
        )
        self.test_file_list = [
            ('python_antenna_pattern/data/file_list1', 851),  # sinlge planet file 
            ('python_antenna_pattern/data/file_list2', 1960), # a pair of planet file
            ('python_antenna_pattern/data/file_list4', 1960), # four planet files
        ]
   
    def test_e2e_pyap_result(self):
        pyap = Pyap('data/file_list2')      
        pyap.polar_pattern()

    def test_directory_option(self):
        pyap = Pyap()      
        pyap.parser.set_defaults(directory='data/test_dir')
        
        pyap.polar_pattern()


    def test_parsing_from_file_list(self):
        # parse by antenna by default. parse by cut not tested yet
        for i in range(0, 2):
            file_name_list = core.read_name_list(self.test_file_list[i][0])
            antenna_pattern = core.AntennaPattern()
            for file_name in file_name_list: 
                antenna_pattern.parse_data(file_name, 'ant') 
                self.assertEqual(antenna_pattern.frequency, 
                                 self.test_file_list[i][1])
    
    def test_header_parsing(self):
        antenna_pattern = core.AntennaPattern()
        for line in self.header_str.split('\n'):
            antenna_pattern.parse_line(line)
            
        self.assertEqual(antenna_pattern.frequency, 851)
        self.assertEqual(antenna_pattern.max_gain_db, 13.6)
        

if __name__=='__main__':
    unittest.main()

