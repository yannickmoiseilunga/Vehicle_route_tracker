import sys
import math
import datetime as dt
import matplotlib.pyplot as plt
from xml.dom import minidom
from os.path import splitext
from io import BytesIO
import datetime
from datetime import timedelta


class Map:
    def __init__(self, points):
        """
        Instantiate an Map object with route coordinates added to the Map object
        :param points: a list of tuples contains latitude, longitude and time of a route
        """
        self._points = points
        self.google_coordinates = ",\n".join(["{{lat: {lat}, lng: {lng}, tm: {tm}}}".format(lat=x, lng=y, tm=z) for x, y, z, *rest in self._points])

    @property
    def zoom(self):
        """
        Algorithm to derive zoom from a route. For details please see
        - https://developers.google.com/maps/documentation/javascript/maptypes#WorldCoordinates
        - http://stackoverflow.com/questions/6048975/google-maps-v3-how-to-calculate-the-zoom-level-for-a-given-bounds
        :return: zoom value 0 - 21 based on the how widely spread of the route coordinates
        """

        map_size = {"height": 900, "width": 1900}
        max_zoom = 21   # maximum zoom level based on Google Map API
        world_dimension = {'height': 256, 'width': 256}     # min map size for entire world

        latitudes  = [lat for lat, lon, tm, *rest in self._points]
        longitudes = [lon for lat, lon, tm, *rest in self._points]
        triptime   = [tm for lat, lon, tm, *rest in self._points]


        # calculate longitude span between east and west
        delta = max(longitudes) - min(longitudes)
        if delta < 0:
            lon_span = (delta + 360) / 360
        else:
            lon_span = delta / 360

        # calculate latitude span between south and north
        lat_span = (self._lat_rad(max(latitudes)) - self._lat_rad(min(latitudes))) / math.pi

        # get zoom for both latitude and longitude
        zoom_lat = math.floor(math.log(map_size['height'] / world_dimension['height'] / lat_span) / math.log(2))
        zoom_lon = math.floor(math.log(map_size['width'] / world_dimension['width'] / lon_span) / math.log(2))

        return min(zoom_lat, zoom_lon, max_zoom)-1

    @property
    def center(self):
        """
        Calculate the center of the current map object
        :return: (center_lat, center_lng) latitude, longitude represents the center of the map object
        """
        center_lat = (max((x[0] for x in self._points)) + min((x[0] for x in self._points))) / 2
        center_lng = (max((x[1] for x in self._points)) + min((x[1] for x in self._points))) / 2
        trip_tme = (max((x[2] for x in self._points)) + min((x[2] for x in self._points))) / 2

        return center_lat, center_lng, trip_tme

    @property
    def altitude_svg(self):
        """
        Create an svg data object using matplotlib for altitude chart that can be injected into html template
        :return: altitude_svg; svg data for altitude chart
        """
        timevar   = [tm for *rest, tm in self._points]
        altitudes = [alt for lat, lng, alt, *rest in self._points]
        distances = [dist for *rest, dist in self._points]

        plt.figure(figsize=(15, 2.5))
        plt.ylabel('Time')
        plt.xlabel('Distance')
        plt.tight_layout()
        #plt.plot(distances, timevar altitudes)
        plt.plot(distances, timevar)
        svg_file = BytesIO()
        plt.savefig(svg_file, format='svg')     # save the file to io.BytesIO
        svg_file.seek(0)

        #altitude_svg = svg_file.getvalue().decode()   # retreive the saved data
        altitude_svg = svg_file.getvalue().decode()   # retreive the saved data
        altitude_svg = '<svg' + altitude_svg.split('<svg')[1]   # strip the xml header
        return altitude_svg

    @staticmethod
    def _lat_rad(lat):
        """
        Helper function for calculating latitude span
        """
        sinus = math.sin(math.radians(lat + math.pi / 180))
        rad_2 = math.log((1 + sinus) / (1 - sinus)) / 2
        return max(min(rad_2, math.pi), -math.pi) / 2

    def _vel_road(tm, dist):
        """
        Helper function for calculating velocity
        """
        return dist / tm


