# --------------------------------------------------------------------------------------
# Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
# --------------------------------------------------------------------------------------
"""Console command that checks the health of NVMe drive then displays result.

.. highlight:: none

Verifies the NVMe drive health by running the short self-test diagnostic, checking the SMART
attributes for errors and log page 6 for prior self-test failures.

If nvme is not specified then all NVMe drives are checked.

Log files are saved to the working directory under checknvme.

.. note::
   This command must be run as Administrator on Windows OS.

Command Line Parameters
    --nvme, -n      Integer NVMe device number, can be found using listnvme.
    --extended, -x  Run the extended self-test, takes much longer than default short self-test.

**Example**

This example checks the health of NVMe 0.

.. code-block:: python

   checknvme  --nvme 0

* `checknvme report (report.pdf) <https://raw.githubusercontent.com/jtjones1001/nvmetools/2ff9f4c3f2c6b7d41f57f01e299c6272fef21994/docs/examples/checknvme/report.pdf>`_
* `checknvme dashboard(dashboard.html) <https://htmlpreview.github.io?https://github.com/jtjones1001/nvmetools/blob/2ff9f4c3f2c6b7d41f57f01e299c6272fef21994/docs/examples/checknvme/dashboard.html>`_

.. warning::
   The Windows OS driver has a bug where the self-test diagnostic fails if rerun within 10 minutes of a prior
   self-test diagnostic.  The workaround is to wait at least 10 minutes before rerunning a diagnostic.  This
   behavior does not occur in Linux or WinPE.
"""  # noqa: E501
import argparse
import logging
import os
import platform
import shutil
import sys

import nvmetools.support.console as console
from nvmetools.apps.nvmecmd import Selftest
from nvmetools.support.conversions import is_windows_admin
from nvmetools.support.info import Info
from nvmetools.support.log import start_logger
from nvmetools.support.report import create_dashboard


class _NoWinAdmin(Exception):
    def __init__(self):
        self.code = 71
        self.nvmetools = True
        super().__init__(" This command must be run as Windows administrator.")


class _FailedToRun(Exception):
    def __init__(self):
        self.code = 100
        self.nvmetools = True
        super().__init__(" Self-test failed to run, possible OS error, wait 10 minutes and try again.")


def _parse_arguments():
    """Parse input arguments from command line."""
    parser = argparse.ArgumentParser(
        description=check_nvme.__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-n", "--nvme", type=int, help="NVMe to read, reads all if not specified", metavar="#")
    parser.add_argument("-x", "--extended", help="run extended self-test")

    return vars(parser.parse_args())


def check_nvme(nvme=None, extended=False):
    """Checks the health of NVMe drive.

    Verifies the NVMe drive health by running the short self-test diagnostic, checking the SMART
    attributes for errors and log page 6 for prior self-test failures.

    If nvme is not specified then all NVMe drives are checked.

    Log files are saved to the working directory under checknvme.
    """
    try:
        directory = os.path.join(os.path.abspath("."), "checknvme")

        if os.path.exists(directory):
            shutil.rmtree(directory)
        os.makedirs(directory, exist_ok=False)

        log = start_logger(directory, logging.INFO, "checknvme.log", False)

        if platform.system() == "Windows" and not is_windows_admin():
            raise _NoWinAdmin()

        log.info(f" Logs: {directory}", indent=False)
        all_nvme_info = {}
        start_nvme = None

        if nvme is None:
            base_info = Info(nvme="*", directory=directory)
            os.remove(os.path.join(directory, "nvme.info.json"))
            os.remove(os.path.join(directory, "read.summary.json"))
            if os.path.exists(os.path.join(directory, "nvmecmd.trace.log")):
                os.remove(os.path.join(directory, "nvmecmd.trace.log"))

            for nvme_entry in base_info.info["_metadata"]["system"]["nvme list"]:
                nvme_number = nvme_entry.split()[1]

                log.info(f" Start: NVMe {nvme_number} self-test", indent=False)
                selftest = Selftest(nvme=nvme_number, directory=directory, extended=False)

                if selftest.data["return code"] == 0:
                    result = "PASSED"
                else:
                    result = "FAILED"
                    if selftest.data["return code"] == 31:
                        raise _FailedToRun()

                log.info(f"        NVMe {nvme_number} self-test {result}", indent=False)

                info_directory = os.path.join(directory, f"nvme{nvme_number}")
                this_info = Info(nvme=nvme_number, directory=info_directory)
                uid = this_info.parameters["Unique Description"]
                all_nvme_info[uid] = this_info

                log.info(f" Read: {uid}", indent=False)

                if start_nvme is None:
                    if nvme is None or nvme == nvme_number:
                        start_nvme = this_info.parameters["Unique Description"]
        else:

            log.info(f" Start: NVMe {nvme} self-test", indent=False)
            selftest = Selftest(nvme=nvme, directory=directory, extended=False)

            if selftest.data["return code"] == 0:
                result = "PASSED"
            else:
                result = "FAILED"
                if selftest.data["return code"] == 31:
                    raise _FailedToRun()

            log.info(f"        NVMe {nvme} self-test {result}", indent=False)

            info_directory = os.path.join(directory, f"nvme{nvme}")
            this_info = Info(nvme=nvme, directory=info_directory)

            start_nvme = this_info.parameters["Unique Description"]
            all_nvme_info[start_nvme] = this_info
            log.info(f" Read: {start_nvme}", indent=False)

        if start_nvme is None:
            raise console.NoNvme(nvme)

        create_dashboard(directory, start_nvme, all_nvme_info)

        sys.exit()

    except Exception as e:
        console.exit_on_exception(e)


def main():
    """Allow command line operation with unique arguments."""
    args = _parse_arguments()
    check_nvme(**args)


if __name__ == "__main__":
    main()
