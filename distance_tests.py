import maping
import pandas as pd
import numpy as np
import unittest

class TestofTests(unittest.TestCase):
    """test"""
    def test_1(self):
        pass
        for i in range(10):
            with self.subTest():
                self.assertEqual(i,i)
        self.assertEqual(3,1)

class DistanceTests(unittest.TestCase):
    """_summary_
    Test Suite for testing distance calculation.
    to run:
    python -m unittest distance_tests.DistanceTests
    """
    def setUp(self):
        pass
        self.df:pd.DataFrame = pd.read_csv("./tests/regular.csv")
    def test_SyntheticData(self):
        for index,row in self.df.iterrows():
            a = maping.Point(row['xa'],row['ya'])
            b = maping.Point(row['xb'],row['yb'])
            res = maping.Point(row['xs'],row['ys'])
            
            distance_a = row['a']
            distance_b = row['b']
            
            print(row)
            
            with self.subTest(msg=f"{index}th Test: "):
                result: maping.Point = maping.calculate_position(a,b,res,distance_a, distance_b)
                print(f"Expected: x = {res.x},y = {res.y},\nResult: x = {result.x}, y = {result.y}")
                
                self.assertAlmostEqual(result.x,res.x,)
                self.assertAlmostEqual(result.y,res.y)

