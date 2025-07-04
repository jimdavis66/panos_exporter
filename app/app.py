import urllib3
import os
import logging

# Logging config
DEBUG = os.environ.get('DEBUG', '0').lower() in ('1', 'true', 'yes')
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s'
)
logger = logging.getLogger("panos_exporter")

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from flask import Flask, request, Response, jsonify
from app.config_loader import ConfigLoader
from app.exporter import Exporter

"""
Flask entry point for panos_exporter.
- Serves /metrics endpoint for Prometheus
- Handles config loading, logging, and debug mode
"""
app = Flask(__name__)
config_loader = ConfigLoader('config.yaml')
config = config_loader.load()
exporter = Exporter(config)

@app.route('/metrics')
def metrics():
    """
    Prometheus scrape endpoint.
    Query param: target (device IP/hostname)
    Returns Prometheus-formatted metrics or error JSON.
    """
    target = request.args.get('target')
    logger.info(f"/metrics requested for target={target}")
    if not target:
        logger.warning("Missing target parameter")
        return jsonify({'error': 'Missing target parameter'}), 400
    try:
        device = config_loader.get_device(target)
    except ValueError as e:
        logger.warning(f"Unknown target: {target}")
        return jsonify({'error': f'Unknown target: {target}'}, debug=str(e) if DEBUG else None), 400
    try:
        output = exporter.collect_metrics(target)
        return Response(output, mimetype='text/plain')
    except Exception as e:
        logger.exception(f"Exporter error for target={target}")
        if DEBUG:
            return jsonify({'error': 'Internal error', 'debug': str(e)}), 500
        return jsonify({'error': 'Internal error'}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9654)
