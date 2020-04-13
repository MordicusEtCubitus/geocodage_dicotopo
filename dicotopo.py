# coding=utf8

import lxml
from lxml import etree
import requests
import os.path
import logging
import pandas as pd
import time

def geocode_file(in_file, addok_api, out_file=None, error_file=None):
    """
    Geocode a dicotopo XML file, save result in out_file and errors in error_file
    

    if no out_file, choose in_file basename + '.geocoded' + '.<extension>'
    if no error_file, choose in_file basename + '.errors' + '.csv'
    """

    start_time = time.time()
    # addok full url
    search_url = addok_api + '/search/'

    # Opening file and reading records
    tree = etree.parse(in_file)

    if not out_file:
        filename, ext = os.path.splitext(in_file)
        out_file = filename + '.geocoded' + ext

    if os.path.exists(out_file):
        logging.warning("Out file %s alreading exists, skipping" % out_file)
        return
    
    if not error_file:
        filename, ext = os.path.splitext(in_file)
        error_file = filename + '.errors.csv'

    errors = []

    # reading articles
    for rank, article in enumerate(tree.xpath("//article")):
        try:
            article_id = article.attrib.get("id", "no_id")
            sm = "".join(article.xpath("./vedette/sm/text()"))
            commune = "".join(article.xpath("./definition/localisation/commune/text()"))
            code_insee = "".join(article.xpath("./definition/localisation/commune/@insee"))
       
            logging.info(f"Reading {sm} @ {commune} insee={code_insee}")
        
            # Quering addok
            query = f'{sm} {commune}'
            r = requests.get(search_url, params={"q" : query})

            # Result form is 
            """
            {'type': 'FeatureCollection'
            , 'version': 'draft'
            , 'features': [
               {'type': 'Feature'
                , 'geometry': {'type': 'Point', 'coordinates': [5.014742, 46.280508]}
                , 'properties': {'label': 'La Felie 01380 Saint-Genis-sur-Menthon', 'score': 0.5402117516629713, 'id': '01355B037A', 'citycode': '01355', 'type': 'place', 'name': 'La Felie', 'postcode': '01380', 'city': 'Saint-Genis-sur-Menthon', 'departement': 'Ain', 'region': 'Rhône-Alpes', 'importance': 0.0155}}
             , {'type': 'Feature'
                , 'geometry': {'type': 'Point', 'coordinates': [5.014742, 46.280508]}
                , 'properties': {'label': 'La Felie 01380 Saint-Genis-sur-Menthon', 'score': 0.5402117516629713, 'id': '01355B037A', 'citycode': '01355', 'type': 'place', 'name': 'La Felie', 'postcode': '01380', 'city': 'Saint-Genis-sur-Menthon', 'departement': 'Ain', 'region': 'Rhône-Alpes', 'importance': 0.0155}}
                , {'type': 'Feature'
                    , 'geometry': {'type': 'Point', 'coordinates': [5.019534, 46.265659]}
                    , 'properties': {'label': 'Grivaudière 01380 Saint-Genis-sur-Menthon', 'score': 0.5341786469344609, 'id': '01355B046K', 'citycode': '01355', 'type': 'place', 'name': 'Grivaudière', 'postcode': '01380', 'city': 'Saint-Genis-sur-Menthon', 'departement': 'Ain', 'region': 'Rhône-Alpes', 'importance': 0.0155}}
            }]
            , 'attribution': 'BANO', 'licence': 'ODbL', 'query': 'Bermondière (La), Saint-Genis-sur-Menthon', 'limit': 5}
            """


            if r.status_code == 200:
                # getting first result
                data = r.json()
                if data['features']:
                    feature = data['features'][0]
                    lon, lat = feature['geometry']['coordinates']
                    localisation = f"<geocoding><bano><longitude>{lon}</longitude><latitude>{lat}</latitude></bano></geocoding>"
                    article.append(etree.XML(localisation))
                else:
                    err = {"rank" : rank
                           , 'sm' : sm
                           , 'commune' : commune
                           , 'insee' : code_insee
                           , "article_id" : article_id
                           , "msg" : "not found in geo database" }
                    errors.append(err)
            else:
                err = {"rank" : rank
                       , 'sm' : sm
                       , 'commune' : commune
                       , 'insee' : code_insee
                       , "article_id" : article_id
                       , "msg" : '%s: %s' % (r.status_code, r.text) }
                errors.append(err)
                logging.error(err)


        except Exception as error:
            logging.error("Error: %s" % error, exc_info=True)
            err = {"rank" : rank
                   , 'sm' : sm
                   , 'commune' : commune
                   , 'insee' : code_insee
                   , "article_id" : article_id
                   , "msg" : error }
            errors.append(err)

    # Writing outfile
    logging.info("Writing outfile:" + out_file)
    tree.write(out_file)

    # Writing error file
    if errors:
        # Using pandas to save csv errors: a bit too much stronger but much more simple than csv.DictWriter
        logging.warning("%s errors found, writing log file %s" % (len(errors), error_file))
        data = pd.DataFrame(errors)
        data.to_csv(error_file, sep=";", index=False)


    end_time = time.time()
    logging.info("File %s: Processed %s articles in %02.2f seconds" % (in_file, rank, end_time - start_time))
