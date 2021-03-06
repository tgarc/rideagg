import json
import urllib
import webapp2
import math
import config
from base_service import BaseService
from google.appengine.api import memcache
from google.appengine.api import urlfetch

class UberService(BaseService):
    uber_product_data = None
    """
    Method to make request to Uber Servers using their API. This method
    autofills the server token and gets the url based on the url_type defined
    in config.py
    Possible url types: products_url, time_url, products_url

    Returns: status code and parsed json response
    """
    # TODO(goyalankit) add error handling code
    def make_request(self, url_type, parameters):
        uber_config = config.app_config.get('uber')
        parameters.update({ 'server_token': uber_config.get('server_token')})
        url_with_params = uber_config.get(url_type) + '?' + urllib.urlencode(parameters)
        response = urlfetch.fetch(url_with_params, method=urlfetch.GET, deadline=60)
        json_response = json.loads(response.content)
        return response.status_code, json_response

    @property
    def has_api(self):
        return True

    def _get_fare_by_lat_lang(self, src_lat, src_long,
            dst_lat, dst_long):
        params = {
                'start_latitude': src_lat,
                'start_longitude': src_long,
                'end_latitude': dst_lat,
                'end_longitude': dst_long
                }

        status, result = self.make_request("price_url", params)
        self._get_product_info(src_lat, src_long)
        for res in result['prices']:
            res['image'] = self.image(res['display_name'])
            res['capacity'] = self.capacity(res['display_name'])

        return result

    def _get_fare_by_distance(self, distance):
        raise NotImplementedError("Method not supported by this service")

    def get_fare(self, route):
        s_l = route.start_location
        e_l = route.end_location
        result = self._get_fare_by_lat_lang(s_l['lat'], s_l['lon'],
                e_l['lat'], e_l['lon'])

        ret = sorted(result['prices'], key=lambda k: k['high_estimate'])
        return {"prices" : ret}


    def image(self, display_name):
        for product in self.__class__.uber_product_data:
            if display_name == product['display_name']:
                return product['image'];

    def capacity(self, display_name):
        for product in self.__class__.uber_product_data:
            if display_name == product['display_name']:
                return product['capacity'];


    def _get_product_info(self, src_lat, src_long, force=False):
        params = {
                'latitude': src_lat,
                'longitude': src_long,
                }

        if (not self.__class__.uber_product_data) or force:
            status, result = self.make_request("products_url", params)
            self.__class__.uber_product_data = result['products']
        return self.__class__.uber_product_data


    """
    This is a method reserved for future use. Just in case we want to pass
    some extra information for any service.

    Return: Empty hash implies no extra information available
    """
    def get_extra_information(self):
        return {}

    """
    Only available for uber api. Not implemented yet (depends if we'd want to
    display it on the UI.)
    """
    def get_min_response_time(self):
        raise NotImplementedError("Subclasses should implement this!")
