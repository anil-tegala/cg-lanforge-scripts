import importlib
import logging
import os
import sys
import time
from datetime import datetime, timedelta
import allure
import paramiko
import pytest
from scp import SCPClient
from tabulate import tabulate
from itertools import islice
import csv
import pandas as pd

sys.path.append(os.path.join(os.path.abspath(__file__ + "../../../")))
lfcli_base = importlib.import_module("py-json.LANforge.lfcli_base")
LFCliBase = lfcli_base.LFCliBase
realm = importlib.import_module("py-json.realm")
cv_test_manager = importlib.import_module("py-json.cv_test_manager")
cv_test = cv_test_manager.cv_test
lf_cv_base = importlib.import_module("py-json.lf_cv_base")
ChamberViewBase = lf_cv_base.ChamberViewBase
create_chamberview_dut = importlib.import_module("py-scripts.create_chamberview_dut")
DUT = create_chamberview_dut.DUT
create_chamberview = importlib.import_module("py-scripts.create_chamberview")
CreateChamberview = create_chamberview.CreateChamberview
sta_connect2 = importlib.import_module("py-scripts.sta_connect2")
StaConnect2 = sta_connect2.StaConnect2
profile_utility = importlib.import_module("py-json.profile_utility")
ProfileUtility = profile_utility.ProfileUtility
createstation = importlib.import_module("py-scripts.create_station")
CreateStation = createstation.CreateStation
sniffradio = importlib.import_module("py-scripts.lf_sniff_radio")
SniffRadio = sniffradio.SniffRadio
stascan = importlib.import_module("py-scripts.sta_scan_test")
StaScan = stascan.StaScan
cv_test_reports = importlib.import_module("py-json.cv_test_reports")
lf_report = cv_test_reports.lanforge_reports
attenuator_serial = importlib.import_module("py-scripts.attenuator_serial")
Attenuator = attenuator_serial.AttenuatorSerial
lf_atten_mod_test = importlib.import_module("py-scripts.lf_atten_mod_test")
Attenuator_modify = lf_atten_mod_test.CreateAttenuator


