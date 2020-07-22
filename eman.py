#!/usr/bin/env python
"""
| Created by: Rob Massingill
| Modefied by Tyler Bruno (tybruno)
| Creation date Date:       Feb. 18, 2019
| Version:    1.2
|
| Use this module to connect to a specified vcenter and
| create a base vm with no os.
"""

import os
import logging
import ipaddress
import re
import subprocess
from logging_config import configure_logger

LOGPATH = os.path.abspath(os.curdir) + "/logs/ete_lib.log"
LOGGER = configure_logger(__name__, LOGPATH)

class UserAuthenticationError(Exception):
    """Exception that will be thrown when user fails to authenticate with AM"""


class UnableToReserveError(Exception):
    """Exception that will be raised when a address block, subnet, or interface can not be reserved"""


class UnableToFindError(Exception):
    """Exception that is raised when unable to find ip address,interface, subnet, address block, .etc"""


# pylint: disable-msg=R0904
class Eman:
    """
    Attributes:
        username: User with rights to make changes in Eman-am or eman-cli
        password: Password for expected user
    """

    def __init__(self, username, password):
        self.username = username
        self.password = password

    def send_command(self, command):
        """
        Takes variables in to the classes and executes a call to eman-am.pl
        :param: command that will be sent to eman
        :return: Success or Fail and Error

        """
        perl_script_location = (
            os.path.dirname(os.path.realpath(__file__)) + "/eman-am.pl"
        )
        if not os.path.exists(perl_script_location):
            perl_script_location = os.path.relpath(
                "../am_wrapper/am_wrapper/eman-am.pl", os.curdir
            )

        header = f'{perl_script_location} -username={self.username} \
        -password="{self.password}"'

        LOGGER.debug(f"command: {command}")

        full_command = f"perl {header} {command}"

        os.environ["PERL_LWP_SSL_VERIFY_HOSTNAME"] = "0"
        process = subprocess.Popen(
            full_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
        )
        output = str(process.stdout.read().decode().strip("\n").lstrip().rstrip())
        error = str(process.stderr.read().decode().strip("\n").lstrip().rstrip())
        if "Unauthorized" in error:
            raise UserAuthenticationError(error)

        if output:
            LOGGER.info(command)
            return output
        else:
            LOGGER.error(command)
            return error

    @staticmethod
    def _generate_command(**flags):
        """
        Generates the command string with the necessary flags that will be ran by the eman perl script

        :param flags: (dict) flags dictionary contains the name of the flag as the key and the flag
        variable as the value. (i.e. {'Addressblock':'10.34.36.64/27'}
        :return: command string that will be ran in eman. (e.g. '-function=next-avail -subnet=10.34.182.128/27
        -type=I -return=1 -length=30 -function=int-add -name=script-test2
        -ipaddress=10.34.182.131 -multihomed=N -PTR=N -Descr=""')

        """
        command = ""
        for flag_name, flag_variable in flags.items():
            if flag_variable and not "" or "":
                if type(flag_variable) is tuple:
                    multiflag_variable = ""
                    items = len(flag_variable) - 1
                    count = 0
                    while count <= items:
                        multiflag_variable = (
                            multiflag_variable + f"'{flag_variable[count]}'"
                        )
                        if count != items:
                            multiflag_variable = multiflag_variable + ","
                        count += 1
                    command += f"-{flag_name}={multiflag_variable} "
                else:
                    command += f"-{flag_name}={flag_variable} "
        return command

    # pylint: disable-msg=R0913
    def add_address_block(
        self,
        address_block,
        function="",
        location="inherit",
        route_point="inherit",
        description="",
        status="Active",
        block_type="Primary",
        lab="",
        contact1="",
        contact1_type="",
    ):
        """
        Add an address block

        example: add_address_block(address_block="10.34.182.128/26",
        location='"San Jose"',status="Active",route_point="RTP",
        function="LAN",description='"This is a address block addition test by tybruno"',
        contact1="tybruno",contact1_type='Employee')

        Comma separate multiple values for an argument,
        and put parenthesis around any value that contains
        a space:

        e.g.
        location= 'Amsterdam,"San Jose",RTP'

        :param address_block: (str) network address of an address block you want to
        add (e.g. 171.23.41.0/24 or 2001:420::1:0:0:0:0/64)

        :param function: (str) function of address block (e.g. Access, Any, DMZ-Lab,
        “Data Center”, “Data Center - ACI”, Desktop,
        ENG-DC, External, GBP-DC, Guest, LAN, Lab,
        “National ISDN”, Network-Core, Partner, SimDMZ, UCV-Endpoint, WAN, Wireless)

        :param location: (str) location of address block (e.g. ANZ, Allen, Amsterdam,
        Any, Atlanta, Atlanta-SA, Austin, Bakersfield,Boston, “Boulder CO”,
        “Boxboro Site 1”, “Boxboro Site 2”, Brussels, Canada, Chatswood, Chelmsford,
        Chicago, China, Dallas, Herndon, ”Hong Kong”, India, Irvine, Japan, Johannesburg,
        Knoxville, TN, Korea, London, Lysaker, Manama, Milan, Milipitas, NEDC, NYC, Netanya,
        Ottawa, Petaluma, RTP, Richardson, ”SE Asia”, ”San Jose”, Santa, Barbara, Seattle, ”Shanghai IDC”,
        Sydney, Tokyo, Toronto)

        :param route_point: (str) route point of address block (e.g. Allen, Amsterdam,
        Any, Atlanta-SA, Bangalore, Boxborough,Chelmsford, DRT, “Hong Kong“, Irvine,
        Johannesburg, Milan, None, RCDN4, RCDN9, RTP, “San Jose“, Shanghai, Singapore,
        Sydney, “Tel Aviv“, Tokyo, VNC)

        :param description: (str) description of address block
        :param status: (str) status of address block (e.g. Active, Inactive,
        "Do not use", Reserved, Returned, Unused)

        :param block_type: (str) type of subnet. Default: 'Primary'
        :param lab: Lab ID to reference from the Lab Registration Tool.
        :param contact1: (str) contact for the subnet
        :param contact1_type: (str) contact type for subnet (e.g. Employee, Mail Alias, Other,
        “Local Contact (on-site)”,“Generic User”, Metric, “Epage Alias”, “Support Group”)
        :return:
        """
        flags = {
            "function": "address-block-add",
            "AddressBlock": address_block,
            "Function": function,
            "Location": location,
            "Routepoint": route_point,
            "Descr": description,
            "Status": status,
            "Type": block_type,
            "lab": lab,
            "Contact1": contact1,
            "Contact1type": contact1_type,
        }
        command = self._generate_command(**flags)

        result = self.send_command(command=command)

        LOGGER.info("add_address_block: %s", result)
        if "ERROR" in result:
            raise UnableToReserveError(result)
        return result

    # pylint: disable-msg=R0914
    # pylint: disable-msg=R0913
    def add_subnet(
        self,
        address_block="",
        subnet="",
        prefix="",
        function="",
        status="Active",
        subnet_type="Primary",
        description="",
        location="inherit",
        dhcp_server="",
        route_point="inherit",
        area="HQ",
        city='"San Jose"',
        country='"United States"',
        ping_before_offer="Yes",
        trend="Yes",
        failover_backup_percentage="5",
        alert_percent_used="95",
        selection_tags="OtherDevices",
        default_router="",
        call_manager="",
        lab="",
        contact1="",
        contact1_type="",
    ):
        """
        Function that will add a subnet to address management.

        If address block is given and a subnet is not given,
        the function will add the next available subnet in the given address block.

        Comma separate multiple values for an argument,
        and put parenthesis around any value that contains
        a space:

        e.g.
        selection_tags='"HP Printer","IP Phones"'

        Calling method example: add_subnet(subnet='10.34.182.128/26',function="LAN")

        e.g. Reserve any next available subnet in address block

        add_subnet(address_block="10.34.182.128/26")

        :param address_block: (str) address block where the next available subnet will be found
        :param subnet: (str) network address of the subnet you want to find an available address
        :param prefix: (str) provides a custom subnet prefix size for searching for next available
        subnet via addressblock (e.g. 29) default is 126 for ipv6 and 30 for ip4.
        :param function: (str) (required with subnet) function of the subnet block (e.g. Access, Any, DMZ-Lab,
        “Data Center”, “Data Center - ACI”, Desktop, ENG-DC, External, GBP-DC, Guest, LAN, Lab,
        “National ISDN”, Network-Core, Partner, SimDMZ, UCV-Endpoint, WAN, Wireless)

        :param status: (str) status of subnet (e.g. Active, Inactive, "Do not use", Reserved, Returned, Unused)
        :param subnet_type: (str) no description was given in the eman cli tool aboutt this field. Default is "Primary"
        :param description: (str) (optional) description of subnet

        :param location: (str) location of address block (e.g. ANZ, Allen, Amsterdam, Any, Atlanta, Atlanta-SA,
        Austin, Bakersfield, Boston, “Boulder CO”, “Boxboro Site 1”, “Boxboro Site 2”, Brussels, Canada,
        Chatswood, Chelmsford, Chicago, China, Dallas, Herndon, ”Hong Kong”, India, Irvine, Japan, Johannesburg,
        Knoxville, TN, Korea, London, Lysaker, Manama, Milan, Milipitas, NEDC, NYC, Netanya, Ottawa, Petaluma,
        RTP, Richardson, ”SE Asia”, ”San Jose”, Santa, Barbara, Seattle, ”Shanghai IDC”,
        Sydney, Tokyo, Toronto)

        :param dhcp_server: (str) function of subnet (e.g. Access,LAN,WAN)

        :param route_point: (str) route point of address block (e.g. Allen, Amsterdam, Any, Atlanta-SA,
        Bangalore, Boxborough,Chelmsford, DRT, “Hong Kong“, Irvine, Johannesburg, Milan, None, RCDN4,
        RCDN9, RTP, “San Jose“, Shanghai, Singapore,Sydney, “Tel Aviv“, Tokyo, VNC)
        :param area: (str) area subnet is in (e.g. ASIA, BODC, CH, CODC, Canada, “China - PRC”, EUR,
        HQ, JP, Korea, LATAM, None, OZ, RTP, US)
        :param city: (str) city subnet is in (e.g. London,RTP,Austin)
        :param country: (str) country subnet is in
        :param ping_before_offer: (str) 'Yes' to ping ip's in subnet before after. 'No' to not ping before offer.
        :param trend: (str) No description was given for this variable in the eman cli tool.
        :param failover_backup_percentage: (str) FailoverBackupPercentage no information was given for this varirabl
         in the eman cli tool.
        :param alert_percent_used: (str) no descriptoin was given for this variable in the eman cli tool
        :param selection_tags: (str)  e.g. selection_tags='"HP Printer","IP Phones"'
        :param default_router: (str) no definition was given to this variable in the eman cli tool
        :param call_manager: (str) no definition was given to this variable in the eman cli tool
        :param lab: (str) Lab ID to reference from the Lab Registration Tool.
        :param contact1: (str) contact for the subnet
        :param contact1_type: (str) contact type for subnet (e.g. Employee, Mail Alias, Other,
        “Local Contact (on-site)”,“Generic User”, Metric, “Epage Alias”, “Support Group”)

        :return: The added subnet (e.g. '10.34.182.128/26')
        """

        if address_block and not subnet:
            try:
                if not prefix:
                    prefix = "126"
                if find_ipv6_with_subnet(address_block):
                    subnet = self.find_next_available(
                        address_block=address_block,
                        search_type="S",
                        subnet_prefix_length=prefix,
                    )
                    print(subnet)
                else:
                    if not prefix:
                        prefix = "30"
                    subnet = self.find_next_available(
                        address_block=address_block,
                        search_type="S",
                        subnet_prefix_length=prefix,
                    )
            except UnableToFindError as error:
                raise UnableToReserveError(error)

        flags = {
            "function": "subnet-add",
            "subnet": subnet,
            "Function": function,
            "Descr": f'"{description}"',
            "Location": location,
            "DhcpServer": dhcp_server,
            "Area": area,
            "City": city,
            "Country": country,
            "Routepoint": route_point,
            "Status": status,
            "type": subnet_type,
            "PingBeforeOffer": ping_before_offer,
            "Trend": trend,
            "FailoverBackupPercentage": failover_backup_percentage,
            "AlertPercentUsed": alert_percent_used,
            "SelectionTags": selection_tags,
            "DefaultRouter": default_router,
            "CallManager": call_manager,
            "lab": lab,
            "Contact1": contact1,
            "Contact1type": contact1_type,
        }

        command = self._generate_command(**flags)
        LOGGER.info(command)

        result = self.send_command(command)

        LOGGER.info("add_subnet: %s", result)
        ip = ""
        if "Success" in result:
            ip = get_ip_from_string(string=result)
        if ip:
            return ip

        raise UnableToReserveError(result)

    def add_interface(
        self,
        interface_name,
        hostname="",
        ip="",
        subnet="",
        multihomed="N",
        ptr="N",
        status="",
        description="",
        contact1="",
        contact1_type="",
    ):
        """
        Function to add a specified host to either a given ip or the next available
        ip within a subnet. The user can specify multihome if desired.

        :param interface_name: (str) name of interface to add.
        :param hostname: (str) hostname (default is interface name)
        :param ip: (str) IP address of interface to add. If left as '' the next available ip will be given used.
        :param subnet: (str) subnet where the next available ip will be retrieved if there is no ip specefied in
        the parameters. Include subnet (i.e. 10.34.182.128/26)

        :param multihomed: (strr)  Multihomed host "Y" for yes and "N" for no. Default is "N" for no.
        :param ptr: (str) "Y" to add PTR record for interface (default is "Y" for yes)
        :param status: (str) status of interface (e.g. Active,Inactive,Reserved,etc.).
        :param description: (str) description of the interface
        :param contact1: (str) contact for the interface (i.e. tybruno)
        :param contact1_type: (str) contact type for the interface (e.g. Employee, Mail Alias, Other,
        “Local Contact (on-site)”,“Generic User”, Metric, “Epage Alias”, “Support Group”)

        :return: the added interface
        """

        if not ip and subnet:
            LOGGER.info(
                "%s - No ipaddress was provided. getting next available "
                "ipaddress based on subnet.",
                interface_name,
            )
            try:
                ip = self.find_list_of_next_available_ips(
                    subnet=subnet, number_of_addresses_returned="1"
                )[0]
            except UnableToFindError as error:
                raise UnableToReserveError(error)

        flags = {
            "function": "int-add",
            "name": interface_name,
            "hostname": hostname,
            "ipaddress": ip,
            "multihomed": multihomed,
            "Contact1": contact1,
            "Contact1type": contact1_type,
            "Status": status,
            "PTR": ptr,
            "Descr": f'"{description}"',
        }
        print(contact1_type)

        command = self._generate_command(**flags)

        LOGGER.info(command)

        result = self.send_command(command)

        LOGGER.info("add_interface: %s", result)

        ip = ""

        if "Success" in result:
            ip = get_ip_from_string(result)

        if ip:
            return ip

        raise UnableToReserveError(result)

    def add_next_ip(self, hostname, subnet, multihomed):
        """
        Function to find the next available ip within a given subnet and
        assign the specified host to that ip.

        :param hostname:
        :param subnet:
        :param multihomed: True/False

        :return: Success/Fail

        """

        if multihomed is True:
            multihomed = "Y"
        else:
            multihomed = "N"

        command = f"-f=add-nextavail -n={hostname} -s={subnet} -Ct1={self.username} \
            -m={multihomed}"
        LOGGER.info(command)

        result = self.send_command(command)

        LOGGER.info("add_next_ip: %s", result)

        return result

    def alias_add(self, alias, interface):
        """
        Function to create an alias

        :param alias:
        :param interface: fqdn

        :return: Success/Fail
        """

        command = f"-f=alias-add -a={alias} -i={interface}"
        LOGGER.info(command)

        result = self.send_command(command)

        LOGGER.info("alias_add: %s", result)

        return result

    def alias_delete(self, alias):
        """
        Function to delete a specified alias from address management.

        :param alias:

        :return: Success/Fail
        """

        command = f"-f=alias-del -a={alias}"
        LOGGER.info(command)

        result = self.send_command(command)

        LOGGER.info("alias_delete: %s", result)

        return result

    def alias_mod(self, oldalias, newalias):
        """
        Function to modify an existing alias from address management.

        :param oldalias:
        :param newalias:

        :return: Success/Fail
        """

        command = f"-f=alias-mod -oa={oldalias} -a={newalias}"
        LOGGER.info(command)

        result = self.send_command(command)

        LOGGER.info("alias_mod: %s", result)

        return result

    def create_scope(self, name, descrip, subnet, iprange, policy, local):
        """
        Function to create a scope within a given subnet. The range is found
        automatically by using the getrange function to find a group of congruent
        ipaddresses that match the given size.


        :param name: Scope Name
        :param descrip:
        :param subnet:
        :param iprange:
        :param policy: Get from am.cisco.com
        :param local: mtv, sjc, aer, ams, gpk, bgl, bxb,
                      hkg, rch, rtp, sng, syd, tky

        :return: Success/Fail
        """

        LOGGER.info(
            "createscope - %s, %s, %s, \
                    %s, %s, %s",
            name,
            descrip,
            subnet,
            iprange,
            policy,
            local,
        )

        lowrange, highrange = self.get_range(subnet, iprange)

        LOGGER.info("Collected Ranges: %s, %s", lowrange, highrange)

        defroute = get_gateway(subnet)

        LOGGER.info("Gateway: %s", defroute)

        dhcp = get_dhcp_add(local.lower())

        LOGGER.info("DHCP: %s", dhcp)
        LOGGER.info("createscope - dhcp server: %s", dhcp)

        if lowrange == 0:
            LOGGER.info(
                """There are not enough consecutive ip's within this subnet to meet
                your requirements. Please reduce your range and try again.
                """
            )
            results = "There are not enough consecutive ip's within this subnet \
                      to meet your requirements. Please reduce your range and try \
                      again."

            return results

        LOGGER.info("Creating Scope")

        command = f"-f=scope-add -N={name} -D={descrip} -sn={subnet} \
        -R='{lowrange}:{highrange}' -P={policy} -DS='{dhcp}' -DR='{defroute}' -Tr='N'"
        LOGGER.info(command)

        result = self.send_command(command)

        LOGGER.info("create_scope: %s", result)

        return result

    def del_address_block(self, address_block):
        """
        Successfully deleted an address block 10.34.182.128/27

        :param address_block:
        :return: if found 'Successfully deleted an address block
        10.34.182.128/27.if not found 'ERROR: No address block found for 10.34.182.160/27'
        """
        address_block_ip = ipaddress.ip_interface(address_block)

        command = f"-f=address-block-del -AddressBlock={address_block_ip}"

        result = self.send_command(command)

        LOGGER.info("del_address_block: %s", result)

        return result

    def del_interface(self, ip="", interface_name=""):
        """
        Delete an Interface.

        To delete an interface only the interfaces ip address or interface
        name needs to be given.

        :param ip: (str) IP address of interface to delete.
        (e.g. '10.34.182.128')
        :param interface_name: (str) Name of interface to delete.
        (e.g. 'sjc12-gg05-isr4451-ten-1-1' or
        'sjc12-gg06-is4451-ten-1-1.cisco.com') cisco.com is the default
        domain if one is not specified with the interface name

        :return: The results if the delete was successful or not.
        (e.g. successful: 'Successfully deleted Interface
        script-test3.cisco.com.' unsuccessful: 'ERROR: No interface found
        for script-test4.cisco.com.' )
        """

        if ip and not interface_name:
            interface = self.find_interfaces(ip=ip, number_of_interfaces_to_return="1")[
                0
            ]
            interface_name = interface.split(":")[1]

        elif interface_name and not ip:
            interface = self.find_interfaces(
                interface_name=interface_name, number_of_interfaces_to_return="1"
            )[0]

            ip = interface.split(":")[1]

        flags = {"function": "int-del", "ipaddress": ip, "name": interface_name}

        command = self._generate_command(**flags)

        result = self.send_command(command)

        LOGGER.info("del_interface: %s", result)

        return result

    def del_subnet(self, subnet):
        """
        Function to delete a specified subnet from address management.


        :param subnet: (str) subnet to delete

        :return: Success/Fail
        """
        command = f"-f=subnet-del -s={subnet}"
        LOGGER.info(command)

        result = self.send_command(command)

        LOGGER.info("delsubnet: %s", result)

        return result

    def find_subnets_free(self, address_block):
        """
        Description: Find all open subnets in an address block. Not currently IPv6 compatable.

        :param address_block: (str) network address and optional prefix length of the addressblock
        :return:
        """

        address_block_ip = ipaddress.ip_interface(address_block)
        command = f"-f=subnets-free -addressblock={address_block_ip.ip}"

        return self.send_command(command=command)

    def find_helpers(self, local):
        """
        Function to locate dhcp helpers for a specified local.


        :param local: mtv, sjc, aer, ams, gpk, bgl, bxb,
                      hkg, rch, rtp, sng, syd, tky

        :return: Example: ['dhcp-mtv1-1-l-tmp.cisco.com:171.68.48.165',
        'dhcp-mtv1-1-l.cisco.com:173.36.131.31|2001:420:68d:4001:0:0:0:11']

        """

        command = f"-f=int-find -n=dhcp-{local}* -r=2"
        LOGGER.info(command)

        result = self.send_command(command)

        LOGGER.info("findhelpers: %s", result)

        if "ERROR" in str(result):
            results = f"No dhcp helpers were found for {local}."
            return results

        return result

    def find_interfaces(
        self,
        address_block="",
        subnet="",
        ip="",
        interface_name="",
        number_of_interfaces_to_return="all",
        search_by_descriptiioin="",
        search_by_function="",
        search_by_technology="",
        search_by_location="",
        search_by_area="",
        search_by_city="",
        search_by_country="",
        search_by_contact="",
        return_as_dictionary=False,
    ):
        """
        Find the IP address or name for an interface, or all interfaces in a subnet or address block

        :param address_block: (str) network address and prefix length of the
        addressblock (prefix length is required) (i.e. 10.34.182.128/27)

        :param subnet: (str) network address of the subnet you want to find an available address
        :param ip: (str) IP address of the interface you want to find
        :param interface_name: (str) DNS name of the interface you want to find
        :param number_of_interfaces_to_return: (str) number of interfaces to return ('all' is default), set to 'all' to
        have all matches returned or number value to have that many interfaces returned (i.g. '1' returns 1 interface)
        :param search_by_descriptiioin: (str) find from address block or subnet matching the description
        :param search_by_function: (str) find from address block or subnet matching the function
        :param search_by_technology: (str) find from address block or subnet matching the technology
        :param search_by_location: (str) find from address block or subnet matching the location
        :param search_by_area: (str) find from address block or subnet matching the area
        :param search_by_city: (str)  find from address block or subnet matching the city
        :param search_by_country: (str) find from address block or subnet matching the country
        :param search_by_contact: (str) find from address block or subnet matching the contact

        :return: a list of found interfaces.
        """
        block_type = "S"
        if address_block:
            block_type = "A"

        command = " -comma "

        flags = {
            "function": "int-find",
            "addressblock": address_block,
            "subnet": subnet,
            "ipaddress": ip,
            "name": interface_name,
            "return": number_of_interfaces_to_return,
            "Bdescr": search_by_descriptiioin,
            "Bfunction": search_by_function,
            "Btechnology": search_by_technology,
            "Blocation": search_by_location,
            "Barea": search_by_area,
            "Bcity": search_by_city,
            "Bcountry": search_by_country,
            "Bcontact": search_by_contact,
            "type": block_type,
        }
        command += self._generate_command(**flags)

        LOGGER.info(command)

        result = self.send_command(command)

        if "ERROR" in result:
            return result

        if return_as_dictionary:
            interfaces = {}
            for item in result.split(","):
                intf_ip, intf_hostname = item.split(":")
                interfaces[intf_ip] = intf_hostname
            LOGGER.info("find_interfaces: %s", interfaces)

            return interfaces

        LOGGER.info("find_interfaces: %s", result)
        return result.split(",")

    def find_interface(self, interface):
        """
        Function to provide address management details
        of a specified hostname or ip address.

        :param interface: hostname or ipaddress

        :return:
             for ipaddress returns ipaddress:fqdn
             for hostname returns  fqdn:ipaddress
        """

        if "." in interface:
            command = f"-f=int-find -i={interface}"
        else:
            command = f"-f=int-find -n={interface}"

        LOGGER.info(command)

        result = self.send_command(command)

        if "ERROR" in str(result):
            LOGGER.info("%s was not found.", interface)
            results = f"{interface} was not found."
            return results

        LOGGER.info("find_inetrface: %s", result)
        return result

    def find_next_available(
        self,
        address_block="",
        subnet="",
        subnet_prefix_length="30",
        search_type="I",
        display_total_count_of_addresses_returned="",
        number_of_blocks_or_addresses_returned="1",
        search_by_description="",
        search_by_function="",
        search_by_technology="",
        search_by_location="",
        search_by_area="",
        search_by_city="",
        search_by_country="",
        search_by_contact="",
    ):
        """
        Find next available interface or subnet in a block.



        :param address_block: (str) network address and prefix length of the addressblock (prefix length is required)
        :param subnet: (str) network address of the subnet you want to find an available address
        :param subnet_prefix_length: (str) prefix length of the subnet you want to be able to find space for
        :param search_type: (str) type of search, i.e. 'I' for IP address or 'S' for subnet
        :param display_total_count_of_addresses_returned: (str) display the total count of addresses returned
        :param number_of_blocks_or_addresses_returned: (str) number of blocks or addresses to return (1 is default)
         set to 'all' to have all matches returned
        :param search_by_description: (str) find from address block or subnet matching the description
        :param search_by_function: (str) find from address block or subnet matching the function
        :param search_by_technology: (str) find from address block or subnet matching the technology
        :param search_by_location: (str) find from address block or subnet matching the location
        :param search_by_area: (str) find from address block or subnet matching the area
        :param search_by_city: (str) find from address block or subnet matching the city
        :param search_by_country: (str) find from address block or subnet matching the country
        :param search_by_contact: (str) find from address block or subnet matching the contact
        :return: next available interface or subnet
        """

        command = f" -comma "

        flags = {
            "function": "next-avail",
            "addressblock": address_block,
            "subnet": subnet,
            "type": search_type,
            "Total": display_total_count_of_addresses_returned,
            "return": number_of_blocks_or_addresses_returned,
            "Bdescr": search_by_description,
            "Bfunction": search_by_function,
            "Btechnology": search_by_technology,
            "Blocation": search_by_location,
            "Barea": search_by_area,
            "Bcity": search_by_city,
            "Bcountry": search_by_country,
            "Bcontact": search_by_contact,
        }

        if address_block:
            flags["length"] = subnet_prefix_length

        command += self._generate_command(**flags)

        result = self.send_command(command=command)

        LOGGER.info("find_next_available: %s", result)
        print("result = " + result)

        if "ERROR" in result:
            raise UnableToFindError(result)

        return get_ip_from_string(result)

    def find_list_of_next_available_ips(
        self, address_block="", subnet="", number_of_addresses_returned="all", ping=True
    ):
        """
        Finds a
        :param address_block:
        :param subnet:
        :param number_of_addresses_returned:
        :param ping:
        :return:
        """

        ips = (
            self.find_next_available(
                address_block=address_block,
                subnet=subnet,
                number_of_blocks_or_addresses_returned=number_of_addresses_returned,
            )
            .replace(" ", "")
            .split(",")
        )

        if ping:
            ip_list = []

            for ip in ips:
                if self.ping_ip(ip):
                    ip_list.append(ip)

            return ip_list

        return ips

    def find_next_ip(self, subnet, iprange, ping):
        """ Find and return the next ip within a subnet or block. This function pings
        the retuned ip to ensure it is not being used. If the ip returns a
        ping, then the next available ip will be chosen and tested.


        :param subnet:
        :param iprange: Number of address to get or 'all'
        :param ping: True pings each available address and
                    only takes non-active ones. Unless range is set to all.
                    False will skip the ping process.

        :return: A list of available ipaddresses.
        """

        command = f"-f=next-avail -s={subnet} -t=I -r=all -comma"
        LOGGER.info(command)

        result = self.send_command(command)

        LOGGER.info("find_next_ip - Eman Return: %s", result)

        ipblock = result.split(",")

        if "all" in iprange:
            return ipblock

        if len(ipblock) < int(iprange):
            LOGGER.info("findnextip: Not enough ip's available")
            return "Not enough ip's available"

        ips = []
        for ip in ipblock:
            if ping is True:
                active = self.ping_ip(ip)
                if active is False:
                    ips.append(ip)
                    if len(ips) >= int(iprange):
                        LOGGER.info("find_next_ip: %s", ips)
                        return ips
            else:
                ips.append(ip)
                if len(ips) >= int(iprange):
                    LOGGER.info("find_next_ip: %s", ips)
                    return ips

        return ips

    def get_range(self, subnet, ip_range):
        """
        Finds and returns a range of congruent ip addresses

        :param subnet:
        :param ip_range: Number of ip addresses

        :return: range based on requested ip addresses
        """

        ips = self.find_next_ip(subnet, "all", False)
        LOGGER.info("getrange - available ip's: %s", ips)
        ips.reverse()
        ipgrouping = []
        count = len(ips)
        base = 0
        max_ip = ip_range
        LOGGER.info("IP Count and Range: %s, %s", count, ip_range)

        while count > int(ip_range):
            iplist = ips[int(base) : int(max_ip)]
            LOGGER.info("IP List: %s", iplist)
            for ip in iplist:
                ipgrouping.append(ip.rsplit(".")[-1])
            ipgrouping.reverse()
            itr = (int(x) for x in ipgrouping)
            first = next(itr)
            consecutive = all(a == b for a, b in enumerate(itr, first + 1))

            if consecutive is True:
                # return range 1,range 2
                return iplist[int(ip_range) - 1], iplist[0]

            ipgrouping = []
            base = base + 1
            max_ip = int(max_ip) + 1
            count = int(count) - 1

        LOGGER.info("get_range: No congruent ip addresses in the given range")
        return 0, 0

    def get_scopes_by_subnet(self, subnet):
        """
        Function to return available scopes of a specified subnet.

        :param subnet:

        :return: List of scopes within subnet
        """

        command = f"-f=scope-info -details -s={subnet}"
        LOGGER.info(command)

        result = self.send_command(command)
        info = result.replace("\n", ",").replace(",,", ",").split(",")
        scope = {}
        count = 0
        for line in info:
            if "Scope Name" in line:
                count += 1
                key, value = line.split(":")
                key = key + str(count)
                scope.update({key: value})
            if "Range" in line:
                key, value = line.split(":")
                key = key + str(count)
                scope.update({key: value})

        LOGGER.info("get_scopes_by_subnet: %s", scope)

        return scope

    def add_scope(
        self,
        scope_name="",
        description="",
        subnet="",
        ranges="",
        policy="",
        dhcpserver="",
        status="Active",
        type="Primary",
        pingbeforeoffer="N",
        failoverbackuppercentage="5",
        trend="Y",
        alertpercentused="95",
        selectiontags="OtherDevices",
        defaultrouter="",
        callmanager="",
        primaryscope="",
        addinterfaces="",
        ddnsenabled="N",
        ddnsdomain="",
    ):
        """

        :param name:
        :param description:
        :param subnet:
        :param range:
        :param policy:
        :param dhcpserver:
        :param status:
        :param type:
        :param pingbeforeoffer:
        :param failoverbackuppercentage:
        :param trend:
        :param alertpercentused:
        :param selectiontags:
        :param defaultrouter:
        :param callmanager:
        :param primaryscope:
        :param addinterfaces:
        :param ddnsenabled:
        :param ddnsdomain:
        :return:
        """

        # if selectiontags != "OtherDevices":
        #

        flags = {
            "function": "scope-add",
            "Name": f'"{scope_name}"',
            "Descr": f'"{description}"',
            "subnet": subnet,
            "R": f'"{ranges}"',
            "Policy": f'"{policy}"',
            "DhcpServer": f'"{dhcpserver}"',
            "Status": status,
            "Type": type,
            "PingBeforeOffer": pingbeforeoffer,
            "FailoverBackupPercentage": failoverbackuppercentage,
            "Trend": trend,
            "AlertPercentUsed": alertpercentused,
            "SelectionTags": selectiontags,
            "DefaultRouter": defaultrouter,
            "CallManager": f'"{callmanager}"',
            "PrimaryScope": primaryscope,
            "AddInterfaces": addinterfaces,
            "DdnsEnabled": ddnsenabled,
            "DdnsDomain": ddnsdomain,
        }

        command = self._generate_command(**flags)

        LOGGER.info(command)

        try:
            result = self.send_command(command)
            LOGGER.info("scope-add: %s", result)
            return result
        except Exception as error:
            LOGGER.info(error)

    def del_scope(self, scope_name, Delete_interfaces="Yes"):
        """

        :param scope_name: Name of scope to delete
        :param Delete_interfaces: Yes or No (Default is Yes)
        :return:
        """
        if "Yes" in Delete_interfaces:
            function = "scope-del -DI -q"
        else:
            function = "scope-del"

        flags = {"function": function, "Name": f'"{scope_name}"'}

        command = self._generate_command(**flags)

        LOGGER.info(command)

        try:
            result = self.send_command(command)
            LOGGER.info("scope-del: %s", result)
            return result
        except Exception as error:
            LOGGER.info(error)
            return error

    def mod_scope(
        self,
        scope_name="",
        callmanager="",
        policy="",
        ddnsenabled="",
        ddnsdomain="",
        selectiontags="",
    ):
        """

        :param name:
        :param policy:
        :param callmanager:
        :param ddnsenabled:
        :param ddnsdomain:
        :param selectiontags:
        :return:
        """

        flags = {
            "function": "scope-mod",
            "name": f'"{scope_name}"',
            "SelectionTags": selectiontags,
        }

        command = self._generate_command(**flags)

        LOGGER.info(command)

        try:
            result = self.send_command(command)
            LOGGER.info("mod_scope: %s", result)
            return result
        except Exception as error:
            LOGGER.info(error)

    def ping_ip(self, address):
        """
        Function to ping a given ipaddress and return true or false.

        :param address: Ip address to ping

        :return: True/False
        """

        command = "ping -c 1 " + address

        result = self.send_command(command)

        if "0 packets received" in result:
            active = False
        else:
            active = True

        return active

    def rename_interface(self, oldname, newname):
        """
        Function to rename a specified interface within address management.

        :param oldname:
        :param newname:

        :return: Success/fail
        """

        command = f"-f=int-ren -on={oldname} -nn={newname}"
        LOGGER.info(command)

        result = self.send_command(command)

        LOGGER.info("rename_interface: %s", result)

        return result


