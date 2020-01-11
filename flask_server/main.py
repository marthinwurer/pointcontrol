import itertools
import json
import logging
import sqlite3
import sys
from datetime import datetime, timedelta

import requests
from flask import Flask, render_template, request
from gevent.pywsgi import WSGIServer

app = Flask(__name__,
            static_url_path='/static',
            static_folder='static',
            template_folder='.')

APIKEY = open("../apikey.txt", "r").read().strip()


def _execute(query, args):
    if not isinstance(args, (tuple, list)):
        args = (args,)
    dbPath = "../data_for_ben.db"
    connection = sqlite3.connect(dbPath)
    cursor= connection.cursor()
    cursor.execute(query, args)
    result = cursor.fetchall()
    connection.commit()
    connection.close()
    return result


@app.route("/")
def index():
    return render_template("main.html")


@app.route("/rate_events.html")
def rate_events():
    return render_template("rate_events.html")


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


@app.route("/event")
def event():
    q = request.args.get("q")
    payload = {
        "_api_key": APIKEY,
        "name_contains": q,
        "_sort": "start_date_asc",
        "_per_page": 100,
        "start_date_gte": (datetime.now() - timedelta(days=7)).isoformat().split("T")[0],
    }
    r = requests.get("https://api.askfred.net/v1/tournament", params=payload)
    eventinfos = []
    if r.status_code == requests.codes.ok:
        rjson = r.json()
        for tournament in rjson["tournaments"]:
            for event in tournament.get("events", []):  # don't error on no events listed for a new tournament
                eventinfos.append({
                    "event_id": event["id"],
                    "tournament_id": tournament["id"],
                    "tname": tournament["name"],
                    "ename": event["full_name"],
                    "weapon": event["weapon"],
                    "start_date": tournament["start_date"],
                })
    return json.dumps(eventinfos)


@app.route("/rate_event")
def rate_event():
    tournament_id = request.args.get("tournament_id")
    event_id = request.args.get("event_id")
    payload = {"tournament_id": tournament_id}
    r = requests.get("https://askfred.net/Events/whoIsComing.php", params=payload)
    datapoints = []
    if r.status_code == requests.codes.ok:
        html = r.text.split("\n")
        i = 0
        weapon = ""
        while not all(s in html[i] for s in ["whoIsComing", str(event_id)]):
            if "Epee" in html[i]:
                weapon = "Epee"
            elif "Foil" in html[i]:
                weapon = "Foil"
            elif "Saber" in html[i]:
                weapon = "Saber"
            i = i + 1
        names = []
        while not ("</table>" in html[i]):
            if "," in html[i] and "<td nowrap>" in html[i]:
                firstlast = html[i].replace("<td nowrap>", "").replace("</td>", "")
                first = firstlast.split(",")[1].strip()
                last = firstlast.split(",")[0]
                names.append((first, last))
            i = i + 1
        if names:
            datapoints = build_datapoints(names, weapon)
    return json.dumps(datapoints)


def build_datapoints(names, weapon):
    fencer_info = get_fencer_info(names)
    datapoints = []
    for f in fencer_info:
        lr = get_latest_rating(f[1], weapon)
        if lr is not None:
            datapoints += [{"name": f[0],
                            "birthyear": f[2],
                            "rating": format(lr[0], ".2f") if lr else "???",
                            "data_rating": lr[0] if lr else None
                            }]
    datapoints = sorted(datapoints, key=lambda x: x["data_rating"], reverse=True)
    return datapoints


def get_fencer_info(names):
    fencer_info = [(f[0] + " " + f[1], get_fencer(f[0], f[1])) for f in names]
    # we need to flatten because multiple people can have the same name
    flat_fencer_info = []
    for name, info in fencer_info:
        for item in info:
            flat_fencer_info.append((name, *item))
    return flat_fencer_info


def getLatestRating(fencerid, weapon):
    return getLatestRatingAsOf(fencerid, weapon, datetime.now().isoformat().split("T")[0])


def getLatestRatingAsOf(fencerid, weapon, asof):
    query = ''' select r.ts_mu, t.start_date
          from adjusted_ratings r, bouts b, events e, 
          tournaments t
          where r.boutid = b.boutid
          and r.weapon = (?)
          and b.eventid = e.eventid
          and e.tournamentid = t.tournamentid
          and r.fencerid = (?)
          and t.start_date <= (?)
          order by t.start_date asc, r.boutid asc
          '''
    args = (weapon, int(fencerid), asof)
    rows = _execute(query, args)
    if not rows:
        return None
    return rows[-1]

def get_latest_rating(fencer_id, weapon):
    as_of = datetime.now().isoformat().split("T")[0]
    query = ''' select r.ts_mu, t.start_date
          from adjusted_ratings r, bouts b, events e, 
          tournaments t, fencers f
          where
           r.fencerid = (?)
           and r.weapon = (?)
           and r.boutid = b.boutid
           and b.eventid = e.eventid
           and e.tournamentid = t.tournamentid
          order by t.start_date asc, r.boutid asc
          '''
    """
          and t.start_date <= (?)
    """
    args = (weapon, fencer_id)#, as_of)
    rows = _execute(query, args)
    if not rows:
        return None
    return rows[-1]

def get_fencer(first_name, last_name):
    query = """
    select f.fencerid, f.birthyear
    from fencers f
    where f.first_name = (?) and f.last_name = (?)
    """
    rows = _execute(query, (first_name, last_name))
    return rows





if __name__ == '__main__':
    db_name = sys.argv[1]
    # logger = logging.getLogger()
    # logger.setLevel(logging.DEBUG)
    # handler = logging.FileHandler("server.log")
    # logger.addHandler(handler)
    server = WSGIServer(('127.0.0.1', 5000), app)#, log=logger, error_log=logger)
    server.serve_forever()