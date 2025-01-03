#!/usr/bin/env python3
'''
NAME: lf_json_api.py

PURPOSE:

 This script will is an example of using LANforge JSON API to use GET Requests to LANforge. 
 

EXAMPLE:

    This will run through the module test:
    ./lf_json_api.py --lf_mgr 192.168.100.178 --lf_port 8080 --resource 1 --log_level debug --port wlan3 --lf_user lanforge --lf_passwd lanforge --get_request 'port radio

NOTE:
    LANforge GUI , click on info -> API Help  look under GET Requests  use similiar format to what is being done below.
'''

import argparse
import sys
import os
import logging
import importlib
import requests
import pandas as pd
import json


if sys.version_info[0] != 3:
    print("This script requires Python 3")
    exit(1)

sys.path.append(os.path.join(os.path.abspath(__file__ + "../../../")))

logger = logging.getLogger(__name__)
lf_logger_config = importlib.import_module("py-scripts.lf_logger_config")



class lf_json_api():
    def __init__(self,
                lf_mgr,
                lf_port,
                lf_user,
                lf_passwd,
                resource,
                port):                
        self.lf_mgr = lf_mgr
        self.lf_port = lf_port
        self.lf_user = lf_user
        self.lf_passwd = lf_passwd
        self.resource = resource
        self.port = port
        # the request can change
        self.request = ''


    def get_request_port_information(self):
        # https://docs.python-requests.org/en/latest/
        # https://stackoverflow.com/questions/26000336/execute-curl-command-within-a-python-script - use requests
        # station command
        # curl -H 'Accept: application/json' 'http://localhost:8080/port/1/1/wlan3' | json_pp
        # a radio command
        # curl --user "lanforge:lanforge" -H 'Accept: application/json'
        # http://192.168.100.116:8080/port/1/1/wlan3 | json_pp  , where --user
        # "USERNAME:PASSWORD"
        request_command = 'http://{lfmgr}:{lfport}/port/1/{resource}/{port}'.format(
            lfmgr=self.lf_mgr, lfport=self.lf_port, resource=self.resource, port=self.port)
        request = requests.get(
            request_command, auth=(
                self.lf_user, self.lf_passwd))
        logger.info(
            "port request command: {request_command}".format(
                request_command=request_command))
        logger.info(
            "port request status_code {status}".format(
                status=request.status_code))
        lanforge_port_json = request.json()
        logger.debug("port request.json: {json}".format(json=lanforge_port_json))
        lanforge_port_text = request.text
        logger.debug("port request.text: {text}".format(text=lanforge_port_text))
        lanforge_port_json_formatted = json.dumps(lanforge_port_json, indent=4)
        logger.debug("lanforge_port_json_formatted: {json}".format(json=lanforge_port_json_formatted))

        return lanforge_port_json, lanforge_port_text, lanforge_port_json_formatted

    def get_request_wifi_stats_information(self):
        # https://docs.python-requests.org/en/latest/
        # https://stackoverflow.com/questions/26000336/execute-curl-command-within-a-python-script - use requests
        # station command
        # curl -H 'Accept: application/json' 'http://localhost:8080/wifi-stats/1/1/wlan4' | json_pp
        # a radio command
        # curl --user "lanforge:lanforge" -H 'Accept: application/json'
        # http://192.168.100.116:8080/wifi-stats/1/1/wlan4 | json_pp  , where --user
        # "USERNAME:PASSWORD"
        request_command = 'http://{lfmgr}:{lfport}/wifi-stats/1/{resource}/{port}'.format(
            lfmgr=self.lf_mgr, lfport=self.lf_port, resource=self.resource, port=self.port)
        request = requests.get(
            request_command, auth=(
                self.lf_user, self.lf_passwd))
        logger.info(
            "wifi-stats request command: {request_command}".format(
                request_command=request_command))
        logger.info(
            "wifi-stats request status_code {status}".format(
                status=request.status_code))
        lanforge_wifi_stats_json = request.json()
        logger.debug("wifi-stats request.json: {json}".format(json=lanforge_wifi_stats_json))
        lanforge_wifi_stats_text = request.text
        logger.debug("wifi-stats request.text: {text}".format(text=lanforge_wifi_stats_text))
        lanforge_wifi_stats_json_formatted = json.dumps(lanforge_wifi_stats_json, indent=4)
        logger.debug("lanforge_wifi_stats_json_formatted: {json}".format(json=lanforge_wifi_stats_json_formatted))
        # TODO just return lanforge_json and lanforge_txt, lanfore_json_formated to is may be the same for all commands
        return lanforge_wifi_stats_json, lanforge_wifi_stats_text, lanforge_wifi_stats_json_formatted

    # TODO this is a generic one.
    def get_request_information(self):
        # https://docs.python-requests.org/en/latest/
        # https://stackoverflow.com/questions/26000336/execute-curl-command-within-a-python-script - use requests
        # station command
        # curl -H 'Accept: application/json' 'http://localhost:8080/{request}/1/1/wlan4' | json_pp
        # a radio command
        # curl --user "lanforge:lanforge" -H 'Accept: application/json'
        # http://192.168.100.116:8080//1/1/wlan4 | json_pp  , where --user
        # "USERNAME:PASSWORD"
        request_command = 'http://{lfmgr}:{lfport}/{request}/1/{resource}/{port}'.format(
            lfmgr=self.lf_mgr, lfport=self.lf_port,request=self.request, resource=self.resource, port=self.port)
        request = requests.get(
            request_command, auth=(
                self.lf_user, self.lf_passwd))
        logger.info(
            "{request} request command: {request_command}".format(request=self.request,
                request_command=request_command))
        logger.info(
            "{request} request status_code {status}".format(request=self.request,
                status=request.status_code))
        lanforge_json = request.json()
        logger.debug("{request} request.json: {json}".format(request=self.request,json=lanforge_json))
        lanforge_text = request.text
        logger.debug("{request} request.text: {text}".format(request=self.request,text=lanforge_text))
        lanforge_json_formatted = json.dumps(lanforge_json, indent=4)
        logger.debug("lanforge_json_formatted: {json}".format(json=lanforge_json_formatted))
        # TODO just return lanforge_json and lanforge_txt, lanfore_json_formated to is may be the same for all commands
        return lanforge_json, lanforge_text, lanforge_json_formatted


    # TODO This method is left in for an example it was taken from
    def get_request_radio_information(self):
        # https://docs.python-requests.org/en/latest/
        # https://stackoverflow.com/questions/26000336/execute-curl-command-within-a-python-script - use requests
        # curl --user "lanforge:lanforge" -H 'Accept: application/json'
        # http://192.168.100.116:8080/radiostatus/all | json_pp  , where --user
        # "USERNAME:PASSWORD"
        request_command = 'http://{lfmgr}:{port}/radiostatus/all'.format(lfmgr=self.lf_mgr, port=self.lf_port)
        request = requests.get(
            request_command, auth=(
                self.lf_user, self.lf_passwd))
        logger.info(
            "radio request command: {request_command}".format(
                request_command=request_command))
        logger.info(
            "radio request status_code {status}".format(
                status=request.status_code))
        lanforge_radio_json = request.json()
        logger.info("radio request.json: {json}".format(json=lanforge_radio_json))
        lanforge_radio_text = request.text
        logger.info("radio request.text: {text}".format(text=lanforge_radio_text))
        return lanforge_radio_json, lanforge_radio_text

    def post_wifi_cli_cmd(self, wifi_cli_cmd):

        # request_command = 'http://{lfmgr}:{port}/{wifi_cli_cmd}'.format(lfmgr=self.lf_mgr, port=self.lf_port, wifi_cli_cmd=json.dumps(wifi_cli_cmd).encode("utf-8"))
        request_command = 'http://{lfmgr}:{port}/{wifi_cli_cmd}'.format(lfmgr=self.lf_mgr, port=self.lf_port, wifi_cli_cmd=wifi_cli_cmd)
        # request_command = 'http://{lfmgr}:{port}/set_wifi_radio 1 1 wiphy1 NA NA NA NA NA NA NA NA NA 4'.format(lfmgr=self.lf_mgr, port=self.lf_port)
        request = requests.post(request_command, auth=(self.lf_user, self.lf_passwd))
        logger.info(
            "wifi_cli_cmd request command: {request_command}".format(
                request_command=request_command))
        logger.info(
            "wifi_cli_cmd request status_code {status}".format(
                status=request.status_code))
        lanforge_wifi_cli_cmd_json = request.json()
        logger.info("radio request.json: {json}".format(json=lanforge_wifi_cli_cmd_json))