class lf_libs:
    """
    "traffic_generator": {
            "name": "lanforge",
            "scenario": "",
            "details": {
                "manager_ip": "<ip-address>",
                "http_port": 8080,
                "ssh_port": 22,
                "default_setup_DB": "Test_Scenario",
                "wan_ports": ["1.1.eth2"],
                "lan_ports": ["1.1.eth1"]
            }
        }
    """
    lanforge_data = dict()
    manager_ip = None
    testbed = None
    run_lf = False
    manager_http_port = None
    manager_ssh_port = None
    manager_default_db = None
    wan_ports = None
    lan_ports = None
    uplink_nat_ports = None
    dut_data = None
    dut_objects = []
    default_scenario_name = None
    default_scenario_test = None
    default_scenario_raw_lines = []
    temp_raw_lines = []
    chamberview_object = None
    max_possible_stations = None
    max_2g_stations = None
    max_5g_stations = None
    max_6g_stations = None
    max_ax_stations = None
    max_ac_stations = None
    twog_prefix = "wlan_2g"
    fiveg_prefix = "wlan_5g"
    sixg_prefix = "wlan_6g"
    ax_prefix = "AX200_0"
    pcap_obj = None
    """
    Scenario : dhcp-bridge / dhcp-external
    dhcp-bridge -   wan_ports will act as dhcp server for AP's and it will use uplink_nat_ports for uplink NAT
                    lan_ports will have IP Address from the AP 

    dhcp-external - wan_ports will have IP Address from the dhcp server that will be hosted outside the lanforge
                    lan_ports will have IP Address from the AP 
                    In case of VLAN configurations, wan_ports will be tagged to get IP Address 
                    from VLANS that are outside LANforge
    """
    scenario = None
    """
    Scenario in chamberview which will be read by read_cv_scenario() and stored here
    This will be used to add additional stuff on scenario along with this
    """
    cv_scenario = None
    """
    Number of Resources available
    """
    resources = None

    # """
    # 6e radio - supports (2.4GHz, 5gHz and 6gHz Band)
    # Maximum 4 Station per radio
    # """
    # mt7925e_radios = []

    """
    ax radio - supports (2.4G and 5gHz Band)
    Maximum 1 Station per radio
    """

    ax200_radios = []

    """
    6e radio - supports (2.4GHz, 5gHz and 6gHz Band)
    Maximum 1 Station per radio
    """
    be200_radios = []

    """
        6e radio - supports (2.4GHz, 5gHz and 6gHz Band)
        Maximum 1 Station per radio
        """
    ax210_radios = []

    """
    ax radio - supports (2.4G and 5gHz Band)
    Maximum 19 Station per radio
    """
    mtk_radios = []

    """
    ax radio - supports (2.4G Band)
    Maximum 64 Station per radio
    """
    wave2_2g_radios = []

    """
    ax radio - supports (5gHz Band)
    Maximum 64 Station per radio
    """
    wave2_5g_radios = []

    """
    ax radio - supports (2.4G and 5gHz Band)
    Maximum 64 Station per radio
    """
    wave1_radios = []

    """lf_tests
        ax radio - supports (2.4G and 5gHz Band)
        Maximum 64 Station per radio
        """
    attenuator = []

    """
    Realm Object can be used to call various methods available
    """
    local_realm = None

    def __init__(self, lf_data={}, dut_data=[], run_lf=False, log_level=logging.DEBUG):
        logging.basicConfig(format='%(asctime)s - %(message)s', level=log_level)
        lf_data = dict(lf_data)
        self.dut_data = dut_data
        self.dut_data = dut_data
        self.run_lf = run_lf
        self.dut_idx_mapping = {}
        # try:
        self.lanforge_data = lf_data.get("details")
        self.testbed = lf_data.get("testbed")
        self.scenario = lf_data.get("scenario")
        self.setup_lf_data()
        self.setup_relevent_profiles()
        self.setup_metadata()
        if self.scenario == "dhcp-bridge":
            logging.info("Scenario name: " + str(self.scenario))
            # creating default  raw lines for chamberview
            self.create_dhcp_bridge()
        elif self.scenario == "dhcp-external":
            logging.info("Scenario name: " + str(self.scenario))
            self.create_dhcp_external()
        self.chamber_view(raw_lines="default")
        logging.info("sleep time 15 sec")
        time.sleep(15)
        self.temp_raw_lines = self.default_scenario_raw_lines.copy()
        self.setup_dut()
        # except Exception as e:
        # logging.error("lf_data has bad values: " + str(lf_data))
        # logging.error(e)

    """
        setup_lf_data : used to set object variables that are passed from lab_info.json
                        It also creates object for realm and CreateChamberview class object
                         which can be used further
    """

    def setup_lf_data(self):
        try:
            self.manager_ip = self.lanforge_data.get("manager_ip")
            self.manager_http_port = self.lanforge_data.get("http_port")
            self.manager_ssh_port = self.lanforge_data.get("ssh_port")
            self.manager_default_db = self.lanforge_data.get("default_setup_DB")
            self.wan_ports = self.lanforge_data.get("wan_ports")
            self.lan_ports = self.lanforge_data.get("lan_ports")
            self.uplink_nat_ports = self.lanforge_data.get("uplink_nat_ports")
            self.local_realm = realm.Realm(lfclient_host=self.manager_ip, lfclient_port=self.manager_http_port)
            self.chamberview_object = CreateChamberview(self.manager_ip, self.manager_http_port)
            self.default_scenario_raw_lines = []
        except Exception as e:

            logging.error(e)

    """
        setup_dut : It read the dut data and creates the dut with relevent data
    """

    def setup_dut(self):
        self.dut_objects = []
        logging.info("DUT Data: " + str(self.dut_data))
        for index in range(0, len(self.dut_data)):
            dut_obj = DUT(lfmgr=self.manager_ip,
                          port=self.manager_http_port,
                          dut_name=self.dut_data[index]["identifier"],
                          sw_version=self.dut_data[index]["firmware_version"],
                          hw_version=self.dut_data[index]["mode"],
                          model_num=self.dut_data[index]["model"],
                          serial_num=self.dut_data[index]["identifier"])
            dut_obj.setup()
            dut_obj.add_ssids()
            self.dut_objects.append(dut_obj)
            logging.info("Creating DUT")

    def setup_metadata(self):
        data = self.json_get("/port/all")
        all_eth_ports = []
        for info in data["interfaces"]:
            if (info[list(info.keys())[0]]["port type"]) == "Ethernet":
                all_eth_ports.append(list(dict(info).keys())[0])
        logging.info("Available Ports: " + str(all_eth_ports))
        for port in self.wan_ports:
            if port not in all_eth_ports:
                logging.error("LANforge system doesn't contains the expected WAN Port:  " + str(port))
                continue
            logging.info("WAN Port is Available on LANforge Port Manager: " + str(port))
        for port in self.lan_ports:
            if port not in all_eth_ports:
                logging.error("LANforge system doesn't contains the expected LAN Port:  " + str(port))
                continue
            logging.info("LAN Port is Available on LANforge Port Manager: " + str(port))
        data = self.json_get("/radiostatus/all")
        all_radios = []
        all_radio_eid = []
        self.max_possible_stations = 0
        self.max_2g_stations = 0
        self.max_5g_stations = 0
        self.max_6g_stations = 0
        self.max_ax_stations = 0
        self.max_ac_stations = 0
        # self.max_be_stations = 0
        phantom_radios = []
        for info in data:
            if info == "handler" or info == "uri" or info == "warnings":
                continue
            all_radio_eid.append(info)
            all_radios.append(data[info])
            if str(data[info]["phantom"]).__contains__("True"):
                phantom_radios.append(str(data[info]["entity id"]))
                logging.error("Radio is in phantom state: " + str(data[info]["entity id"]) +
                              " ,Please Contact: support@candelatech.com")
            # if str(data[info]["driver"]).__contains__("mt7925e"):
            #     self.max_possible_stations += 4
            #     self.max_2g_stations += 4 * int(str(data[info]["max_vifs"]))
            #     self.max_5g_stations += 4 * int(str(data[info]["max_vifs"]))
            #     self.max_6g_stations += 4 * int(str(data[info]["max_vifs"]))
            #     self.max_be_stations += 4 * int(str(data[info]["max_vifs"]))
            #     self.mt7925e_radios.append(info)
            if str(data[info]["driver"]).__contains__("BE200"):
                self.max_possible_stations += 1
                self.max_2g_stations += 1 * int(str(data[info]["max_vifs"]))
                self.max_5g_stations += 1 * int(str(data[info]["max_vifs"]))
                self.max_6g_stations += 1 * int(str(data[info]["max_vifs"]))
                self.max_ax_stations += 1 * int(str(data[info]["max_vifs"]))
                self.be200_radios.append(info)
            if str(data[info]["driver"]).__contains__("AX210"):
                self.max_possible_stations += 1
                self.max_2g_stations += 1 * int(str(data[info]["max_vifs"]))
                self.max_5g_stations += 1 * int(str(data[info]["max_vifs"]))
                self.max_6g_stations += 1 * int(str(data[info]["max_vifs"]))
                self.max_ax_stations += 1 * int(str(data[info]["max_vifs"]))
                self.ax210_radios.append(info)
            if str(data[info]["driver"]).__contains__("AX200"):
                self.max_possible_stations += 1 * int(str(data[info]["max_vifs"]))
                self.max_2g_stations += 1 * int(str(data[info]["max_vifs"]))
                self.max_5g_stations += 1 * int(str(data[info]["max_vifs"]))
                self.max_ax_stations += 1 * int(str(data[info]["max_vifs"]))
                self.ax200_radios.append(info)
            if str(data[info]["driver"]).__contains__("ath10k") and str(data[info]["driver"]).__contains__("(988x)"):
                self.max_possible_stations += 1 * int(str(data[info]["max_vifs"]))
                self.max_2g_stations += 1 * int(str(data[info]["max_vifs"]))
                self.max_5g_stations += 1 * int(str(data[info]["max_vifs"]))
                self.max_ac_stations += 1 * int(str(data[info]["max_vifs"]))
                self.wave1_radios.append(info)
            if str(data[info]["driver"]).__contains__("ath10k") and str(data[info]["driver"]).__contains__("(9984)"):
                if str(data[info]["capabilities"]).__contains__("802.11bgn-AC"):
                    self.max_possible_stations += 1 * int(str(data[info]["max_vifs"]))
                    self.max_2g_stations += 1 * int(str(data[info]["max_vifs"]))
                    self.max_ac_stations += 1 * int(str(data[info]["max_vifs"]))
                    self.wave2_2g_radios.append(info)
                if str(data[info]["capabilities"]).__contains__("802.11an-AC"):
                    self.max_possible_stations += 1 * int(str(data[info]["max_vifs"]))
                    self.max_5g_stations += 1 * int(str(data[info]["max_vifs"]))
                    self.max_ac_stations += 1 * int(str(data[info]["max_vifs"]))
                    self.wave2_5g_radios.append(info)
            if str(data[info]["driver"]).__contains__("mt7915e"):
                self.max_possible_stations += 1 * int(str(data[info]["max_vifs"]))
                self.max_2g_stations += 1 * int(str(data[info]["max_vifs"]))
                self.max_5g_stations += 1 * int(str(data[info]["max_vifs"]))
                self.max_ax_stations += 1 * int(str(data[info]["max_vifs"]))
                self.mtk_radios.append(info)
        logging.info("Radio Information is Extracted")
        logging.info("Available Radios: " + str(all_radio_eid) + "  -  Phantom Radios: " + str(phantom_radios))
        logging.info("max_possible_stations: " + str(self.max_possible_stations))
        logging.info("max_2g_stations: " + str(self.max_2g_stations))
        logging.info("max_5g_stations: " + str(self.max_5g_stations))
        logging.info("max_6g_stations: " + str(self.max_6g_stations))
        logging.info("max_ax_stations: " + str(self.max_ax_stations))
        logging.info("max_ac_stations: " + str(self.max_ac_stations))

    def load_scenario(self):
        self.local_realm.load(self.manager_default_db)

    def setup_connectivity_port(self, data=None):
        """setting up ethernet port"""
        if len(data) == 0:
            return
        for eth_port in data:
            if data[eth_port]["addressing"] == "dhcp-server":
                return
            elif data[eth_port]["addressing"] == "static":
                try:
                    data = {
                        "shelf": eth_port.split(".")[0],
                        "resource": eth_port.split(".")[1],
                        "port": eth_port.split(".")[2],
                        "ip_addr": data[eth_port]["ip"].split("/")[0],
                        "netmask": data[eth_port]["ip_mask"],
                        "gateway": data[eth_port]["gateway_ip"].split("/")[0],
                        "dns_servers": data[eth_port]["dns_servers"],
                        "current_flags": 562949953421312,
                        "interest": 0x401e

                    }
                    self.json_post("/cli-json/set_port", data)
                    time.sleep(1)
                except Exception as e:
                    logging.error(e)
            elif data[eth_port]["addressing"] == "dynamic":
                try:
                    data = {
                        "shelf": eth_port.split(".")[0],
                        "resource": eth_port.split(".")[1],
                        "port": eth_port.split(".")[2],
                        "current_flags": 2147483648,
                        "interest": 16384
                    }
                    self.json_post("/cli-json/set_port", data)
                    time.sleep(1)
                except Exception as e:
                    logging.error(e)

    def create_dhcp_bridge(self):
        """ create chamber view scenario for DHCP-Bridge"""
        self.setup_connectivity_port(data=self.wan_ports)
        self.setup_connectivity_port(data=self.lan_ports)
        self.setup_connectivity_port(data=self.uplink_nat_ports)
        for wan_ports, uplink_nat_ports in zip(self.wan_ports, self.uplink_nat_ports):
            upstream_port = wan_ports
            upstream_resources = upstream_port.split(".")[0] + "." + upstream_port.split(".")[1]
            uplink_port = uplink_nat_ports
            uplink_resources = uplink_port.split(".")[0] + "." + uplink_port.split(".")[1]
            uplink_subnet = self.uplink_nat_ports[uplink_nat_ports]["ip"]
            gateway_ip = self.uplink_nat_ports[uplink_nat_ports]["gateway_ip"]
            dut_obj = DUT(lfmgr=self.manager_ip,
                          port=self.manager_http_port,
                          dut_name="upstream",
                          lan_port=gateway_ip)
            dut_obj.setup()
            dut_obj.add_ssids()
            # dut_obj.show_text_blob(None, None, True)  # Show changes on GUI
            # dut_obj.sync_cv()
            # time.sleep(2)
            # dut_obj.sync_cv()
            self.default_scenario_raw_lines.append(["profile_link " + upstream_resources + " upstream-dhcp 1 NA NA " +
                                                    upstream_port.split(".")[2] + ",AUTO -1 NA"])
            self.default_scenario_raw_lines.append(
                ["profile_link " + uplink_resources + " uplink-nat 1 'DUT: upstream LAN "
                 + gateway_ip
                 + "' NA " + uplink_port.split(".")[2] + "," + upstream_port.split(".")[2] + " -1 NA"])
        return self.default_scenario_raw_lines

    def create_dhcp_external(self):
        self.setup_connectivity_port(data=self.wan_ports)
        self.setup_connectivity_port(data=self.lan_ports)
        for wan_port in self.wan_ports:
            upstream_port = wan_port
            upstream_resources = upstream_port.split(".")[0] + "." + upstream_port.split(".")[1]
            self.default_scenario_raw_lines.append(["profile_link " + upstream_resources + " upstream 1 NA NA " +
                                                    upstream_port.split(".")[2] + ",AUTO -1 NA"])
        return self.default_scenario_raw_lines

    def json_get(self, _req_url="/"):
        cli_base = LFCliBase(_lfjson_host=self.manager_ip, _lfjson_port=self.manager_http_port)
        json_response = cli_base.json_get(_req_url=_req_url)
        return json_response

    def json_post(self, _req_url="/", data=None):
        cli_base = LFCliBase(_lfjson_host=self.manager_ip, _lfjson_port=self.manager_http_port)
        json_response = cli_base.json_post(_req_url=_req_url, _data=data)
        return json_response

    def read_cv_scenario(self):
        cv_obj = cv_test(lfclient_host=self.manager_ip, lfclient_port=self.manager_http_port)
        cv_obj.show_text_blob(type="Last-Built-Scenario")
        data = self.json_get("/text/Last-Built-Scenario.last_built")
        data = data['record']['text'].split("\n")
        for d in data:
            if "scenario-name" in d:
                self.default_scenario_name = d.split(":")[1][1:]
        cv_obj.apply_cv_scenario(self.default_scenario_name)
        time.sleep(2)
        cv_obj.show_text_blob(type="Network-Connectivity")
        data = self.json_get("/text/Network-Connectivity." + str(self.default_scenario_name))
        data = data["record"]["text"].split("\n")
        for d in data:
            self.temp_raw_lines = self.default_scenario_raw_lines.copy()
            if "profile_link" in d:
                self.temp_raw_lines.append([d])
        logging.info("Saved default CV Scenario details: " + str(self.temp_raw_lines))

    def setup_interfaces(self, ssid="", bssid="", passkey="", encryption="", band=None, vlan_id=None, mode=None,
                         num_sta=None, dut_data_=None, channel=0):
        logging.info("dut_data_ in setup_interfaces: " + str(dut_data_))
        if dut_data_ is None:
            pytest.skip("No DUT data received")
        if band not in ["twog", "fiveg", "sixg"]:
            pytest.skip("Unsupported Band Selected: " + str(band))
        if mode not in ["BRIDGE", "NAT-WAN", "NAT-LAN", "VLAN"]:
            pytest.skip("Unsupported Mode Selected: " + str(mode))
        r_val = dict()
        for dut in self.dut_data:
            r_val[dut["identifier"]] = None
        for i in r_val:
            r_val[i] = dict.fromkeys(["ssid", "bssid", "passkey", "encryption", "upstream_port",
                                      "upstream_resource", "upstream", "station_data", "sniff_radio_2g",
                                      "sniff_radio_5g", "sniff_radio_6g"])
        if mode == "BRIDGE":
            ret = self.get_wan_upstream_ports()
            for dut in r_val:
                if ret.keys().__contains__(dut) and ret[dut] is not None:
                    upstream_data = (ret[dut]).split(".")
                    r_val[dut]["upstream_port"] = ret[dut]
                    upstream_resource = upstream_data[1]
                    r_val[dut]["upstream_resource"] = upstream_resource
                    upstream_data.pop(0)
                    upstream_data.pop(0)
                    upstream = ".".join(upstream_data)
                    r_val[dut]["upstream"] = upstream
                else:
                    r_val.pop(dut)
        if mode == "NAT-WAN":
            ret = self.get_wan_upstream_ports()
            for dut in r_val:
                if ret.keys().__contains__(dut) and ret[dut] is not None:
                    upstream_data = (ret[dut]).split(".")
                    r_val[dut]["upstream_port"] = ret[dut]
                    upstream_resource = upstream_data[1]
                    r_val[dut]["upstream_resource"] = upstream_resource
                    upstream_data.pop(0)
                    upstream_data.pop(0)
                    upstream = ".".join(upstream_data)
                    r_val[dut]["upstream"] = upstream
                else:
                    r_val.pop(dut)
        if mode == "NAT-LAN":
            ret = self.get_lan_upstream_ports()
            temp = r_val.copy()
            for dut in temp:
                if ret.keys().__contains__(dut) and ret[dut] is not None:
                    upstream_data = (ret[dut]).split(".")
                    r_val[dut]["upstream_port"] = ret[dut]
                    upstream_resource = upstream_data[1]
                    r_val[dut]["upstream_resource"] = upstream_resource
                    upstream_data.pop(0)
                    upstream_data.pop(0)
                    upstream = ".".join(upstream_data)
                    r_val[dut]["upstream"] = upstream
                else:
                    r_val.pop(dut)
        if mode == "VLAN":
            if vlan_id is None:
                logging.error("VLAN ID is Unspecified in the VLAN Case")
                pytest.skip("VLAN ID is Unspecified in the VLAN Case")
            else:
                self.add_vlan(vlan_ids=vlan_id)
                ret = self.get_wan_upstream_ports()
                for dut in r_val:
                    if ret.keys().__contains__(dut) and ret[dut] is not None:
                        upstream_data = (ret[dut] + "." + str(vlan_id[0])).split(".")
                        r_val[dut]["upstream_port"] = ret[dut] + "." + str(vlan_id[0])
                        upstream_resource = upstream_data[1]
                        r_val[dut]["upstream_resource"] = upstream_resource
                        upstream_data.pop(0)
                        upstream_data.pop(0)
                        upstream = ".".join(upstream_data)
                        r_val[dut]["upstream"] = upstream
                    else:
                        r_val.pop(dut)
        dict_all_radios_2g = {
                              # "mt7925e_radios":self.mt7925e_radios,
                              "be200_radios": self.be200_radios,
                              "mtk_radios": self.mtk_radios,
                              "ax210_radios": self.ax210_radios,
                              "wave2_2g_radios": self.wave2_2g_radios,
                              "wave1_radios": self.wave1_radios,
                              "ax200_radios": self.ax200_radios
                              }

        dict_all_radios_5g = {
                              # "mt7925e_radios":self.mt7925e_radios,
                              "be200_radios": self.be200_radios,
                              "mtk_radios": self.mtk_radios,
                              "ax210_radios": self.ax210_radios,
                              "wave2_5g_radios": self.wave2_5g_radios,
                              "wave1_radios": self.wave1_radios,
                              "ax200_radios": self.ax200_radios
                              }

        dict_all_radios_6g = {
                              # "mt7925e_radios":self.mt7925e_radios,
                              "be200_radios": self.be200_radios,
                              "ax210_radios": self.ax210_radios}

        max_station_per_radio = {"wave2_2g_radios": 64, "wave2_5g_radios": 64, "wave1_radios": 64, "mtk_radios": 19,
                                 "ax200_radios": 1, "ax210_radios": 1, "be200_radios": 1}
        radio_data = {}
        sniff_radio = ""

        sta_prefix = ""
        data_dict = {}
        # deleting existing stations and layer 3
        # self.pre_cleanup()
        data_dict["sniff_radio_2g"] = None
        data_dict["sniff_radio_5g"] = None
        data_dict["sniff_radio_6g"] = None
        if band == "twog":
            sta_prefix = self.twog_prefix
            data_dict["sta_prefix"] = sta_prefix
            # checking station compitality of lanforge
            if int(num_sta) > int(self.max_2g_stations):
                logging.error("Can't create %s stations on lanforge" % num_sta)
                pytest.skip("Can't create %s stations on lanforge" % num_sta)
            # checking atleast one 2g radio is available or not
            elif len(self.wave2_2g_radios) == 0 and len(self.wave1_radios) == 0 and len(self.ax210_radios) == 0 and len(
                    self.ax200_radios) == 0 and len(self.mtk_radios) == 0 and len(self.be200_radios) == 0:
                logging.error("Twog radio is not available")
                pytest.skip("Twog radio is not available")
            # radio and station selection
            stations = num_sta
            for j in dict_all_radios_2g:
                max_station = max_station_per_radio[j]
                if stations > 0:
                    if len(dict_all_radios_2g[j]) > 0:
                        diff = max_station - stations
                        for i in dict_all_radios_2g[j]:
                            if diff >= 0:
                                radio_data[i] = stations
                                stations = 0
                                break
                            elif diff < 0:
                                radio_data[i] = max_station
                                stations = stations - max_station
                                diff = max_station - stations
            sniff_radio = self.setup_sniffer(band=band, station_radio_data=radio_data)
            data_dict["sniff_radio_2g"] = sniff_radio
        if band == "fiveg":
            sta_prefix = self.fiveg_prefix
            data_dict["sta_prefix"] = sta_prefix
            # checking station compitality of lanforge
            if int(num_sta) > int(self.max_5g_stations):
                logging.error("Can't create %s stations on lanforge" % num_sta)
                pytest.skip("Can't create %s stations on lanforge" % num_sta)
            # checking atleast one 5g radio is available or not
            elif len(self.wave2_5g_radios) == 0 and len(self.wave1_radios) == 0 and len(self.ax210_radios) == 0 and len(
                    self.ax200_radios) == 0 and len(self.mtk_radios) == 0 and len(self.be200_radios) == 0:
                logging.error("fiveg radio is not available")
                pytest.skip("fiveg radio is not available")

            # radio and station selection
            stations = num_sta
            for j in dict_all_radios_5g:
                max_station = max_station_per_radio[j]
                if stations > 0:
                    if len(dict_all_radios_5g[j]) > 0:
                        diff = max_station - stations
                        for i in dict_all_radios_5g[j]:
                            if diff >= 0:
                                radio_data[i] = stations
                                stations = 0
                                break
                            elif diff < 0:
                                radio_data[i] = max_station
                                stations = stations - max_station
                                diff = max_station - stations
            # setup sniffer
            sniff_radio = self.setup_sniffer(band=band, station_radio_data=radio_data)
            data_dict["sniff_radio_5g"] = sniff_radio
        if band == "sixg":
            sta_prefix = self.sixg_prefix
            data_dict["sta_prefix"] = sta_prefix
            # checking station compatibility of lanforge
            if int(num_sta) > int(self.max_6g_stations):
                logging.error("Can't create %s stations on lanforge" % num_sta)
                pytest.skip("Can't create %s stations on lanforge" % num_sta)
            # checking atleast one 6g radio is available or not
            elif len(self.be200_radios) == 0 and len(self.ax210_radios) == 0:
                logging.error("sixg radio is not available")
                pytest.skip("sixg radio is not available")

            # radio and station selection
            stations = num_sta
            for j in dict_all_radios_6g:
                max_station = max_station_per_radio[j]
                if stations > 0:
                    if len(dict_all_radios_6g[j]) > 0:
                        diff = max_station - stations
                        for i in dict_all_radios_6g[j]:
                            if diff >= 0:
                                radio_data[i] = stations
                                stations = 0
                                break
                            elif diff < 0:
                                radio_data[i] = max_station
                                stations = stations - max_station
                                diff = max_station - stations

            sniff_radio = self.setup_sniffer(band=band, station_radio_data=radio_data)
            data_dict["sniff_radio_6g"] = sniff_radio

        dict_radio_sta_list = {}
        # list of per radio station
        length_to_split = list(radio_data.values())
        # station list of per radio
        sta_list = self.get_station_list(num_sta=num_sta, band=band)
        sta_list = iter(sta_list)
        sta_list_ = [list(islice(sta_list, elem))
                     for elem in length_to_split]
        # Checking station lists according to radios
        if len(sta_list_) == len(length_to_split):
            dict_radio_sta_list = dict(zip(list(radio_data.keys()), sta_list_))
        for i in dict_radio_sta_list:
            temp_list = []
            shelf_resource = str(i.split(".")[0] + "." + i.split(".")[1] + ".")
            for j in dict_radio_sta_list[i]:
                temp_list.append(shelf_resource + j)
            dict_radio_sta_list[i] = temp_list
        data_dict["radios"] = dict_radio_sta_list

        for i in r_val:
            r_val[i]["station_data"] = data_dict["radios"]
            r_val[i]["sta_prefix"] = data_dict["sta_prefix"]
            r_val[i]["sniff_radio_2g"] = data_dict["sniff_radio_2g"]
            r_val[i]["sniff_radio_5g"] = data_dict["sniff_radio_5g"]
            r_val[i]["sniff_radio_6g"] = data_dict["sniff_radio_6g"]
            #mode encryption and band
        if band == "twog":
            temp_band = "2G"
        elif band == "fiveg":
            temp_band = "5G"
        elif band == "sixg":
            temp_band = "6G"
        if self.run_lf:
            ssid_data_run_lf = self.run_lf_dut_data()
            for dut in self.dut_data:
                if mode != ssid_data_run_lf[dut["identifier"]]["mode"]:
                    pytest.skip("Dut is not configured in mode: " + mode)
                    #"{'706dec0a8a79': {'ssid': 'ssid_wpa_5g_br', 'bssid': '[BLANK]', 'passkey': 'something', 'encryption': 'wpa', 'upstream_port': '1.1.eth2',
                    # 'upstream_resource': '1', 'upstream': 'eth2', 'station_data': {'1.1.wiphy5': ['1.1.ath10k_5g00']},
                    # 'sniff_radio_2g': None, 'sniff_radio_5g': '1.1.wiphy0', 'sniff_radio_6g': None, 'sta_prefix': 'ath10k_5g0'}}"
                else:
                    for i in ssid_data_run_lf[dut["identifier"]]["ssid_data"]:
                        if encryption == ssid_data_run_lf[dut["identifier"]]["ssid_data"][i]["encryption"]:
                            if band == ssid_data_run_lf[dut["identifier"]]["ssid_data"][i]["band"]:
                                r_val[dut["identifier"]]["ssid"] = ssid_data_run_lf[dut["identifier"]]["ssid_data"][i]["ssid"]
                                r_val[dut["identifier"]]["passkey"] = ssid_data_run_lf[dut["identifier"]]["ssid_data"][i]["password"]
                                r_val[dut["identifier"]]["encryption"] = ssid_data_run_lf[dut["identifier"]]["ssid_data"][i]["encryption"]
                                r_val[dut["identifier"]]["bssid"] = ssid_data_run_lf[dut["identifier"]]["ssid_data"][i]["bssid"]
                                r_val[dut["identifier"]]["channel"] = ssid_data_run_lf[dut["identifier"]]["radio_data"][temp_band]["channel"]
                    if r_val[dut["identifier"]]["ssid"] is None:
                        logging.warning("Required combination: " + temp_band + ", " + encryption + " is not available")

                        pytest.skip("Expected ssid configuration is not available in DUT")
        else:
            for dut in self.dut_data:
                ssid_data = []
                if r_val.keys().__contains__(dut["identifier"]):
                    r_val[dut["identifier"]]["ssid"] = ssid
                    r_val[dut["identifier"]]["passkey"] = passkey
                    r_val[dut["identifier"]]["encryption"] = encryption
                    r_val[dut["identifier"]]["bssid"] = bssid
                    r_val[dut["identifier"]]["channel"] = channel
                    if str(encryption).upper() == "OPEN":
                        ssid_data.append(['ssid_idx=0 ssid=' + ssid])
                                          # ' bssid=' + str(bssid).upper()
                    else:
                        ssid_data.append(['ssid_idx=0 ssid=' + ssid +
                                          ' security=' + str(encryption).upper() +
                                          ' password=' + passkey])
                                          # ' bssid=' + str(bssid).upper()])

                    if str(encryption).upper() in ["OPEN", "WPA", "WPA2", "WPA3", "WEP"]:
                        self.update_duts(identifier=dut["identifier"], ssid_data=ssid_data)
        return r_val

    def update_duts(self, identifier=0, ssid_data=[]):
        for dut_obj in self.dut_objects:
            if identifier == dut_obj.dut_name:
                dut_obj.ssid = ssid_data
                dut_obj.add_ssids()
            # SSID data should be in this format
            # [
            # ['ssid_idx=0 ssid=Default-SSID-2g security=WPA|WEP| password=12345678 bssid=90:3c:b3:94:48:58'],
            # ['ssid_idx=1 ssid=Default-SSID-5gl password=12345678 bssid=90:3c:b3:94:48:59']
            #  ]

    def setup_relevent_profiles(self):
        """ TODO
             Read all Profiles
             Create upstream-dhcp and uplink-nat profile if they don't exists
             Create VLAN Based profiles
             Create 2 Profiles for vlan
             vlan profile with dhcp server
             vlan profile without dhcp server
        """
        profile_utility_obj = ProfileUtility(lfclient_host=self.manager_ip, lfclient_port=self.manager_http_port)
        # Read all Profiles
        all_profiles = profile_utility_obj.show_profile()
        logging.info("Profiles: " + str(all_profiles))

        # Create upstream-dhcp and uplink-nat profile if they don't exists
        # Checking availability of upstream-dhcp profile
        try:
            upstream_dhcp = profile_utility_obj.check_profile(profile_name="upstream-dhcp")
            # Checking availability of uplink-nat profile
            uplink_nat = profile_utility_obj.check_profile(profile_name="uplink-nat")
        except Exception as e:
            upstream_dhcp = True
            uplink_nat = True
            pass
        if upstream_dhcp:
            logging.info("upstream_dhcp profile: Available")
            profile_utility_obj.remove_profile(name="upstream-dhcp")
            profile_utility_obj.add_profile(profile_name="upstream-dhcp", profile_type="upstream",
                                            profile_flags="DHCP-SERVER")
        else:
            profile_utility_obj.add_profile(profile_name="upstream-dhcp", profile_type="upstream",
                                            profile_flags="DHCP-SERVER")
        if uplink_nat:
            profile_utility_obj.remove_profile(name="uplink-nat")
            profile_utility_obj.add_profile(profile_name="uplink-nat", profile_type="uplink", profile_flags="NAT")
        else:
            profile_utility_obj.add_profile(profile_name="uplink-nat", profile_type="uplink", profile_flags="NAT")

        # Create VLAN Based profiles
        if self.scenario == "dhcp-bridge":
            try:
                vlan_dhcp_profile = profile_utility_obj.check_profile(profile_name="vlan_dhcp_profile")
            except Exception as e:
                vlan_dhcp_profile = True

            if vlan_dhcp_profile:
                profile_utility_obj.remove_profile(name="vlan_dhcp_profile")
                profile_utility_obj.add_profile(profile_name="vlan_dhcp_profile", profile_type="vlan",
                                                profile_flags="DHCP-SERVER")
            else:
                profile_utility_obj.add_profile(profile_name="vlan_dhcp_profile", profile_type="vlan",
                                                profile_flags="DHCP-SERVER")

        elif self.scenario == "dhcp-external":
            try:
                vlan_profile = profile_utility_obj.check_profile(profile_name="vlan_profile")
            except Exception as e:
                vlan_profile = True
            if vlan_profile:
                profile_utility_obj.remove_profile(name="vlan_profile")
                profile_utility_obj.add_profile(profile_name="vlan_profile", profile_type="vlan", profile_flags=None)
            else:
                profile_utility_obj.add_profile(profile_name="vlan_profile", profile_type="vlan", profile_flags=None)

    def pre_cleanup(self):
        """ deleting existing stations and layer 3 connections """
        logging.info("Checking existing stations and layer3 connections...")
        exist_sta = []
        for u in self.json_get("/port/?fields=port+type,alias")['interfaces']:
            if list(u.values())[0]['port type'] not in ['Ethernet', 'WIFI-Radio', 'NA']:
                exist_sta.append(list(u.keys())[0])
        if len(exist_sta) == 0:
            logging.info("Existing stations are not available")
        else:
            for port_eid in exist_sta:
                self.local_realm.rm_port(port_eid, check_exists=True)
                time.sleep(0.3)
            logging.warning("Deleting existing stations")
            logging.info("Deleted %s Stations" % exist_sta)

        # deleting the previously created traffic
        try:
            exist_l3 = list(filter(lambda cx_name: cx_name if (cx_name != 'handler' and cx_name != 'uri') else False,
                                   self.json_get("/cx/?fields=name")))
            if len(exist_l3) == 0 or exist_l3[0] == "empty":
                logging.info("Existing layer3 and endp  are not available")
            else:
                list(map(lambda i: self.local_realm.rm_cx(cx_name=i), exist_l3))
                list(map(lambda cx_name: [self.local_realm.rm_endp(ename=i) for i in [f"{cx_name}-A", f"{cx_name}-B"]],
                         exist_l3))
        except Exception as e:
            logging.error(e)

    def nametoresource(self, name=None):
        """Returns resource number"""
        if name is not None:
            resource = name.split(".")[1]
            return resource
        else:
            logging.error("Name is not provided")

    def get_wan_upstream_ports(self):
        """finding upstream wan ports"""
        r_val = dict()
        for dut in self.dut_data:
            r_val[dut["identifier"]] = None
            if dut["wan_port"] is not None:
                if dut["wan_port"] in self.lanforge_data["wan_ports"].keys():
                    r_val[dut["identifier"]] = dut["wan_port"]
        return r_val

    def get_lan_upstream_ports(self):
        """finding upstream wan ports"""
        r_val = dict()
        for dut in self.dut_data:
            r_val[dut["identifier"]] = None
            if dut["lan_port"] is not None:
                if dut["lan_port"] in self.lanforge_data["lan_ports"].keys():
                    r_val[dut["identifier"]] = dut["lan_port"]
        return r_val

    def setup_sniffer(self, band=None, station_radio_data=None):
        """Setup sniff radio"""
        sniff_radio = None
        if band == "twog":
            all_radio_2g = (self.wave2_2g_radios + self.wave1_radios + self.mtk_radios + self.ax200_radios +
                            self.be200_radios + self.ax210_radios)
            logging.info("All 2g radios" + str(all_radio_2g))
            left_radio = list(set(all_radio_2g) - set(list(station_radio_data.keys())))
            if len(left_radio) == 0:
                sniff_radio = None
                logging.error("Radios are not available for sniffing")
            else:
                sniff_radio = left_radio[0]
        elif band == "fiveg":
            all_radio_5g = (self.wave2_5g_radios + self.wave1_radios + self.mtk_radios + self.ax200_radios
                            + self.be200_radios + self.ax210_radios)
            logging.info("All 5g radios" + str(all_radio_5g))
            left_radio = list(set(all_radio_5g) - set(list(station_radio_data.keys())))
            if len(left_radio) == 0:
                sniff_radio = None
                logging.error("Radios are not available for sniffing")
            else:
                sniff_radio = left_radio[0]
        elif band == "sixg":
            all_radio_6g = self.be200_radios + self.ax210_radios
            logging.info("All 6g radios" + str(all_radio_6g))
            left_radio = list(set(all_radio_6g) - set(list(station_radio_data.keys())))
            if len(left_radio) == 0:
                sniff_radio = None
                logging.error("Radios are not available for sniffing")
            else:
                sniff_radio = left_radio[0]
        return sniff_radio

    def scan_ssid(self, radio="", retry=1, allure_attach=True, scan_time=15, ssid=None, ssid_channel=None):
        '''This method for scan ssid data'''
        count = 0
        sta_list = []
        sta_name = str(radio.split(".")[0]) + "." + str(radio.split(".")[1]) + "." + "sta_scan000"
        sta_list.append(sta_name)
        logging.info("scan station: " + str(sta_list))
        for i in range(retry + 1):
            list_data = []
            obj_scan = StaScan(host=self.manager_ip, port=self.manager_http_port, ssid="fake ssid", security="open",
                               password="[BLANK]", radio=radio, sta_list=sta_list, csv_output="scan_ssid.csv",
                               scan_time=scan_time)
            # obj_scan.pre_cleanup()
            time1 = datetime.now()
            first = time.mktime(time1.timetuple()) * 1000
            obj_scan.build()
            obj_scan.start()
            time2 = datetime.now()
            second = time.mktime(time2.timetuple()) * 1000
            diff = int(second - first)
            try:
                with open(obj_scan.csv_output, 'r') as file:
                    reader = csv.reader(file)
                    for row in reader:
                        if row[1] == "age":
                            list_data.append(row)
                            continue
                        elif int(row[1]) < diff:
                            list_data.append(row)
            except Exception as e:
                logging.error(e)
            report_obj = Report()
            csv_data_table = report_obj.table2(list_data)
            # allure.attach(name="scan_ssid_data", body=csv_data_table)
            if allure_attach:
                if i == 0:
                    allure.attach(name="scan_ssid_data", body=csv_data_table)
                else:
                    allure.attach(name="scan_ssid_data_retry", body=csv_data_table)
            obj_scan.cleanup()
            if self.check_ssid_available_scan_result(scan_ssid_data=list_data, ssid=ssid):
                count = count + 1
                return list_data
        if count == 0:
            return False

    def start_sniffer(self, radio_channel=11, radio="wiphy0", test_name="sniff_radio", duration=60):
        self.pcap_name = test_name + ".pcap"
        self.pcap_obj = SniffRadio(lfclient_host=self.manager_ip, lfclient_port=self.manager_http_port, radio=radio,
                                   channel=radio_channel, monitor_name="moni3a")
        self.pcap_obj.setup(0, 0, 0)
        time.sleep(5)
        self.pcap_obj.monitor.admin_up()
        time.sleep(5)
        self.pcap_obj.monitor.start_sniff(capname=self.pcap_name, duration_sec=duration)

    def stop_sniffer(self, sta_list=[]):
        self.pcap_obj.monitor.admin_down()
        time.sleep(2)
        self.pcap_obj.cleanup()
        try:
            lf_report.pull_reports(hostname=self.manager_ip, port=self.manager_ssh_port, username="lanforge",
                                   password="lanforge",
                                   report_location="/home/lanforge/" + self.pcap_name,
                                   report_dir=".")
            allure.attach.file(source=self.pcap_name,
                               name="pcap_file " + ", ".join(sta_list), attachment_type=allure.attachment_type.PCAP)
            logging.info("pcap file name: " + str(self.pcap_name))
            sniff_radio = self.pcap_obj.radio
            logging.info("In stop sniffer radio:- " + str(sniff_radio))
            self.set_radio_channel(radio=sniff_radio, channel="AUTO")
            logging.info("After stop sniffer, Sniff radio channel is Auto:- Done")
        except Exception as e:
            logging.error(e)

        return self.pcap_name

    def check_ssid_available_scan_result(self, scan_ssid_data=None, ssid=None):
        """This method will check ssid available or not in scan ssid data"""
        try:
            flag = False
            for i in scan_ssid_data:
                if ssid in i:
                    flag = True
            if flag:
                return True
            else:
                return False
        except Exception as e:
            logging.error(e)

    def set_radio_channel(self, radio="1.1.wiphy0", channel="AUTO", country=None, antenna=None):
        # country_code = US(840)
        try:
            radio = radio.split(".")
            shelf = radio[0]
            resource = radio[1]
            radio_ = radio[2]
            local_realm_obj = realm.Realm(lfclient_host=self.manager_ip, lfclient_port=self.manager_http_port)
            data = {
                "shelf": shelf,
                "resource": resource,
                "radio": radio_,
                "mode": "NA",
                "channel": channel
            }
            try:
                if country:  # update the dictionary
                    data["country"] = country
                if antenna:
                    data["antenna"] = antenna
            except Exception as e:
                logging.error(f"{e}\nunable to change lanforge radio country code")
            local_realm_obj.json_post("/cli-json/set_wifi_radio", _data=data)
            time.sleep(2)
        except Exception as e:
            logging.error(e)

    def get_station_data(self, rows=[], sta_name=[], allure_attach=True, allure_name="station data"):
        """
        Attach station data to allure
        e.g. rows = ["ip", "signal"] , sta_names = ["1.1.wlan0000", "1.1.wlan0001"]
        """
        # dict for station data
        sta_dict = {}
        try:
            for sta in sta_name:
                sta_url = "port/" + str(sta.split(".")[0]) + "/" + str(sta.split(".")[1]) + "/" + str(sta.split(".")[2])
                station_info = self.json_get(sta_url)
                dict_data = station_info["interface"]
                temp_dict = {}
                for i in rows:
                    temp_dict[i] = dict_data[i]
                    if i == "channel":
                        if dict_data[i] == "-1":
                            self.local_realm.reset_port(sta)
                            time.sleep(5)
                            sta_url_ = "port/" + str(sta.split(".")[0]) + "/" + str(sta.split(".")[1]) + "/" + str(
                                sta.split(".")[2])
                            station_info_ = self.json_get(sta_url_)
                            dict_data_ = station_info_["interface"]
                            logging.info("station data after port reset" + str(dict_data_))
                            temp_dict[i] = dict_data_[i]
                sta_dict[sta] = temp_dict
        except Exception as e:
            logging.error(e)
        logging.info("station info: " + str(sta_dict))
        # Creating dict for allure table
        station_table_dict = {}
        station_table_dict["station name"] = list(sta_dict.keys())
        for i in rows:
            temp_list = []
            for j in sta_name:
                temp_list.append(sta_dict[j][i])
            station_table_dict[i] = temp_list
        if allure_attach:
            self.attach_table_allure(data=station_table_dict, allure_name=allure_name)
        return sta_dict

    def get_cx_data(self, cx_name=[], cx_data=[], allure_attach=True):
        """Attach cx data to allure"""
        url = "cx/all"
        # cx_data.append("type")
        dict_cx_data = {}
        cx_json_data = self.json_get(url)
        try:
            for sta_ in cx_name:
                temp_dict = {}
                for i in cx_data:
                    temp_dict[i] = cx_json_data[sta_][i]
                dict_cx_data[sta_] = temp_dict
        except Exception as e:
            logging.error(e)
        cx_table_dict = {}
        cx_table_dict["cx name"] = list(dict_cx_data.keys())
        for i in cx_data:
            temp_list = []
            for j in cx_name:
                temp_list.append(dict_cx_data[j][i])
            if i == "bps rx a":
                cx_table_dict["Download"] = temp_list
            elif i == "bps rx b":
                cx_table_dict["Upload"] = temp_list
            elif i == "type":
                cx_table_dict["cx type"] = temp_list
        if allure_attach:
            self.attach_table_allure(data=cx_table_dict, allure_name="cx data")
        return dict_cx_data

    def get_station_list(self, num_sta=1, band="twog"):
        """Create station list"""
        sta_list = []
        for i in range(num_sta):
            if band == "twog":
                sta_list.append(self.twog_prefix + str(i))
            elif band == "fiveg":
                sta_list.append(self.fiveg_prefix + str(i))
            elif band == "sixg":
                sta_list.append(self.sixg_prefix + str(i))
            else:
                logging.error("band is wrong")
        return sta_list

    def attach_table_allure(self, data=None, allure_name=None):
        """Attach table to allure.data should be dict."""
        try:
            report_obj = Report()
            data_table = report_obj.table2(table=data, headers='keys')
            allure.attach(name=allure_name, body=data_table)
            logging.info(str("\n") + str(data_table))
        except Exception as e:
            logging.error(e)

    def create_stations(self):
        pass

    def delete_stations(self):
        pass

    def modify_station(self):
        pass

    def read_stations(self):
        pass

    def pull_reports(self):
        pass

    def get_wifi_radios(self):
        pass

    def modify_wifi_radio(self):
        pass

    def load_scenario_db(self):
        pass

    def delete_dut(self):
        pass

    def read_dut(self):
        pass

    def update_dut(self):
        pass

    def get_ethernet_ports(self):
        pass

    def set_ethernet_port(self):
        pass

    def clean_port_manager(self):
        pass

    def clean_layer3cx(self):
        pass

    def station_data_query(self, station_name=None, query=None):
        """Station data query. station name e.g 1.1.wlan0000"""
        if station_name is None or query is None:
            logging.error("Station name or query is missing")
        x = station_name.split(".")
        url = f"/port/{x[0]}/{x[1]}/{x[2]}?fields={query}"
        logging.info("url: " + str(url))
        response = self.json_get(_req_url=url)
        if (response is None) or ("interface" not in response):
            logging.info("station_list: incomplete response:")
            # pprint(response)
            pytest.skip("station_list: incomplete response:")
        y = response["interface"][query]
        return y

    def get_max_sta(self, radio=""):
        data = self.json_get("/radiostatus/all")
        return data[radio]["max_vifs"]

    def add_vlan(self, vlan_ids=[], build=True):
        self.temp_raw_lines = self.default_scenario_raw_lines.copy()
        data = self.json_get("/port/all")
        flag = 0
        profile_name = ""
        port_list = []
        vlan_raws = []
        # temp_raw_lines = self.default_scenario_raw_lines.copy()
        for port in self.wan_ports:
            for vlans in vlan_ids:
                for i in data["interfaces"]:
                    if list(i.keys())[0] != port + "." + str(vlans):
                        flag = 1
            if flag == 1:
                for vlans in vlan_ids:
                    if self.scenario == "dhcp-bridge":
                        profile_name = "vlan_dhcp_profile"
                    elif self.scenario == "dhcp-external":
                        profile_name = "vlan_profile"
                    port_list.append(str(port) + "." + str(vlans))
                    vlan_raws.append(["profile_link " + port + " " + profile_name + " 1 " + port
                                      + " NA " + port.split(".")[2] + ",AUTO -1 " + str(vlans)])
                    self.temp_raw_lines.append(["profile_link " + port + " " + profile_name + " 1 " + port
                                                + " NA " + port.split(".")[2] + ",AUTO -1 " + str(vlans)])

        if build:
            self.chamber_view(raw_lines="custom")
            time.sleep(10)
            if self.scenario == "dhcp-external":
                for port in port_list:
                    data = {
                        "shelf": port.split(".")[0],
                        "resource": port.split(".")[1],
                        "port": port.split(".")[2] + "." + port.split(".")[3],
                        "current_flags": 2147483648,
                        "interest": 16384
                    }
                    self.json_post("/cli-json/set_port", data)
                    time.sleep(2)
            time.sleep(5)
            # query and fetch vlan Ip Address
            port_data = self.json_get(_req_url="/port?fields=alias,parent+dev,port+type,ip,mac")['interfaces']
            logging.info("Port data: " + str(port_data))
            vlan_table_data = {}
            port = []
            ip = []
            parent_dev = []
            not_ip_vlans = []
            vlan_ip_fail = False
            for i in port_data:
                for item in i:
                    if i[item]['port type'] == '802.1Q VLAN' and i[item]['ip'] == '0.0.0.0':
                        vlan_ip_fail = True
                        logging.error(f"VLAN Interface - {i[item]['alias']} do not have IP")
                        port.append(item)
                        ip.append(i[item]['ip'])
                        not_ip_vlans.append(item)
                        parent_dev.append(i[item]['parent dev'])
                    elif i[item]['port type'] == '802.1Q VLAN' and i[item]['ip'] != '0.0.0.0':
                        port.append(item)
                        ip.append(i[item]['ip'])
                        parent_dev.append(i[item]['parent dev'])
            # creating dict for vlan table
            vlan_table_data["Port"] = port
            vlan_table_data["Parent Dev"] = parent_dev
            vlan_table_data["ip"] = ip
            # Attaching vlan table to allure
            self.attach_table_allure(data=vlan_table_data, allure_name="VLAN Table")
            if vlan_ip_fail:
                # Fail if Vlan don't have IP
                pytest.fail("VLAN do not have IP:-" + str(not_ip_vlans))
            return vlan_raws
        else:
            return vlan_raws

    def chamber_view(self, delete_old_scenario=True, raw_lines="default"):
        """create chamber view. raw_lines values are default | custom"""
        if delete_old_scenario:
            self.chamberview_object.clean_cv_scenario(scenario_name=self.scenario)
        # if self.scenario == "dhcp-bridge":
        #     self.create_dhcp_bridge()
        #     logging.info("Scenario name: " + str(self.scenario))
        # elif self.scenario == "dhcp-external":
        #     self.create_dhcp_external()
        #     logging.info("Scenario name: " + str(self.scenario))
        if raw_lines.lower() == "default":
            raw_lines_ = self.default_scenario_raw_lines
        elif raw_lines.lower() == "custom":
            raw_lines_ = self.temp_raw_lines
        else:
            logging.error("raw lines are wrong. Provide default or custom")
        self.chamberview_object.setup(create_scenario=self.scenario,
                                      raw_line=raw_lines_
                                      )
        logging.info("Raw Lines type: " + str(raw_lines))
        logging.info("Raw Lines: " + str(raw_lines_))
        self.chamberview_object.build(self.scenario)
        self.chamberview_object.sync_cv()
        time.sleep(2)
        self.chamberview_object.show_text_blob(None, None, True)  # Show changes on GUI
        self.chamberview_object.sync_cv()
        time.sleep(15)
        return self.chamberview_object, self.scenario

    def setup_radius_server(self, user=""):
        """
            TODO:
                setup freeradius server on lanforge and return the radius server data
                setup the radius server for basic EAP-TLS and EAP-TTLS encryptions
            Special Radius configurations can be done in later implementations
            Radius server should be working properly on WAN Interface of AP
        """
        pass

    def enable_verbose_debug(self, radio=None, enable=True):
        """Increase debug info in wpa-supplicant and hostapd logs"""
        # radio e.g 1.1wiphy0
        if radio is not None:
            shelf = radio.split(".")[0]
            resource = radio.split(".")[1]
            radio_name = radio.split(".")[2]
            if enable:
                flag_value = "0x10000"
            else:
                flag_value = "0x00000"
            data = {
                "shelf": shelf,
                "resource": resource,
                "radio": radio_name,
                "flags": flag_value
            }
            self.json_post("/cli-json/set_wifi_radio", data=data)
        else:
            logging.error("Radio name is wrong")

    def attach_report_graphs(self, report_name=None, pdf_name="WIFI Capacity Test PDF Report"):
        if report_name[-1] == "/":
            relevant_path = "../reports/" + report_name
            entries = os.listdir("../reports/" + report_name)
        else:
            relevant_path = "../reports/" + report_name + "/"
            entries = os.listdir("../reports/" + report_name + '/')
        # logging.info("GETCWD" + str(os.getcwd()))
        # logging.info("List report dict" + str(os.listdir("../reports")))
        # logging.info("CHeck Report directory" + str(os.path.exists(f"../reports/{report_name}")))
        logging.info("Entries" + str(entries))
        pdf = False
        for i in entries:
            if ".pdf" in i:
                pdf = i
        if pdf:
            allure.attach.file(source=relevant_path + pdf,
                               name=pdf_name)

        included_extensions = ['png']
        file_names = [fn for fn in os.listdir(relevant_path)
                      if any(fn.endswith(ext) for ext in included_extensions)]

        a = [item for item in file_names if 'print' not in item]
        a = [item for item in a if 'logo' not in item]
        a = [item for item in a if 'Logo' not in item]
        a = [item for item in a if 'candela' not in item]

        a.sort()
        for i in a:
            allure.attach.file(source=relevant_path + i,
                               name=i,
                               attachment_type="image/png", extension=None)

    def read_csv_individual_station_throughput(self, dir_name, option, individual_station_throughput=True,
                                               kpi_csv=False,
                                               file_name="/csv-data/data-Combined_bps__60_second_running_average-1.csv",
                                               batch_size="0"):
        try:
            df = pd.read_csv("../reports/" + str(dir_name) + file_name,
                             sep=r'\t', engine='python')
            logging.info("csv file opened")
        except FileNotFoundError:
            logging.info(f"csv file {file_name} does not exist\nTrying {file_name.replace('_bps__', '_Mbps__')}")
            try:
                df = pd.read_csv("../reports/" + str(dir_name) + file_name.replace('_bps__', '_Mbps__'),
                                 sep=r'\t', engine='python')
                logging.info("csv file opened")
            except FileNotFoundError:
                logging.info(f"csv file {file_name} does not exist")
                return False

        if kpi_csv:
            count = 0
            dict_data = {"Down": {}, "Up": {}, "Both": {}}
            csv_short_dis = df.loc[:, "short-description"]
            csv_num_score = df.loc[:, "numeric-score"]
            for i in range(len(batch_size.split(","))):
                dict_data["Down"][csv_short_dis[count + 0]] = csv_num_score[count + 0]
                dict_data["Up"][csv_short_dis[count + 1]] = csv_num_score[count + 1]
                dict_data["Both"][csv_short_dis[count + 2]] = csv_num_score[count + 2]
                count += 3

        if individual_station_throughput:
            dict_data = {}
            if option == "download":
                csv_sta_names = df.iloc[[0]].values.tolist()
                csv_throughput_values = df.iloc[[1]].values.tolist()
            elif option == "upload":
                csv_sta_names = df.iloc[[0]].values.tolist()
                csv_throughput_values = df.iloc[[2]].values.tolist()
            else:
                print("Provide proper option: download or upload")
                return
            csv_throughput_values = csv_throughput_values[0][0].split(',')
            print("Throughput Values:", csv_throughput_values)
            print("Station Names:", csv_sta_names)

            raw_sta_names = csv_sta_names[0][0].strip('"')
            sta_list = raw_sta_names.split('","')
            print("Processed Station List:", sta_list)

            if len(sta_list) != len(csv_throughput_values):
                raise ValueError("The number of station names and throughput values must match.")
            dict_data = {sta_list[i]: csv_throughput_values[i] for i in range(len(sta_list))}
        return dict_data

    def attach_report_kpi(self, report_name=None, file_name="kpi_file"):
        if report_name[-1] == "/":
            path = "../reports/" + str(report_name) + "kpi.csv"
        else:
            path = "../reports/" + str(report_name) + "/kpi.csv"
        if os.path.exists(path):
            allure.attach.file(source=path,
                               name=file_name, attachment_type="CSV")
        return os.path.exists(path)

    def get_supplicant_logs(self, radio="1.1.wiphy0", sta_list=[], attach_allure=True):
        try:
            resource = radio.split(".")[1]
            radio = radio.split(".")[2]
            ip = self.get_manager_from_resource(resource=int(resource))
            if ip is not None:
                supplicant = "/home/lanforge/wifi/wpa_supplicant_log_" + radio + ".txt"
                obj = SCP_File(ip=ip, port=22, username="root", password="lanforge",
                               remote_path=supplicant,
                               local_path=".")
                obj.pull_file()
                if attach_allure:
                    allure.attach.file(source="wpa_supplicant_log_" + radio + ".txt",
                                       name=f"wpa_supplicant_log - {radio} - {', '.join(sta_list)}")
        except Exception as e:
            logging.error("get_supplicant_logs() - Error in getting supplicant Logs: " + str(e))

    def get_resources(self):
        try:
            d = self.json_get("/port/?fields=alias,ip")
            resource_data = dict()
            for i in d["interfaces"]:
                if str(list(dict(i).keys())[0]).__contains__("eth0"):
                    resource_data[str(list(dict(i).keys())[0]).split(".")[1]] = i[str(list(dict(i).keys())[0])]["ip"]
            logging.info("Resource ID and Management port Mapping: " + str(resource_data))
        except Exception as e:
            logging.error(str(e))
        return resource_data

    def get_manager_from_resource(self, resource=1):
        resource_data = self.get_resources()
        try:
            ip = resource_data[str(resource)]
        except Exception as e:
            logging.error("Resource is Unavailable when reading manager: " + str(e))
            ip = None
        return ip

    def client_disconnect(self, station_name=[], clean_l3_traffic=False, clear_all_sta=False):
        client_dis = CreateStation(_host=self.manager_ip, _port=self.manager_http_port,
                                   _sta_list=station_name, _password="passkey", _ssid="ssid", _security="security")
        if len(station_name) > 0:
            client_dis.station_profile.cleanup(station_name)
        elif clear_all_sta:
            exist_sta = []
            for u in client_dis.json_get("/port/?fields=port+type,alias")['interfaces']:
                if list(u.values())[0]['port type'] not in ['Ethernet', 'WIFI-Radio', 'NA']:
                    exist_sta.append(list(u.keys())[0])
            client_dis.station_profile.cleanup(desired_stations=exist_sta)
        if clean_l3_traffic:
            try:
                exist_l3 = list(
                    filter(lambda cx_name: cx_name if (cx_name != 'handler' and cx_name != 'uri') else False,
                           client_dis.json_get("/cx/?fields=name")))
                list(map(lambda i: client_dis.rm_cx(cx_name=i), exist_l3))
                list(map(lambda cx_name: [client_dis.rm_endp(ename=i) for i in [f"{cx_name}-A", f"{cx_name}-B"]],
                         exist_l3))
            except Exception as e:
                logging.error(e)
        return True

    def run_lf_dut_data(self):
        """Dut data for running test cases only on lanforge"""
        ret = {}
        try:
            for i in self.dut_data:
                ret = {i["identifier"]: i["ssid"]}
        except Exception as e:
            logging.error(e)
        return ret

    def check_band_ap(self, band=None):
        """"This method will check given band ap is supporting or not"""
        temp_band = None
        if band is not None:
            if band == "twog" or band == "2G":
                temp_band = "2G"
            elif band == "fiveg" or band == "5G":
                temp_band = "5G"
            elif band == "sixg" or band == "6G":
                temp_band = "6G"
            print(self.dut_data)
            if len(self.dut_data) == 1:
                for ap in self.dut_data:
                    print(ap)
                    if temp_band not in ap["supported_bands"]:
                        logging.error("AP is not supporting " + temp_band + " Band")
                        pytest.skip("AP is not supporting " + temp_band + " Band")
            else:
                pass

    def lf_sixg_lookup_validation(self, channel=None):
        """
        This method will return ap equaivalent 6g channel for lanforge.
        channel should be ap 6g channel
        """
        ap_lanforge_6g_channel_dict = {
            1: 191,
            5: 195,
            9: 199,
            13: 203,
            17: 207,
            21: 211,
            25: 215,
            29: 219,
            33: 223,
            37: 227,
            41: 231,
            45: 235,
            49: 239,
            53: 243,
            57: 247,
            61: 251,
            65: 255,
            69: 259,
            73: 263,
            77: 267,
            81: 271,
            85: 275,
            89: 279,
            93: 283,
            97: 287,
            101: 291,
            105: 295,
            109: 299,
            113: 303,
            117: 307,
            121: 311,
            125: 315,
            129: 319,
            133: 323,
            137: 327,
            141: 331,
            145: 335,
            149: 339,
            153: 343,
            157: 347,
            161: 351,
            165: 355,
            169: 359,
            173: 363,
            177: 367,
            181: 371,
            185: 375,
            189: 379,
            193: 383,
            197: 387,
            201: 391,
            205: 395,
            209: 399,
            213: 403,
            217: 407,
            221: 411,
            225: 415,
            229: 419,
            233: 423
        }
        if channel is not None:
            channel = int(channel)
            return ap_lanforge_6g_channel_dict[channel]
        else:
            return None

    def attenuator_serial(self):
        self.obj = Attenuator(
            lfclient_host=self.manager_ip,
            lfclient_port=self.manager_http_port
        )
        val = self.obj.show()
        return val

    def attenuator_modify(self, serno, idx, val):
        atten_obj = Attenuator_modify(self.manager_ip, self.manager_http_port, serno, idx, val)
        atten_obj.build()

    def get_station_signal(self, station_name="", timeout=10):
        while timeout:
            signal = self.json_get(_req_url=f'/port/1/1/{station_name}?fields=signal')['interface']['signal']
            if signal != '0 dBm':
                break
            else:
                timeout -= 1
                time.sleep(1)
        if signal == '0 dBm':
            return False
        else:
            return signal

    def attenuator_serial_radio(self, ssid="[BLANK]", passkey="[BLANK]", security="wpa2", mode="BRIDGE", atn_val=400,
                                vlan_id=100, client_type=0, station_name=[], radio='1.1.wiphy0', timeout=20):
        # index 0 of atten_serial_radio will ser no of 1st 2g/5g radio and index 1 will ser no of 2nd and 3rd 2g/5g radio
        atten_serial_radio = []
        atten_serial = self.attenuator_serial()
        self.client_connect_using_radio(ssid=ssid, passkey=passkey, security=security, mode=mode,
                                        vlan_id=vlan_id, radio=radio, client_type=client_type,
                                        station_name=station_name)
        signal1 = self.get_station_signal(station_name[0], timeout)
        atten_sr = atten_serial[0].split(".")
        self.attenuator_modify(int(atten_sr[2]), "all", atn_val)
        time.sleep(0.5)
        signal2 = self.get_station_signal(station_name[0], timeout)
        try:
            if abs(int(signal2.split(" ")[0])) - abs(int(signal1.split(" ")[0])) >= 5:
                atten_serial_radio = atten_serial
            else:
                atten_serial_radio = atten_serial[::-1]
            return atten_serial_radio
        except Exception as e:
            logging.error(f"{e}")
            return False
        finally:
            self.client_disconnect(station_name=station_name)

    def read_kpi_file(self, column_name, dir_name):
        if column_name == None:
            df = pd.read_csv("../reports/" + str(dir_name) + "/kpi.csv", sep=r'\t', engine='python')
            if df.empty == True:
                return "empty"
            else:
                return df
        else:
            df = pd.read_csv("../reports/" + str(dir_name) + "/kpi.csv", sep=r'\t', usecols=column_name,
                             engine='python')
            if df.empty == True:
                return "empty"
            else:
                result = df[column_name].values.tolist()
                return result

    def monitor(self, duration_sec, monitor_interval, created_cx, col_names, iterations, side_a_min_rate=0,
                side_b_min_rate=0):
        try:
            duration_sec = self.local_realm.parse_time(duration_sec).seconds
        except:
            if (duration_sec is None) or (duration_sec <= 1):
                raise ValueError("L3CXProfile::monitor wants duration_sec > 1 second")
            if (duration_sec <= monitor_interval):
                raise ValueError("L3CXProfile::monitor wants duration_sec > monitor_interval")
        if created_cx == None:
            raise ValueError("Monitor needs a list of Layer 3 connections")
        if (monitor_interval is None):
            raise ValueError("L3CXProfile::monitor wants monitor_interval ")

        # monitor columns
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=duration_sec)
        # bps-rx-a (download) and bps-rx-b(upload) values are taken
        self.bps_rx_a, self.bps_rx_b, self.bps_rx, index = [], [], {}, -1
        bps_rx_a_avg, bps_rx_b_avg = [], []
        [(self.bps_rx_a.append([]), self.bps_rx_b.append([])) for i in range(len(created_cx))]
        for test in range(1 + iterations):
            while datetime.now() < end_time:
                index += 1
                response = list(
                    self.json_get('/cx/%s?fields=%s' % (','.join(created_cx), ",".join(col_names))).values())[2:]
                self.bps_rx[index] = list(map(lambda i: [float(f"{x / (1E6):.2f}") for x in i.values()], response))
                time.sleep(monitor_interval)
        # bps_rx list is calculated
        print("rx rate values are with [bps-rx-a, bps-rx-b] :-\n", self.bps_rx, "\n\n")
        for index, key in enumerate(self.bps_rx):
            for i in range(len(self.bps_rx[key])):
                if side_b_min_rate != '0' and side_b_min_rate != 0:
                    self.bps_rx_a[i].append(self.bps_rx[key][i][0])
                if side_a_min_rate != '0' and side_a_min_rate != 0:
                    self.bps_rx_b[i].append(self.bps_rx[key][i][1])
        print(f"bps-rx-a values-: \n{self.bps_rx_a}\nbps-rx-b values-: \n{self.bps_rx_b}")
        if side_a_min_rate != '0' and side_a_min_rate != 0:
            bps_rx_b_avg = [float(f"{sum(i) / len(i): .2f}") for i in self.bps_rx_b]
        if side_b_min_rate != '0' and side_b_min_rate != 0:
            bps_rx_a_avg = [float(f"{sum(i) / len(i): .2f}") for i in self.bps_rx_a]
        return bps_rx_a_avg, bps_rx_b_avg

    def create_layer3(self, side_a_min_rate=0, side_a_max_rate=0, side_b_min_rate=0, side_b_max_rate=0,
                      traffic_type="", sta_list=[], side_b="", start_cx=True, prefix=None):
        # checked
        if side_b == "":
            side_b = self.wan_ports
            side_b_ = list(side_b.keys())
            side_b = side_b_[0]
        local_realm = realm.Realm(lfclient_host=self.manager_ip, lfclient_port=self.manager_http_port)
        cx_profile = local_realm.new_l3_cx_profile()
        cx_profile.host = self.manager_ip
        cx_profile.port = self.manager_http_port
        layer3_cols = ['name', 'tx bytes', 'rx bytes', 'tx rate', 'rx rate']
        cx_profile.side_a_min_bps = side_a_min_rate
        cx_profile.side_a_max_bps = side_a_max_rate
        cx_profile.side_b_min_bps = side_b_min_rate
        cx_profile.side_b_max_bps = side_b_max_rate
        if prefix:
            cx_profile.name_prefix = prefix
        # create
        cx_profile.create(endp_type=traffic_type, side_a=sta_list, side_b=side_b, sleep_time=0, prefix=prefix)
        if start_cx:
            cx_profile.start_cx()

    def start_cx(self):
        local_realm = realm.Realm(lfclient_host=self.manager_ip, lfclient_port=self.manager_http_port)
        cx_profile = local_realm.new_l3_cx_profile()
        cx_profile.start_cx()

    def l3_cleanup(self):
        local_realm = realm.Realm(lfclient_host=self.manager_ip, lfclient_port=self.manager_http_port)
        local_realm.remove_all_cxs(remove_all_endpoints=True)

    def get_cx_list(self):
        local_realm = realm.Realm(lfclient_host=self.manager_ip, lfclient_port=self.manager_http_port)
        layer3_result = local_realm.cx_list()
        layer3_names = [item["name"] for item in layer3_result.values() if "_links" in item]
        print(layer3_names)
        return layer3_names

    def start_cx_list(self, created_cx=None, check_run_status=True):
        local_realm = realm.Realm(lfclient_host=self.manager_ip, lfclient_port=self.manager_http_port)
        cx_profile = local_realm.new_l3_cx_profile()
        cx_profile.host = self.manager_ip
        cx_profile.port = self.manager_http_port
        cx_profile.created_cx = created_cx
        cx_profile.start_cx()
        time.sleep(20)
        if check_run_status:
            timeout = 50
            while timeout:
                timeout -= 1
                check_run_state = list(self.json_get('/cx/%s?fields=%s' % (','.join(
                    cx_profile.created_cx.keys()), ",".join(['bps rx a', 'bps rx b']))).values())[2:]
                for i in check_run_state:
                    if list(i.values()).count(0) != len(i):
                        timeout = 0
                        break

    def allure_report_table_format(self, dict_data=None, key=None, value=None,
                                   name=None):  #, value_on_same_table=True):
        report_obj = Report()
        data_table, dict_table = "", {}
        dict_table[key] = list(dict_data.keys())
        dict_table[value] = list(dict_data.values())
        try:
            data_table = report_obj.table2(table=dict_table, headers='keys')
        except Exception as e:
            print(e)
        if name is not None:
            allure.attach(name=name, body=str(data_table))

    def get_radio_availabilities(self, num_stations_2g: int = 0, num_stations_5g: int = 0) -> tuple:
        """
        Get the port name of radios and how many stations to be created on each radio for the given num of
        2g stations and 5g stations. This method takes in account the fact that same radio can't be used to
        create a station on multiple band at the same time even though it supports both bands.

        - Returns tuple[dict[str, int], dict[str, int]] or skips the test if not enough radios are available
        for the requested number of stations.
        """
        message = None
        requested_num_stations_2g = num_stations_2g
        requested_num_stations_5g = num_stations_5g

        radio_dict_2g = {}
        radio_dict_5g = {}
        dict_all_radios_2g = {
            "wave2_2g_radios": self.wave2_2g_radios,
            "wave1_radios": self.wave1_radios,
            "mtk_radios": self.mtk_radios,
            "ax200_radios": self.ax200_radios,
            "be200_radios": self.be200_radios,
            "ax210_radios": self.ax210_radios
        }
        dict_all_radios_5g = {
            "wave2_5g_radios": self.wave2_5g_radios,
            "wave1_radios": self.wave1_radios,
            "mtk_radios": self.mtk_radios,
            "ax200_radios": self.ax200_radios,
            "be200_radios": self.be200_radios,
            "ax210_radios": self.ax210_radios
        }
        max_station_per_radio = {
            "wave2_2g_radios": 64,
            "wave2_5g_radios": 64,
            "wave1_radios": 64,
            "mtk_radios": 19,
            "ax200_radios": 1,
            "be200_radios": 1,
            "ax210_radios": 1
        }

        for i in range(2):
            if num_stations_2g > num_stations_5g:
                for keys in dict_all_radios_2g:
                    if num_stations_2g == 0:
                        break
                    max_station = max_station_per_radio[keys]
                    if len(dict_all_radios_2g[keys]) > 0:
                        diff = max_station - num_stations_2g
                        for port_name in dict_all_radios_2g[keys]:
                            if port_name in radio_dict_5g:
                                continue
                            if diff >= 0:
                                radio_dict_2g[port_name] = num_stations_2g
                                num_stations_2g = 0
                                break
                            else:
                                radio_dict_2g[port_name] = max_station
                                num_stations_2g -= max_station
                                diff = max_station - num_stations_2g
                if num_stations_2g != 0:
                    if i == 0:
                        message = f"Not enough radios available for connecting {requested_num_stations_2g} 2g clients!"
                    break
            else:
                for keys in dict_all_radios_5g:
                    if num_stations_5g == 0:
                        break
                    max_station = max_station_per_radio[keys]
                    if len(dict_all_radios_5g[keys]) > 0:
                        diff = max_station - num_stations_5g
                        for port_name in dict_all_radios_5g[keys]:
                            if port_name in radio_dict_2g:
                                continue
                            if diff >= 0:
                                radio_dict_5g[port_name] = num_stations_5g
                                num_stations_5g = 0
                                break
                            else:
                                radio_dict_5g[port_name] = max_station
                                num_stations_5g -= max_station
                                diff = max_station - num_stations_5g
                if num_stations_5g != 0:
                    if i == 0:
                        message = f"Not enough radios available for connecting {requested_num_stations_5g} 5g clients!"
                    break

        if num_stations_2g != 0 or num_stations_5g != 0:
            logging.info(f"Radio-2G-Stations dict : {num_stations_2g}")
            logging.info(f"Radio-5G-Stations dict : {num_stations_5g}")
            if message is None:
                message = (f"Not enough radios available for connecting {requested_num_stations_2g} 2g clients and "
                           f"{requested_num_stations_5g} 5g clients simultaneously!")
            logging.info(message)
            pytest.skip(message)

        return radio_dict_2g, radio_dict_5g

    def client_connect_using_radio(self, ssid="[BLANK]", passkey="[BLANK]", security="wpa2", mode="BRIDGE", band=None,
                                   vlan_id=[None], radio=None, client_type=0, station_name=[], dut_data=None,
                                   sniff_radio=False, create_vlan=True, attach_port_info=True,
                                   attach_station_data=True, timeout_sec=100):
        # pre cleanup
        # if pre_cleanup:
        #     self.pre_cleanup()
        global upstream_port, sniffer_channel
        if mode == "BRIDGE" or mode == "NAT-WAN":
            port_data = self.wan_ports
            port = list(port_data.keys())
            upstream_port = port[0]
        elif mode == "VLAN":
            if vlan_id is None:
                logging.error("VLAN ID is Unspecified in the VLAN Case")
                pytest.skip("VLAN ID is Unspecified in the VLAN Case")
            else:
                up = self.get_wan_upstream_ports()
                upstream = list(up.values())
                upstream_port = upstream[0] + "." + str(vlan_id[0])
                if create_vlan:
                    self.add_vlan(vlan_ids=vlan_id, build=True)
                else:
                    self.add_vlan(vlan_ids=vlan_id, build=False)
        print("upstream_port1:", upstream_port)

        client_connect = CreateStation(_host=self.manager_ip, _port=self.manager_http_port, _mode=client_type,
                                       _sta_list=station_name, _password=passkey, _ssid=ssid, _security=security)
        client_connect.upstream_port = upstream_port
        client_connect.upstream_resource = 1
        client_connect.radio = radio
        if attach_port_info is True:
            # allure attach for port info
            port_data = self.json_get(_req_url="port?fields=ip")
            port_info = {key: value for d in port_data["interfaces"] for key, value in d.items()}
            self.allure_report_table_format(dict_data=port_info, key="Port Names", value="ip", name="Port info")
        if sniff_radio:
            for dut_ in self.dut_data:
                identifier = dut_["identifier"]
                if dut_data.keys().__contains__(identifier):
                    if band == "twog":
                        sniffer_channel = dict(dut_data.get(identifier)["radio_data"])["2G"]["channel"]
                    elif band == "fiveg":
                        sniffer_channel = dict(dut_data.get(identifier)["radio_data"])["5G"]["channel"]
                    elif band == "sixg":
                        sniffer_channel = dict(dut_data.get(identifier)["radio_data"])["6G"]["channel"]
                    sniff_radio = self.setup_sniffer(band=band, station_radio_data={radio: 1})  # to setup sniffer radio
                    print("sniffer_radio", sniff_radio)
                    if radio is not None and sniffer_channel is not None:
                        self.start_sniffer(radio_channel=sniffer_channel, radio=sniff_radio, duration=60)
                    logging.info("started-sniffer")
                    client_connect.build()
                    logging.info("napping 10 sec")
                    time.sleep(10)
                    if attach_station_data is True:
                        # station data
                        sta_length = len(station_name)
                        for i in range(sta_length):
                            sta_data1 = self.json_get(_req_url="port/1/1/%s" % (station_name[i]))
                            self.allure_report_table_format(dict_data=sta_data1["interface"], key="STATION DETAILS",
                                                            value="VALUE", name="%s info" % (station_name[i]))
                    # to stop sniffer
                    if radio is not None and sniffer_channel is not None:
                        self.stop_sniffer(station_name)
                else:
                    logging.info("missing identifier.")
        else:
            client_connect.build()
        # fetch supplicant logs from lanforge
        try:
            self.get_supplicant_logs(radio=str(radio), sta_list=station_name)
        except Exception as e:
            print(e)
            logging.error(f"Error in getting Supplicant logs: {str(e)}")
        if client_connect.wait_for_ip(station_name, timeout_sec=timeout_sec):
            client_connect._pass("ALL Stations got IP's", print_=True)
            logging.info('cleaning up stations :',station_name)
            self.client_disconnect(station_name=station_name)
            return "PASS", client_connect
        else:
            logging.info('cleaning up stations :', station_name)
            self.client_disconnect(station_name=station_name)
            return False, "Test Failed"

    def convert_to_gbps(self, value="1Mbps"):
        """ Convert values to Gbps """
        number = int(''.join([char for char in value if char.isdigit()]))
        unit = ''.join([char for char in value if char.isalpha()])
        unit = unit.lower()
        if unit == 'gbps':
            return number
        elif unit == 'mbps':
            return number / 1000
        elif unit == 'kbps':
            return number / 1000000
        else:
            raise ValueError("Unknown unit")


