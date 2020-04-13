# coding=utf8

import argparse
import logging
import lxml
from lxml import etree
import requests
import dicotopo

logging.basicConfig(level=logging.INFO)

try:
    parser = argparse.ArgumentParser("Geocode a dicotopo xml file using addok")

    parser.add_argument("--dicotopo-file", "-f"
                        , required=True
                        , action="store"
                        , dest="dicotopo_file"
                        , help="XML file from dicotopo data folder" )


    parser.add_argument("--addok-api"
                        , required=True
                        , action="store"
                        , dest="addok_api"
                        , help="Addok serveur url" )

    args = parser.parse_args()

    logging.info("Using arguments:")
    logging.info("File: " +  args.dicotopo_file)
    logging.info("addok api: " +  args.addok_api)

    dicotopo.geocode_file(args.dicotopo_file, args.addok_api)
        

except Exception as err:
    logging.error("Error: %s" % err, exc_info=True)
