#!/usr/bin/env python
#  ----------------------------------------------------------------
# Copyright 2016 Cisco Systems
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ------------------------------------------------------------------

import os
import datetime
from secrets import USERNAME, PASSWORD
import ipaddress
import xlsxwriter
import pandas as pd
import constants
from eman import Eman
from logging_config import configure_logger

LOGPATH = os.path.abspath(os.curdir) + "/logs/viptela_onboarding.log"
LOGGER = configure_logger(__name__, LOGPATH)


class UserOnboard:
    """ Pulls from CSV file to create subnets for a specific addressblock for
    use in assigning for viptela CVO users. If username and password are not
    passed via command line, they mus tbe present in a file called secrets.py
    in the same directory as onboarding.py in the following format:

    USERNAME = "username"
    PASSWORD = "password"

    Please provide absolute path to the csv file.

    An xlsx called vedge_onboarding-<current date>.xls is created in the same
    directory as onboarding.py with the results.
    """

    def __init__(self, username="", password=""):
        self.username = username
        self.password = password
        self.csv_file = csv_file

    def read_csv(self):
        """
        Reads the CSV file, row by row and creates the subnets, scope and dhco
        interfaces accordingly.

        :return:
        """
        LOGGER.info(
            "\n"
            "+++++++++++++++++++++++++++++\n"
            "Starting new on-boarding run.\n"
            "+++++++++++++++++++++++++++++\n"
        )
        # get username/password for address management access
        if self.username and self.password:
            am = Eman(self.username, self.password)
        else:
            am = Eman(USERNAME, PASSWORD)

        # Checking Authentication with EMAN
        self.check_eman_auth(am)

        # Open xlsx workbook for editing
        workbook, worksheet = self.openxlsx()

        # read dataset from csv file into data with pandas
        data = pd.read_csv(self.csv_file)
        outputrow = 2
        # read and act upon each row in dataset
        for index, row in data.head(n=1000).iterrows():
            hostname = row["csv-host-name"]
            LOGGER.info("\n\n" f"++++++++++++++{hostname}+++++++++++++++\n")
            region = row["REGION"].upper()
            if pd.isnull(row["csv-deviceIP"]):
                subnet = self.create_subnet(am, region, hostname)
                if subnet == 1:
                    continue
                gateway = str(ipaddress.ip_address(subnet.rsplit("/")[0]) + 1)
            else:
                gateway = row["csv-deviceIP"].strip()
                subnet = f"{str(ipaddress.ip_address(gateway) - 1)}/29"
                subnet = self.create_subnet(
                    am, region, hostname, existing_subnet=subnet
                )

            if subnet == 1:
                gateway = "Failed Subnet"
            else:
                # create scope for subnet...5 ip's
                errors = self.create_scope(am, hostname, subnet, gateway, region)
                if errors == 1:
                    gateway = "Failed Scope"
                errors = self.add_interfaces(am, hostname, gateway)
                if errors == 1:
                    gateway = "Failed Interface"

            # write info to xlsx spreadsheet
            worksheet.write(f"B{outputrow}", hostname)
            worksheet.write(f"A{outputrow}", gateway)
            worksheet.write(f"C{outputrow}", f"{gateway}/29")
            worksheet.write(f"D{outputrow}", gateway)
            outputrow += 1

        LOGGER.info(
            "\n"
            "++++++++++++++++++++++++++++++\n"
            "Completed new on-boarding run.\n"
            "++++++++++++++++++++++++++++++\n"
        )

        self.closexlsx(workbook)

    def check_eman_auth(self, am):
        """
        Makes a dummy call to Eman to determine if given credentials ar valid.

        Args:
            am: Function call to Eman

        Returns: Nothing if valid. Halts if not

        """
        LOGGER.info("verifying Eman authentication")
        try:
            am.find_interfaces(interface_name="AnyDevice")
        except:
            LOGGER.info(f"User in not authorized for EMAN. Exiting.")
            exit()

    def cleanup_ab(self, am, existing_subnet, hostname):
        """
        Removes a specified scope and subnet

        Args:
            am: Function call to Eman
            existing_subnet: determined from gateway listed in csv-deviceIP
            hostname: hostname determined from csv-host-name and used as
                      scope name.

        Returns: Nothing

        """
        LOGGER.info(f"Deleting existing scope: {hostname}")
        results = am.del_scope(hostname)
        LOGGER.info(f"Eman output: {results}")

        LOGGER.info(f"Deleting existing subnet: {existing_subnet}")
        results = am.del_subnet(existing_subnet)
        LOGGER.info(f"Eman output: {results}")

    def create_subnet(self, am, region, hostname, existing_subnet=""):
        """
        Determines if the device already has a subnet and if so, deletes it and
        recreates it. If not, finds the next available /29 block in the given
        address block and creates a new subnet.

        Args:
            am: Function call to Eman
            region: Specified from xlsxfile and used to determine variables
                    from constants.py
            hostname: Name to be used to label subnet, scope and interfaces.
            existing_subnet: Existing subnet specified in csv-deviceIP which
                             should be deleted nd recreated.

        Returns: subnet or errors

        """
        errors = 0
        # determine address block based on region from csv file
        if existing_subnet:
            self.cleanup_ab(am, existing_subnet, hostname)

            subnet, prefix = existing_subnet.rsplit("/")
            try:
                LOGGER.info(f"Re-creating subnet: {existing_subnet}")
                subnet = am.add_subnet(
                    subnet=existing_subnet,
                    prefix=prefix,
                    description=hostname,
                    function="LAN",
                    contact1='"ete-sec"',
                    contact1_type='"Mail Alias"',
                )
                LOGGER.info(f"Eman output: {subnet}")
                return subnet
            except Exception as error:
                LOGGER.info(error)
                errors = 1
                return errors
        else:
            if region in constants.regionsab:
                addressblock = constants.regionsab.get(region)
                try:
                    LOGGER.info(f"Creating new subnet")
                    subnet = am.add_subnet(
                        address_block=addressblock,
                        prefix="29",
                        description=hostname,
                        function="LAN",
                        contact1='"ete-sec"',
                        contact1_type='"Mail Alias"',
                    )
                    LOGGER.info(f"Eman output: {subnet}")
                    return subnet
                except Exception as error:
                    LOGGER.info(error)
                    errors = 1
                    return errors

    def create_scope(self, am, hostname, subnet, gateway, region):
        """
        Creates scope for the specified subnet. s
        Args:
            am: Function call to Eman
            hostname: Name to be used to label subnet, scope and interfaces.
            subnet: subnet where scope should be created
            gateway: IP address of gateway interface
            region: region from xlsxfile to determine call manager details
                    from constants.py

        Returns: Success or Error

        """

        print(f"subnet = {subnet}")
        scope_name = hostname
        description = hostname
        range = am.get_range(subnet, 5)
        ranges = f"{range[0]}:{range[1]}"

        dhcpserver = constants.dhcpservers.get(region)

        policy = constants.regionspolicys.get(region)

        callmanager = constants.callmanagers.get(region)
        errors = 0
        try:
            LOGGER.info(f"Creating scope for {hostname}")
            scope = am.add_scope(
                scope_name=scope_name,
                description=description,
                subnet=subnet,
                ranges=ranges,
                policy=policy,
                selectiontags=("IPPhones", "OtherDevices"),
                dhcpserver=dhcpserver,
                defaultrouter=gateway,
                callmanager=callmanager,
            )
            LOGGER.info(f"Eman output: {scope}")
            return "success"
        except Exception as error:
            LOGGER.info(error)
            errors = 1
            return errors

    def add_interfaces(self, am, hostname, gateway):
        """
        Creates gateway and dhcp interfaces.

        Args:
            am: Function call to Eman
            hostname: Name to be used to label subnet, scope and interfaces.
            gateway: IP address of gateway interface

        Returns: Errors

        """
        errors = 0
        try:
            LOGGER.info(f"Adding gateway interface: {gateway}")
            interface = am.add_interface(
                hostname,
                hostname=hostname,
                ip=gateway,
                ptr="Y",
                status="Active",
                description=hostname,
                contact1='"ete-sec"',
                contact1_type='"Mail Alias"',
            )
            LOGGER.info(f"Eman output: {interface}")
        except Exception as error:
            LOGGER.info(error)
            errors = 1

        interfaceip = ipaddress.ip_address(gateway)

        count = 1
        while count <= 5:
            interfaceip = interfaceip + 1
            try:
                LOGGER.info(f"Adding dhcp interface: {interfaceip}")
                interface = am.add_interface(
                    f"{hostname}-ip{count}",
                    hostname=f"{hostname}-ip{count}",
                    ip=interfaceip,
                    ptr="Y",
                    status="Active",
                    description=f"{hostname}-ip{count}",
                    contact1='"ete-sec"',
                    contact1_type='"Mail Alias"',
                )
                LOGGER.info(f"Eman output: {interface}")
            except Exception as error:
                LOGGER.info(error)
                errors = 1
            count += 1
        return errors

    def openxlsx(self):
        """
        Creates a spreadsheet in the working directory to provide
        details.

        Returns: workbook, worksheet

        """
        nowdate = datetime.datetime.now()
        dirpath = os.getcwd()
        xlsxpath = f"{dirpath}/vedge_onboarding-{nowdate}.xlsx"
        workbook = xlsxwriter.Workbook(xlsxpath)
        worksheet = workbook.add_worksheet()
        worksheet.write("A1", "csv-deviceIP")
        worksheet.write("B1", "csv-host-name")
        worksheet.write("C1", "/100/irb1/interface/ip/address")
        worksheet.write("D1", "//system/system-ip")

        return workbook, worksheet

    def closexlsx(self, workbook):
        workbook.close()
#
#
# if __name__ == "__main__":
#     # for testing
#     print("\n++++++++++++++++++++++")
#     print("Starting New Test Run!")
#     print("++++++++++++++++++++++\n")
#     print("\n++++++++++++++++++")
#     print("Test Run Complete!")
#     print("++++++++++++++++++\n")
