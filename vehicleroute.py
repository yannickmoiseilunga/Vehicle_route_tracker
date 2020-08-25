import sys
import math
import datetime as dt
import matplotlib.pyplot as plt
from xml.dom import minidom
from os.path import splitext
from io import BytesIO
import datetime
from datetime import timedelta
from PIL import Image
import pandas
from pandas import DataFrame
import numpy
from dateutil.parser import parse
from pandas.plotting import register_matplotlib_converters
import matplotlib.gridspec as gridspec

register_matplotlib_converters()



class Map:
    def __init__(self, points):
        """
        Instantiate an Map object with route coordinates added to the Map object
        :param points: a list of tuples contains latitude, longitude and time of a route
        """
        self._points = points
        self.v = []
        self.google_coordinates = ",\n".join(["{{lat: {lat}, lng: {lng}, alt: {alt}, dist: {dist}, tm: {tm}}}".format(lat=x, lng=y, alt=a, dist=d, tm=z) for x, y, a, d, z, *rest in self._points])

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

        latitudes  = self._points['lat']
        longitudes = self._points['lng']
        #self._points['tm'] 
    
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
        latitudes  = [lat for lat, lng, *rest in self._points]
        longitudes = [lng for lat, lng, *rest in self._points]
      
        center_lat = (max((x for x in self._points['lat']))  + min((x for x in self._points['lat'])))  / 2
        center_lng = (max((x for x in self._points['lng']))  + min((x for x in self._points['lng']))) / 2
        return center_lat, center_lng

    @property
    def altitude_svg(self):
        """
        Create an svg data object using matplotlib for altitude chart that can be injected into html template
        :return: altitude_svg; svg data for altitude chart
        """
        #self._points = all_val
        #all_val = self._points 
        self._points = DataFrame(self._points, columns=['lat', 'lng', 'alt', 'tm', 'dist'])
        #vlc_tm = self._to_velocity(self)
        self._points['lat']  = pandas.Series(self._points['lat'].astype(float))
        self._points['lng']  = pandas.Series(self._points['lng'].astype(float))
        self._points['tm']   = pandas.Series(self._points['tm'])
        self._points['alt']  = pandas.to_numeric(self._points['alt'],errors='coerce')
        self._points['dist'] = pandas.to_numeric(self._points['dist'],errors='coerce')

        #df_all_values['Time'] = df_all_values['tm'].values.astype(numpy.int64) / 1e9
        self._points['Time'] = self._points['tm'].values.astype(numpy.int64) / 1e9
        #dist_values = df_all_values.diff().fillna(0.)
        self._points['Time'] = self._points['Time'].diff().fillna(0.)
        #dist_values[['Speedv','tm']].plot(x='tm', y='Speedv')
        self._points['Speedv'] = self._points['dist'].diff().fillna(0.) / self._points['Time'] 

        timevar   = self._points['tm'] 
 
        altitudes = self._points['alt']
        ##v = [t[i+1]-t[i] for i in range(len(self.trackpoints)-1) ]
        ##distances = [dist for *rest, dist in self._points]
        distances = self._points['dist']
        #distancesvar = [distances[i+1]-distances[i] for i in range(len(self._points['dist'])-1) ]
        distancesvar = self._points['dist'].diff().fillna(0.)
        speeds = self._points['Speedv']
        timevar1 = self._points['Time']

        fig, (ax1, ax2, ax3, ax4) =  plt.subplots(4, constrained_layout=False)
        ax1.plot(distances, altitudes)
        ax1.legend(loc="upper right", title="x vs h", title_fontsize="x-large")
        ax2.plot(distances, timevar)
        ax2.legend(loc="lower right", title="x vs t", title_fontsize="x-large")
        ax3.plot(distances, speeds)
        ax3.legend(loc="lower right", title="x vs v", title_fontsize="x-large")
        ax4.plot(speeds, timevar)
        ax4.legend(loc="upper right", title="v vs t", title_fontsize="x-large")
        svg_file = BytesIO()
        plt.savefig(svg_file, format='svg')     # save the file to io.BytesIO
        svg_file.seek(0)

        #altitude_svg = svg_file.getvalue().decode()   # retreive the saved data
        altitude_svg = svg_file.getvalue().decode()   # retreive the saved data
        altitude_svg = '<svg' + altitude_svg.split('<svg')[1]   # strip the xml header
        return altitude_svg

    @property
    def altitude_svg1(self):
        #self._points = all_val
        #all_val = self._points 
        self._points = DataFrame(self._points, columns=['lat', 'lng', 'alt', 'tm', 'dist'])
        #vlc_tm = self._to_velocity(self)
        self._points['lat']  = pandas.Series(self._points['lat'].astype(float))
        self._points['lng']  = pandas.Series(self._points['lng'].astype(float))
        self._points['tm']   = pandas.Series(self._points['tm'])
        self._points['alt']  = pandas.to_numeric(self._points['alt'],errors='coerce')
        self._points['dist'] = pandas.to_numeric(self._points['dist'],errors='coerce')

        #df_all_values['Time'] = df_all_values['tm'].values.astype(numpy.int64) / 1e9
        self._points['Time'] = self._points['tm'].values.astype(numpy.int64) / 1e9
        #dist_values = df_all_values.diff().fillna(0.)
        self._points['Time'] = self._points['Time'].diff().fillna(0.)
        #dist_values[['Speedv','tm']].plot(x='tm', y='Speedv')
        self._points['Speedv'] = self._points['dist'].diff().fillna(0.) / self._points['Time'] 

        timevar   = self._points['tm'] 

        altitudes = self._points['alt']
        ##v = [t[i+1]-t[i] for i in range(len(self.trackpoints)-1) ]
        ##distances = [dist for *rest, dist in self._points]
        distances = self._points['dist']
        #distancesvar = [distances[i+1]-distances[i] for i in range(len(self._points['dist'])-1) ]
        distancesvar = self._points['dist'].diff().fillna(0.)
        speeds = self._points['Speedv']
        timevar1 = self._points['Time']

        fig, (ax1, ax2, ax3, ax4, ax5) =  plt.subplots(5, constrained_layout=False)
        ax1.plot(timevar, distancesvar)
        ax1.legend(loc="upper right", title="t vs dt", title_fontsize="x-large")
        ax2.plot(timevar1, distancesvar)
        ax2.legend(loc="upper right", title="dt vs dt", title_fontsize="x-large")
        ax3.plot(speeds, distancesvar)
        ax3.legend(loc="upper right", title="v vs dt", title_fontsize="x-large")
        ax4.plot(distances, timevar1)
        ax4.legend(loc="upper right", title="x vs dt", title_fontsize="x-large")
        ax5.plot(speeds, timevar1)
        ax5.legend(loc="upper right", title="v vs dt", title_fontsize="x-large")
        svg_file1 = BytesIO()
        plt.savefig(svg_file1, format='svg')     # save the file to io.BytesIO
        #svg_file1.seek(0)
        svg_file1.seek(1)

        #altitude_svg = svg_file.getvalue().decode()   # retreive the saved data
        altitude_svg1 = svg_file1.getvalue().decode()   # retreive the saved data
        altitude_svg1 = '<svg' + altitude_svg1.split('<svg')[1]   # strip the xml header
        return altitude_svg1

    @staticmethod
    def _lat_rad(lat):
        """
        Helper function for calculating latitude span
        """
        sinus = math.sin(math.radians(lat + math.pi / 180))
        rad_2 = math.log((1 + sinus) / (1 - sinus)) / 2
        return max(min(rad_2, math.pi), -math.pi) / 2

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
        self.vlc_tm = 0
        self.t = [] 
        self.v = [] 

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
            tm_node = self._to_local(tm_node.firstChild.data)
            datetimeFormat = '%Y-%m-%d %H:%M:%S'
            tm = datetime.datetime.strptime(tm_node, datetimeFormat)

            lat_node = trackpoint.getElementsByTagName("LatitudeDegrees")[0]
            lat = float(lat_node.firstChild.data)

            lng_node = trackpoint.getElementsByTagName("LongitudeDegrees")[0]
            lng = float(lng_node.firstChild.data)
           
            # In the case of Endomondo, AltitudeMeters is not always available
            try:
                alt_node = trackpoint.getElementsByTagName("AltitudeMeters")[0]
                alt = float(alt_node.firstChild.data)
            except IndexError:
                alt = 0

            dist_node = trackpoint.getElementsByTagName("DistanceMeters")[0]
            dist = float(dist_node.firstChild.data)
           
            self.trackpoints.append((lat, lng, alt, tm, dist))

    @staticmethod
    def _to_local(utc_datetime):
        """
        Helper function to cover utc time to local time
        """
        utc = dt.datetime.strptime(utc_datetime, '%Y-%m-%dT%H:%M:%SZ')
        offset = dt.datetime.utcnow() - dt.datetime.now()
        return (utc - offset).strftime("%Y-%m-%d %H:%M:%S")

