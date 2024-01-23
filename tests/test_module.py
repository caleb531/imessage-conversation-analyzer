#!/usr/bin/env python3
"""test characteristics of the ica module"""
import unittest

import ica

case = unittest.TestCase()


def test_module_import() -> None:
    """should import ica package successfully"""
    case.assertTrue(ica)