# unit test
def main():
    lfjson_host = "localhost"
    lfjson_port = 8080
    parser = argparse.ArgumentParser(
        prog="lf_json_api.py",
        formatter_class=argparse.RawTextHelpFormatter,
        description="""
        example
        """)

    parser.add_argument("--lf_mgr", type=str, help="address of the LANforge GUI machine (localhost is default)",
                        default='localhost')
    parser.add_argument("--lf_port", help="IP Port the LANforge GUI is listening on (8080 is default)",
                        default=8080)
    parser.add_argument("--lf_user", type=str, help="user: lanforge")
    parser.add_argument("--lf_passwd", type=str, help="passwd: lanforge")
    parser.add_argument("--port", type=str, help=" port : wlan3")
    parser.add_argument("--radio", type=str, help=" --radio wiphy0")
    # TODO should be parsed from EID
    parser.add_argument("--resource", type=str, help="--resource LANforge, Station resource ID to use, default is 1", default=1)
    parser.add_argument('--log_level', default=None, help='Set logging level: debug | info | warning | error | critical')
    # logging configuration
    parser.add_argument(
        "--lf_logger_config_json",
        help="--lf_logger_config_json <json file> , json configuration of logger")
    # TODO check command 
    # TODO make generic so any request may be passed in
    parser.add_argument("--get_requests", type=str, help="perform get request may be a list:  port | radio | port_rssi | wifi-stats")
    parser.add_argument("--post_requests", type=str, help="perform set request may be a list:  nss ")
    parser.add_argument("--nss", type=str, help="--nss 4  set the number of spatial streams for a speific antenna ")


    args = parser.parse_args()

    # set up logger
    logger_config = lf_logger_config.lf_logger_config()

    if args.log_level:
        logger_config.set_level(level=args.log_level)

    # lf_logger_config_json will take presidence to changing debug levels
    if args.lf_logger_config_json:
        # logger_config.lf_logger_config_json = "lf_logger_config.json"
        logger_config.lf_logger_config_json = args.lf_logger_config_json
        logger_config.load_lf_logger_config()


    lf_json = lf_json_api( args.lf_mgr,
                            args.lf_port,
                            args.lf_user,
                            args.lf_passwd,
                            args.resource,
                            args.port)



    if args.get_requests:
        get_requests = args.get_requests.split()

        for get_request in get_requests:
            if get_request == "radio":
                lf_json.get_request_radio_information()

            if get_request == "port":
                lanforge_port_json, lanforge_port_text, lanforge_port_json_formatted = lf_json.get_request_port_information()

                logger.info("lanforge_port_json = {lanforge_port_json}".format(lanforge_port_json=lanforge_port_json))
                logger.info("lanforge_port_text = {lanforge_port_text}".format(lanforge_port_text=lanforge_port_text))
                logger.info("lanforge_port_text = {lanforge_port_text}".format(lanforge_port_text=lanforge_port_text))

            if get_request == "port_rssi":
                lanforge_port_json, lanforge_port_text, lanforge_port_json_formatted = lf_json.get_request_port_information()
                logger.info("lanforge_port_json = {lanforge_port_json}".format(lanforge_port_json=lanforge_port_json))
                logger.info("lanforge_port_json_formatted = {lanforge_port_json_formatted}".format(lanforge_port_json_formatted=lanforge_port_json_formatted))

                for key in lanforge_port_json:
                    if 'interface' in key:
                        avg_chain_rssi = lanforge_port_json[key]['avg chain rssi']
                        logger.info("avg chain rssi = {avg_chain_rssi}".format(avg_chain_rssi=avg_chain_rssi))
                        chain_rssi = lanforge_port_json[key]['chain rssi']
                        logger.info("chain rssi = {chain_rssi}".format(chain_rssi=chain_rssi))
                        signal = lanforge_port_json[key]['signal']
                        logger.info("signal = {signal}".format(signal=signal))

            if get_request == "alerts":
                lanforge_alerts_json = lf_json.get_alerts_information()

            if get_request == "wifi-stats":
                lanforge_wifi_stats_json, lanforge_wifi_stats_text, lanforge_wifi_stats_json_formatted = lf_json.get_request_wifi_stats_information()

                logger.info("lanforge_wifi_stats_json = {lanforge_wifi_stats_json}".format(lanforge_wifi_stats_json=lanforge_wifi_stats_json))
                logger.info("lanforge_wifi_stats_text = {lanforge_wifi_stats_text}".format(lanforge_wifi_stats_text=lanforge_wifi_stats_text))
                logger.info("lanforge_wifi_stats_json_formatted = {lanforge_wifi_stats_json_formatted}".format(lanforge_wifi_stats_json_formatted=lanforge_wifi_stats_json_formatted))

            # Generic so can do any query
            else:
                # set the generic request
                lf_json.request = get_request
                lanforge_json, lanforge_text, lanforge_json_formatted = lf_json.get_request_information()
                logger.info("{request} : lanforge_json = {lanforge_json}".format(request=get_request,lanforge_json=lanforge_json))
                logger.info("{request} : lanforge__text = {lanforge_text}".format(request=get_request,lanforge_text=lanforge_text))
                logger.info("{request} : lanforge_json_formatted = {lanforge_json_formatted}".format(request=get_request,lanforge_json_formatted=lanforge_json_formatted))




    if args.post_requests:
        post_requests = args.post_requests.split()

        for post_request in post_requests:
            if post_request == "nss":
                nss = int(args.nss)
                if (nss == 1):
                    antennas_set = 1
                if (nss == 2):
                    antennas_set = 4
                if (nss == 3):
                    antennas_set = 7
                if (nss == 4):
                    antennas_set = 8

                wifi_cli_cmd = 'set_wifi_radio 1 {resource} {radio} NA NA NA NA NA NA NA NA NA {antennas}'.format(
                    resource=args.resource, radio=args.radio,antennas=antennas_set)
                lf_json.post_wifi_cli_cmd(wifi_cli_cmd=wifi_cli_cmd)
         

    # sample of creating layer 3 


if __name__ == '__main__':
    main()
