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

# These are fake, you would need to add real address, servers and policies.
regionsab = {
    'SJC': '192.168.0.1/21',
    'RTP': '192.168.76.0/22',
    'AER': '192.168.232.0/21',
    'TEST': '192.168.137.0/24'
}
regionspolicys = {
    'CHK': 'Chicago Wireless LAN',
    'DFW': 'DFW Wireless LAN',
    'HOL': 'Holland WLAN',
    'TEST': 'Home Based LAN'
}
dhcpservers = {
    'CHK': 'server-chk-7-k',
    'DFW': 'server-dfw-7-k',
    'HOL': 'server-hol-7-k',
    'TEST': 'server-test-7-k'
}
callmanagers = {
    'CHK': '192.168.146.221,192.168.131.161',
    'DFW': '192.168.36.165,192.168.24.202',
    'HOL': '192.168.75.175,192.168.100.5',
    'TEST': '192.168.146.221,192.168.131.161',
}
