""" stream_magic remote test suite
    Limit tests to those not requiring access to an actual device.
"""
import sys
sys.path.append("..")
from stream_magic import discovery


def test_object_instance():
    # test object creation
    sm_object = discovery.StreamMagic()
    assert isinstance(sm_object, discovery.StreamMagic)
