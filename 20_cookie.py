from tornado.ioloop import IOLoop
from tornado.web import RequestHandler, Application
from bokeh.embed import components
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, Circle, CustomJS, Title
from markupsafe import Markup
import pymysql
import json

# connect to database
db = pymysql.connect(
    user='root',
    password='root',
    host='localhost',
    database='testdatabase'
    )

cursor = db.cursor()

cursor.execute("CREATE TABLE IF NOT EXISTS coordinates (x float, y float, id INT AUTO_INCREMENT PRIMARY KEY)")


# form a IndexHandler class
class IndexHandler(RequestHandler):
    def get(self):
        # create a data source for the circle glyph
        source = ColumnDataSource(data=dict(x=[], y=[]))

        # create a plot
        p = figure(
            x_range=(0, 9),
            y_range=(0, 9),
            title="Stress                                                      Übererregung                                         Euphorie",
            tools='tap'
        )

        # name the tickers
        p.xaxis.ticker = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        p.yaxis.ticker = [1, 2, 3, 4, 5, 6, 7, 8, 9]

        # add extra titles with add_layout
        p.add_layout(Title(
            text="Depression                                            Schläfrigkeit                                            Entspannung",
            align="left"), "below")
        p.add_layout(Title(text="Unangenehme Gefühle", align="center"), "left")
        p.add_layout(Title(text="Angenehme Gefühle", align="center"), "right")

        # removing minor ticks on axis
        p.xaxis.minor_tick_line_color = None
        p.yaxis.minor_tick_line_color = None

        # define the bounds
        p.xgrid.bounds = (0, 8)
        p.ygrid.bounds = (0, 8)

        # turn off visibility of axis
        p.axis.visible = False

        # add a circle glyph to the plot
        circle = Circle(x='x', y='y', size=20, fill_color='red')
        p.add_glyph(source, circle)

        # set the cookie
        self.set_cookie('handler_cookie', '12')

        # define a callback function that will be executed when the user clicks on the plot
        callback = """
           var data = source.data;
           var x = cb_obj.x;
           var y = cb_obj.y;
           data['x'] = [x];
           data['y'] = [y];
           source.change.emit();
           console.log(data);

           // Insert coordinates into the MySQL database
           var xhr = new XMLHttpRequest();
           xhr.open("POST", "/save_coordinates", true);
           xhr.setRequestHeader("Content-Type", "application/json");
           xhr.send(JSON.stringify({x: x, y: y}));
           """

        # attach the callback function to the plot
        p.js_on_event('tap', CustomJS(args=dict(source=source), code=callback))

        # generate the HTML and JavaScript code for the plot
        script, div = components(p)

        # mark the script and div variables as safe for rendering in the template
        script = Markup(script)
        div = Markup(div)

        # render the template with the plot code
        self.render('index.html', script=script, div=div)

# form a SaveCoordinatesHandler class
class SaveCoordinatesHandler(RequestHandler):
    def post(self):
        http_body = json.loads(self.request.body)
        x = http_body['x']
        y = http_body['y']

        # read the cookie
        cookie = self.get_cookie('handler_cookie')
        print(cookie)

        # Insert the coordinates into the MySQL database
        query = "INSERT INTO coordinates (x, y) VALUES (%s, %s)"
        cursor = db.cursor()
        cursor.execute(query, (x, y))
        db.commit()
        self.finish()



cursor.execute("SELECT * FROM coordinates")
for x in cursor:
    print(x)

cursor.close()

if __name__ == '__main__':
    app = Application([
        (r'/', IndexHandler),
        (r'/save_coordinates', SaveCoordinatesHandler),
    ], debug=True)
    app.listen(8648)
    IOLoop.current().start()