def get_gateway(subnet):
    """
    Function which returns the gateway of a given subnet.

    :param subnet:
    :return: gateway
    """

    subnet, __prefix = subnet.split("/")
    gateway = ipaddress.ip_address(subnet) + 1

    return str(gateway)


def get_dhcp_add(local):
    """
    Function to provide a DHCP name based on a provided local.

    :param local: mtv, sjc, aer, ams, gpk, bgl, bxb,
                 hkg, rch, rtp, sng, syd, tky

    :return: dhcpsrv
    """
    dhcpsrv = ""

    if "mtv" in local:
        dhcpsrv = "dhcp-mtv1-1-l"
    elif "sjc" in local:
        dhcpsrv = "dhcp-mtv1-1-l"
    elif "aer" in local:
        dhcpsrv = "dhcp-aer1-1-l"
    elif "ams" in local:
        dhcpsrv = "dhcp-aer1-1-l"
    elif "gpk" in local:
        dhcpsrv = "dhcp-aer1-1-l"
    elif "bgl" in local:
        dhcpsrv = "dhcp-blr1-1-l"
    elif "bxb" in local:
        dhcpsrv = "dhcp-bxb1-1-l"
    elif "hkg" in local:
        dhcpsrv = "dhcp-hkg1-1-l"
    elif "rch" in local:
        dhcpsrv = "dhcp-rch1-1-l"
    elif "rtp" in local:
        dhcpsrv = "dhcp-rtp5-1-l"
    elif "sng" in local:
        dhcpsrv = "dhcp-sin1-1-l"
    elif "syd" in local:
        dhcpsrv = "dhcp-syd1-1-l"
    elif "tky" in local:
        dhcpsrv = "dhcp-tyo1-1-l"

    return dhcpsrv


