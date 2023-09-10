from pathlib import Path
from pcb2gcode.tproc import Processor

import pytest


def test_simple_file():
    """ Test real life situation with a test PCB """
    p = Processor()

    # Load from this folder
    this_path = Path(__file__).resolve().parent
    tproc_test_file = this_path / "test.tproc"

    p.process_file(tproc_test_file)

    pre = p.expand("@preamble")

    print("XXX", pre)

    assert p


