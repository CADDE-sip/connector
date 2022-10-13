#!/usr/bin/env python3

import connexion
import logging

from swagger_server import encoder
from swagger_server.utilities.error_handler import handle_api_exception

__LOG_FORMAT = '%(asctime)s %(levelname)s %(name)s :%(message)s'
logging.basicConfig(format=__LOG_FORMAT, level=logging.INFO)


def main():
    app = connexion.App(__name__, specification_dir='./swagger/')
    app.app.json_encoder = encoder.JSONEncoder
    app.app.config['JSON_AS_ASCII'] = False
    app.add_error_handler(Exception, handle_api_exception)
    app.add_api(
        'swagger.yaml', arguments={
            'title': 'CADDE v4 Specification 提供者 コネクタメイン'})
    app.run(port=8080, threaded=True)


if __name__ == '__main__':
    main()