def find_ipv6_with_subnet(string):
    """
    Find and return IPv6 address with subnet inside a string.
    This function will only return an ipv6 address with a subnet



    :param string: (str) The string to search for ipv6 with subnet
    (i.e. "Successfully added Subnet 2001:420:30a:200::a10/127")
    :return: (str) the found ipv6 address with subnet (i.e. '2001:420:30a:200::a10/127')
    """
    ip = re.search(
        r"(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|"
        r"([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}"
        r"(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|"
        r"([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}"
        r"(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:"
        r"((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|"
        r"::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}"
        r"(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|"
        r"(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))/"
        r"([0-9])([0-9])([0-9])?",
        string,
    )
    if ip:
        return ip.group()

    return None


def find_ipv6_without_subnet(string):
    """
    Find and resturn IPv6 address without subnet inside a string
    This function will only return an ipv6address that does not have a subnet


    :param string: (str) The string to search for ipv6 with subnet(i.e.
    "Successfully added interface 2001:420:30a:200::a10")
    :return: (str) the found ipv6 address with subnet (i.e. '2001:420:30a:200::a10')
    """
    ip = re.search(
        r"(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:"
        r"|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|"
        r"([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|"
        r"([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]"
        r"{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}"
        r"(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]"
        r"{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]"
        r"{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}"
        r"((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}"
        r"[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:"
        r"((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}"
        r"[0-9]){0,1}[0-9]))",
        string,
    )
    if ip:
        return ip.group()

    return None