class Report:
    def __init__(self, key1=None,
                 key2=None,
                 val1=None,
                 val2=None):
        self.key1 = key1
        self.key2 = key2
        self.val1 = val1
        self.val2 = val2

    def table1(self):
        table = {str(self.key1): self.val1, str(self.key2): self.val2}
        x = tabulate(table, headers="keys", tablefmt="fancy_grid")
        return x

    def table2(self, table=None, headers='firstrow', tablefmt='fancy_grid'):
        self.table = table
        x = tabulate(self.table, headers=headers, tablefmt=tablefmt)
        return x


class SCP_File:
    def __init__(self, ip="localhost", port=22, username="lanforge", password="lanforge", remote_path="/home/lanforge/",
                 local_path="."):
        self.ip = ip
        self.port = port
        self.remote_path = remote_path
        self.local_path = local_path
        self.username = username
        self.password = password

    def pull_file(self):
        ssh = paramiko.SSHClient()
        ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=self.ip, username=self.username, password=self.password, port=self.port, allow_agent=False,
                    look_for_keys=False)
        # ssh.close()

        with SCPClient(ssh.get_transport()) as scp:
            scp.get(remote_path=self.remote_path, local_path=self.local_path, recursive=True)
            scp.close()

    def save_current_scenario(self):
        pass
