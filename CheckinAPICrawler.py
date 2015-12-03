#! /usr/bin/python2
# vim: set fileencoding=utf-8
"""Get checkin info by expanding 4sq.com short url with bit.ly and then
requesting Foursquare API."""

import itertools
import ssl
import bitly_api
import foursquare
import Chunker
import logging
import ConfigParser
logging.basicConfig(filename='tweets.log', level=logging.INFO,
                    format='%(asctime)s [%(levelname)s]: %(message)s')
import twitter_helper as th
CHECKIN_URL = th.CHECKIN_URL
BITLY_SIZE = 15
config = ConfigParser.ConfigParser()
config.read('api_keys.cfg')
BITLY_TOKEN = config.get('bitly', 'BITLY_TOKEN')
CLIENT_ID = config.get('foursquare', 'FOURSQUARE_ID2')
CLIENT_SECRET = config.get('foursquare', 'FOURSQUARE_SECRET2')

def get_id_and_signature(url):
    """Potentially extract checkin id and signature from `url`."""
    components = None if not url else CHECKIN_URL.search(url)
    if not components:
        return (None, None)
    return components.groups()


class FoursquareDown(Exception):
    """Signal that even after waiting a long time, request to Foursquare still
    result in ServerError."""
    pass


class CheckinAPICrawler(object):
    """Get checkins info."""
    def __init__(self):
        self.bitly = bitly_api.Connection(access_token=BITLY_TOKEN)
        self.client = foursquare.Foursquare(CLIENT_ID, CLIENT_SECRET)
        self.bitly_batch = Chunker.Chunker(BITLY_SIZE)
        self.failures = th.Failures(initial_waiting_time=1.8)

    def checkins_from_url(self, urls):
        """Return info from all url in `urls`"""
        res = []
        for batch in self.bitly_batch(urls):
            try:
                res.extend(self.get_checkins_info(batch))
            except FoursquareDown:
                logging.exception("Foursquare not responding")
                return None
        return res

    def expand_urls(self, urls):
        """Use Bitly to expand short link in `urls`.
        Return a list of (checkin id, signature)."""
        try:
            expanded = [res.get("long_url", None)
                        for res in self.bitly.expand(link=urls)]
        except bitly_api.BitlyError:
            logging.exception("Error expanding URL")
            expanded = itertools.repeat(None, BITLY_SIZE)
        return [get_id_and_signature(url) for url in expanded]

    def query_foursquare(self, id_and_sig):
        """Request Foursquare to get raw info about checkins in `id_and_sig`"""
        for cid, sig in id_and_sig:
            if cid:
                self.client.checkins(cid, {'signature': sig}, multi=True)
        try:
            return self.client.multi()
        except (foursquare.FoursquareException, ssl.SSLError):
            logging.exception("Error requesting batch checkins")
            waiting_time = self.failures.fail()
            if self.failures.recent_failures >= 5:
                raise FoursquareDown
            msg = 'Will wait for {:.0f} seconds'.format(waiting_time)
            logging.info(msg)
            self.failures.do_sleep()

    def get_checkins_info(self, urls):
        """Return info from a batch of `urls`"""
        id_and_sig = self.expand_urls(urls)
        raw_checkins = self.query_foursquare(id_and_sig)

        res = []
        for cid, sig in id_and_sig:
            if not cid:
                res.append(None)
                continue
            try:
                raw_checkin = raw_checkins.next()
            except foursquare.ServerError as oops:
                logging.exception('error in getting next checkin')
                if 'status' in str(oops):
                    waiting_time = self.failures.fail()
                    if self.failures.recent_failures >= 5:
                        raise FoursquareDown
                    msg = 'Will wait for {:.0f} seconds'.format(waiting_time)
                    logging.info(msg)
            if isinstance(raw_checkin, foursquare.FoursquareException):
                msg = 'Weird id: {}?s={}\n{}'.format(cid, sig,
                                                     str(raw_checkin))
                logging.warn(msg)
                res.append(None)
            else:
                parsed = th.parse_json_checkin(raw_checkin)
                checkin_info = None
                if parsed:
                    checkin_info = (cid + '?s=' + sig, ) + parsed
                res.append(checkin_info)
        return res