def find_ipv4_with_subnet(string):
    """
    Find and return IPv4 address with subnet inside a string.
    This function will only return an ipv4 address with a subnet



    :param string: (str) The string to search for ipv6 with subnet(i.e. "Successfully added Subnet 10.34.33.20/30")
    :return: (str) the found ipv6 address with subnet (i.e. '10.34.33.20/30')
    """
    ip = re.search(r"([0-9]{1,3}\.){3}[0-9]{1,3}/([0-9])([0-9])?", string)

    if ip:
        return ip.group()

    return None


def find_ipv4_without_subnet(string):
    """
    Find and return IPv4 address with subnet inside a string.
    This function will only return an ipv4 address with a subnet

    :param string: (str) The string to search for ipv6 with subnet(i.e. "Successfully added interface 10.34.33.20")
    :return: (str) the found ipv6 address with subnet (i.e. '10.34.33.20')
    """
    ip = re.search(r"([0-9]{1,3}\.){3}[0-9][0-9]?", string)

    if ip:
        return ip.group()

    return None


def get_ip_from_string(string):
    """
    Will find and return an ipv4 address w/ subnet, ipv4 address w/o subnet, ipv6 address w/ subnet, or
    ipv6 address w/o subnet.

    if string = 'Successfully added Subnet 10.34.33.20/30' return '10.34.33.20/30'
    if string = 'Successfully added interface 10.34.33.20' return '10.34.33.20'
    if string ='Successfully added Subnet 2001:420:30a:200::a10/57' return '2001:420:30a:200::a10/57'
    if string = 'Successfully added interface 2001:420:30a:200::a10' return '2001:420:30a:200::a10'

    :param string: (str) the string to search for ipv4 w/ or w/o subnet or ipv6 w/ or w/o subnet
    :return: (str) ipv4 address w/ or w/o subnet or ipv6 address w/ or w/o subnet
    """
    ip = find_ipv4_with_subnet(string)
    if ip:
        return ip

    ip = find_ipv4_without_subnet(string)

    if ip:
        return ip

    ip = find_ipv6_with_subnet(string)

    if ip:
        return ip

    ip = find_ipv6_without_subnet(string)

    if ip:
        return ip

    return None


