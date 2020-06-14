
import time
from datetime import datetime
import grovepi
import yaml
from elasticsearch import Elasticsearch

import MoistureDetector


def main():
    with open('config.yaml', 'r') as config_file:
        config = yaml.load(config_file)

    es = Elasticsearch([config['es']['url']])
    es_alias_name = 'moisture-index'

    detector = MoistureDetector(port=0)
    interval = 5 * 60
    led = 5
    grovepi.pinMode(led,"OUTPUT")
    grovepi.ledBar_init(led, 0)

    while True:
        try:
            moisture, condition = detector.read_moisture_value()

            doc = {
                'moisture' : moisture,
                'condition': condition,
                'timestamp': datetime.utcnow()
            }
            es_index_name = "{}-{}".format(es_alias_name, datetime.now().strftime("%Y%m"))
            if not es.indices.exists(es_index_name):
                es.indices.create(index=es_index_name)

            res = es.index(index=es_index_name, body=doc)
            print(res)

            led_brightness = int(min(moisture / 300 * 10, 10)) + 1
            grovepi.ledBar_setLevel(led, led_brightness)

            # Alert @ 7am
            now = datetime.utcnow()
            if now.hour == 23 and condition == "DRY":
                pass

            time.sleep(interval)

        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    try:
        main()
    except IOError:
        print(str(error))
        exit(1)

    exit(0)