class Route:
    """
    Parse a tcx route file and generateds all trackpoints in a list of tuples that consists of
    latitude, longitude, altitude, timelapsed, and distance(accumulated)
    """
    def __init__(self, route_file):
        """
        Read the tcx route file, and parse the file to get all the trackpoints.
        Useage: route = Route(route_file)
                route.trackpoints to get all the trackpoints
        :param route_file: file in tcx format
        """
        self.title = splitext(route_file)[0]
        self.trackpoints = []
        self.trip_velocity = []
        #self.vlc_tm = []
        #var diff 

        try:
            dom = minidom.parse(route_file)
        except FileNotFoundError as e:
            print("Error({0}): {1}".format(e.errno, e.strerror))
            sys.exit()
        tracknodes = dom.getElementsByTagName("Trackpoint")
        self._parse_trackpoints(tracknodes)

    def _parse_trackpoints(self, trkpts):
        for trackpoint in trkpts:
            tm_node = trackpoint.getElementsByTagName("Time")[0]
            tm = self._to_local(tm_node.firstChild.data)

            lat_node = trackpoint.getElementsByTagName("LatitudeDegrees")[0]
            lat = float(lat_node.firstChild.data)

            lng_node = trackpoint.getElementsByTagName("LongitudeDegrees")[0]
            lng = float(lng_node.firstChild.data)

            
            # In the case of Endomondo, AltitudeMeters is not always available
            try:
                alt_node = trackpoint.getElementsByTagName("AltitudeMeters")[0]
                alt = float(alt_node.firstChild.data)
            except IndexError:
                alt = 0.0

            dist_node = trackpoint.getElementsByTagName("DistanceMeters")[0]
            dist = float(dist_node.firstChild.data)
            #trip_velocity = float(dist) / float(tm)
            #vlc_tm = self._to_velocity(self)

            #self.trackpoints.append((lat, lng, alt, tm, dist, trip_velocity))
            self.trackpoints.append((lat, lng, alt, tm, dist))
        


    @staticmethod
    def _to_local(utc_datetime):
        """
        Helper function to cover utc time to local time
        """
        utc = dt.datetime.strptime(utc_datetime, '%Y-%m-%dT%H:%M:%SZ')
        offset = dt.datetime.utcnow() - dt.datetime.now()
        return (utc - offset).strftime("%Y-%m-%d %H:%M:%S")
"""
    @property
    def _to_velocity(self):
        
        #trip_elaptme  = self.trackpoints[2][-1] - self.trackpoints[2][0] 
        #trip_elaptme  = self.trackpoints - self.trackpoints
        #trip_dist     = self.trackpoints[-1][-1] - self.trackpoints[-1][0]  
        #trip_velocity = trip_dist / float(trip_elaptme)
        trip_velocity = self.trackpoints 
        #trip_tme = (max((x[3] for x in self.trackpoints)) - min((x[3] for x in self.trackpoints))).strftime("%Y-%m-%d %H:%M:%S") 
        #trip_elaptme = (max((x[3] for x in self.trackpoints)) - min((x[3] for x in self.trackpoints))).strftime("%S") 
        #trip_elaptme = tm[tm.length -1] - tm[0]  
        #trip_dist = (max((x[4] for x in self.trackpoints)) - min((x[4] for x in self.trackpoints))) 
        #trip_velocity = trip_dist / float(trip_elaptme)

        #utc = dt.datetime.strptime(utc_datetime, '%Y-%m-%dT%H:%M:%SZ')
        #offset = dt.datetime.utcnow() - dt.datetime.now()


        trip_elaptme  = self.trackpoints[-2][-1] - self.trackpoints[-2][0] 
        trip_dist     = self.trackpoints[-1][-1] - self.trackpoints[-1][0]  
        trip_velocity = trip_dist / float(trip_elaptme)
        #vlc_tm = self._to_velocity(self, trip_dist, trip_elaptme)

        datetimeFormat = '%Y-%m-%d %H:%M:%S.%f'
        #date1 = trackpoints.tm[0] 
        #date2 = trackpoints.tm[-1]

        date1 = self.trackpoints[-2][0]  
        date2 = self.trackpoints[-2][-1]
         
        #diff = datetime.datetime.strptime(date1, datetimeFormat) - datetime.datetime.strptime(date2, datetimeFormat)
 
        diff = date1 - date2
 
        return trip_velocity
"""

"""
        #Helper function to calculate velocity
        """
