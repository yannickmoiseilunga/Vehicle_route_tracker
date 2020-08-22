from vehicleroute import Map, Route
from flask import Flask, render_template


app = Flask(__name__)
app.config['API_KEY'] = "AIzaSyBvQ0AZSNA9oinBVXD2hGmi7lmjDmVbXsg"
route = Route("20180117_023924.tcx.xml")
map = Map(route.trackpoints)


@app.route('/')
def index():
    context = {
        "key": app.config['API_KEY'],
        "title": route.title
        #"velocity": route.vlc_tm,
        #"velocityb": route.trip_velocity,
    }
    return render_template('template.html', map=map, context=context)


if __name__ == '__main__':
    app.run()
