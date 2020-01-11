import unittest

from main import *

class TestREST(unittest.TestCase):
    def test_build_datapoints(self):
        names = [
            ('Harshil', 'Cherukuri'),
            ('David', 'DiSimone'),
            ('Michael', 'Froncek'),
            ('Matthew', 'Furst'),
            ('Chinua', 'Jones'),
            ('Leo', 'Kastenberg'),
            ('Donald', 'Lampe-Vorgity'),
            ('Shwan', 'Lee'),
            ('Jeffrey', 'Li'),
            ('Sean', 'Maas'),
            ('Tyler', 'Morse'),
            ('Ian', 'Park'),
            ('John', 'Ridge'),
            ('Daniel', 'Robitzski'),
            ('Samuel', 'Shrem'),
            ('Alec', 'Wrana'),
        ]
        weapon = "Epee"
        datapoints = build_datapoints(names, weapon)

    def test_get_fencer(self):
        names = [
            ('Harshil', 'Cherukuri'),
            ('David', 'DiSimone'),
            ('Michael', 'Froncek'),
            ('Matthew', 'Furst'),
            ('Chinua', 'Jones'),
            ('Leo', 'Kastenberg'),
            ('Donald', 'Lampe-Vorgity'),
            ('Shwan', 'Lee'),
            ('Jeffrey', 'Li'),
            ('Sean', 'Maas'),
            ('Tyler', 'Morse'),
            ('Ian', 'Park'),
            ('John', 'Ridge'),
            ('Daniel', 'Robitzski'),
            ('Samuel', 'Shrem'),
            ('Alec', 'Wrana'),
        ]
        info = get_fencer_info(names)
        print(info[0])

    def test_get_latest_result(self):
        fid = 134277
        data = get_latest_rating(fid, "Epee")

if __name__ == '__main__':
    unittest.main()
