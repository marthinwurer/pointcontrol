import json
import logging
import sqlite3
import sys

from flask import Flask, render_template, request
from gevent.pywsgi import WSGIServer

app = Flask(__name__,
            static_url_path='/static',
            static_folder='static',
            template_folder='.')


def _execute(query, args):
    if not isinstance(args, (tuple, list)):
        args = (args,)
    dbPath = "../data_for_ben.db"
    connection = sqlite3.connect(dbPath)
    cursorobj = connection.cursor()
    try:
        cursorobj.execute(query, args)
        result = cursorobj.fetchall()
        connection.commit()
    except Exception:
        raise
    connection.close()
    return result


@app.route("/")
def index():
    return render_template("main.html")


@app.route("/search")
def search():
    name = request.args.get("q")

    query = ''' select f.first_name || " " || f.last_name, f.fencerid, f.birthyear
            from fencers as f
            where f.first_name || " " || f.last_name like "%"||(?)||"%"
            group by f.fencerid
            '''

    results = _execute(query, (name,))
    result = []
    for x in results:
        item = {"fullname": x[0], "id": x[1], "birthyear": x[2]}
        result.append(item)
    return json.dumps(result)


@app.route("/get", methods=['GET'])
def get_rating():
    fencerid = int(request.args.get("id"))
    weapon = request.args.get("weapon")
    query = ''' select r.ts_mu, t.start_date
            from adjusted_ratings r, bouts b, events e, 
            tournaments t
            where r.boutid = b.boutid
            and r.weapon = (?)
            and b.eventid = e.eventid
            and e.tournamentid = t.tournamentid
            and r.fencerid = (?)
            order by t.start_date asc, r.boutid desc
            '''
    args = (weapon, int(fencerid),)
    rows = _execute(query, args)


    data_points = {"fencerid": fencerid, "ratings": [], "weapon": weapon}
    for row in rows:
        point = {"date": row[1], "rating": row[0]}
        data_points["ratings"].append(point)
    return json.dumps(data_points)


@app.route("/translate")
def translate():
    fencerid = int(request.args.get("id"))
    query = """
        select first_name || " " || last_name 
        from fencers
        where fencerid = (?)
    """
    obj = {"name": _execute(query, (fencerid,))[0]}
    return json.dumps(obj)


if __name__ == '__main__':
    db_name = sys.argv[1]
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler("server.log")
    logger.addHandler(handler)
    server = WSGIServer(('127.0.0.1', 5000), app, log=logger, error_log=logger)
    server.serve_forever()