if __name__ == "__main__":
    # for testing
    print("\n++++++++++++++++++++++")
    print("Starting New Test Run!")
    print("++++++++++++++++++++++\n")
    from secrets import USERNAME, PASSWORD
    import inspect

    # csv_file = '/Users/rmassing/Downloads/CVO-100WM-Bridge-for-test copy.csv'
    b = Eman(USERNAME, PASSWORD)
    # result = b.add_scope(scope_name="rmassing-viptela-cvo",
    #                      description="rmassing-viptela-cvo",
    #                      subnet="10.35.105.0/29",
    #                      ranges="10.35.105.2:10.35.105.6",
    #                      policy="San Jose Wireless LAN",
    #                      dhcpserver="dhcp-mtv1-1-l",
    #                      defaultrouter="10.35.105.1",
    #                      callmanager="171.70.146.221,173.36.131.161"
    #                   )
    scopes = (
        "nortwong-cvo-vEdge100WM",
        "aadixon-cvo-vEdge100WM",
        "timiller-cvo-vEdge100WM",
        "johcurra-cvo-vEdge100WM",
        "hitpanch-cvo-vEdge100WM",
        "dhighlan-cvo-vEdge100WM",
        "calchris-cvo-vEdge100WM",
        "gwerner-cvo-vEdge100WM",
        "tnorling-cvo-vEdge100WM",
        "diacobac-cvo-vEdge100WM",
        "cbarrero-cvo-vEdge100WM",
        "crmoelle-cvo-vEdge100WM",
        "skilpatr-cvo-vEdge100WM",
        "iprocyk-cvo-vEdge100WM",
        "brhuston-cvo-vEdge100WM",
        "brfreder-cvo-vEdge100WM",
        "matrhebe-cvo-vEdge100WM",
        "janaraya-cvo-vEdge100WM",
        "ramasub-cvo-vEdge100WM",
        "petho-cvo-vEdge100WM",
        "lawchung-cvo-vEdge100WM",
        "tkonewka-cvo-vEdge100WM",
        "sjahansh-cvo-vEdge100WM",
        "sherrman-cvo-vEdge100WM",
        "davisick-cvo-vEdge100WM",
        "aljurado-cvo-vEdge100WM",
        "clsorens-cvo-vEdge100WM",
        "jaschnei-cvo-vEdge100WM",
        "jvanhave-cvo-vEdge100WM",
        "kvassall-cvo-vEdge100WM",
    )
    for i in scopes:
        result = b.mod_scope(scope_name=i, selectiontags=("IPPhones", "OtherDevices"))
        # result = b.del_scope('rmassing-viptela-cvo')
        print(result)
    print("\n++++++++++++++++++")
    print("Test Run Complete!")
    print("++++++++++++++++++\n")
