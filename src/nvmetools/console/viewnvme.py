# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
"""Console command that displays NVMe drive information in html format.

Reads NVMe drive information using the Admin Commands: Get Log Page, Get Feature, Identify
Controller, and Identify Namespace. A few parameters, such as PCIe location and link info, are read
from the OS.

**Command Line Parameters**
    --nvme, -n      Integer NVMe device number, can be found using listnvme.

The following log files are saved to the working directory:

    - readnvme.log contains the console output
    - nvme.info.json contains the NVMe parameters in json format
    - info.html is a html format report
    - nvmecmd.trace.log and trace.log are trace file for debug if something goes wrong
    - read.summary.json contains information on the Admin commands used

**Example**

    This example reads the information of NVMe 0

    .. highlight:: none
    .. code-block:: python

        viewnvme  --nvme 0

    * `Example html output (info.html) <https://raw.githubusercontent.com/jtjones1001/nvmetools/2ff9f4c3f2c6b7d41f57f01e299c6272fef21994/docs/examples/readnvme_hex/readnvme.log>`_

"""  # noqa: E501
import argparse
import logging
import os
import sys

from nvmetools.support.console import exit_on_exception
from nvmetools.support.info import Info
from nvmetools.support.log import start_logger
from nvmetools.support.report import create_info_dashboard

def _parse_arguments():
    """Parse input arguments from command line."""
    parser = argparse.ArgumentParser(
        description=read_nvme.__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-n", "--nvme", type=int, default=0, help="NVMe drive to read", metavar="#")
    return vars(parser.parse_args())


def read_nvme(nvme=0, as_list=False, as_hex=False, as_all=False, describe=False, create_pdf=False, verbose=False):
    """Display and log NVMe information.

    Reads NVMe information using the nvmecmd utility. This utility creates a file named nvme.info.json
    with the entire set of information. This script reads nvme.info.json and displays the NVMe
    information as an html dashboard (info.html).
    """
    try:
        directory = os.path.join(os.path.abspath("."),"viewnvme")
        os.makedirs(directory, exist_ok=True)
        start_logger(directory, logging.INFO, "viewnvme.log")
        info = Info(nvme=nvme,directory=directory)
        create_info_dashboard(info, directory)
        sys.exit()

    except Exception as e:
        exit_on_exception(e)


def main():
    """Allow command line operation with unique arguments."""
    args = _parse_arguments()
    read_nvme(**args)


if __name__ == "__main__":
    main()
