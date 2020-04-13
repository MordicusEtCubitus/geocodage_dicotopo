# coding=utf8

import argparse
import logging
import lxml
from lxml import etree
import requests
import dicotopo
from glob import glob

logging.basicConfig(level=logging.INFO)

parser = argparse.ArgumentParser("Geocode all xml files in the dicotopo data folder using addok")

parser.add_argument("--dicotopo-folder", "-f"
                    , required=True
                    , action="store"
                    , dest="dicotopo_folder"
                    , help="Data folder containing all subfolders DT* with XML file from dicotopo" )


parser.add_argument("--addok-api"
                    , required=True
                    , action="store"
                    , dest="addok_api"
                    , help="Addok serveur url" )

args = parser.parse_args()

logging.info("Using arguments:")
logging.info("File: " +  args.dicotopo_folder)
logging.info("addok api: " +  args.addok_api)

    
for file in glob(args.dicotopo_folder + '/DT*/DT*[0-9].xml'):
    try:
        logging.info( f"Processing file {file}")
        dicotopo.geocode_file(file, args.addok_api)
    except Exception as err:
        logging.error("Error: %s" % err, exc_info=True)
