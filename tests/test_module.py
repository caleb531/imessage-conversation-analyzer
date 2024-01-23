#!/usr/bin/env python3

import unittest

import ica

case = unittest.TestCase()


def test_module_import() -> None:
    """should import ica package successfully"""
    case.assertTrue(ica)
