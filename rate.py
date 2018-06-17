import sqlite3
import argparse
import trueskill
from datetime import datetime, timedelta




class DBAccess:

    def __init__(self, db, begin_date):
        self.conn = sqlite3.connect(db, timeout=10)
        self.cursor = self.conn.cursor()
        # Cache all the fencer's states
        self.FENCER_STATE = dict()
        self.begin_date = begin_date

    def commit(self):
        self.conn.commit()

    def getLatestRating(self, fencerid, boutid, weapon):

        # hit the local in-memory cache
        if (fencerid, weapon) in self.FENCER_STATE:
            return self.FENCER_STATE[(fencerid, weapon)]
        query = self.cursor.execute("""
          SELECT r.ts_mu, r.ts_sigma FROM ratings r , bouts b, events e, tournaments t
          WHERE r.fencerid = %(fencerid)s
            AND r.boutid = b.boutid
            AND e.weapon = '%(weapon)s'
            AND b.eventid = e.eventid
            AND e.tournamentid = t.tournamentid
            AND t.start_date < '%(begin_date)s'
          ORDER BY t.start_date desc, b.boutid desc
          LIMIT 1;
          """ % {
            "fencerid": fencerid,
            "weapon": weapon,
            "boutid": boutid,
            "begin_date": self.begin_date
        }).fetchone()
        if query:
            return query
        else:
            return (trueskill.MU, trueskill.SIGMA)

    def updateLatestRating(self, fencerid, weapon, boutid, rating, prev_rating):
        query = self.cursor.execute("""
      INSERT OR REPLACE INTO ratings
      (fencerid, weapon, boutid, ts_mu, ts_sigma, prev_ts_mu, prev_ts_sigma)
      VALUES
      (%(fencerid)s, '%(weapon)s', %(boutid)s, %(ts_mu)f, %(ts_sigma)f, %(prev_ts_mu)f, %(prev_ts_sigma)f)
      """ % {
            "fencerid": fencerid,
            "weapon": weapon,
            "boutid": boutid,
            "ts_mu": rating.mu,
            "ts_sigma": rating.sigma,
            "prev_ts_mu": prev_rating.mu,
            "prev_ts_sigma": prev_rating.sigma,
        })
        self.FENCER_STATE[(fencerid, weapon)] = (rating.mu, rating.sigma)

    def get_bouts(self, begin_date, end_date, weapon):
        bouts = self.cursor.execute("""
        SELECT b.boutid,
               b.fencer1id,
               b.fencer2id,
               b.score1,
               b.score2,
               b.type,
               e.weapon,
               t.start_date
        FROM bouts b, events e, tournaments t
        WHERE b.eventid = e.eventid
          AND e.tournamentid = t.tournamentid
          AND e.weapon = '%(weapon)s'
          AND t.start_date >= '%(begin_date)s'
          AND t.start_date <= '%(end_date)s'
        ORDER BY t.start_date asc, b.boutid asc
        """ % {
            "begin_date": begin_date,
            "end_date": end_date,
            "weapon": weapon,
        })
        return bouts


def updateRank(db, bout):


    boutid, fencer1id, fencer2id, score1, score2, de_or_pool, weapon, start_date = bout
    oldp1 = db.getLatestRating(fencer1id, boutid, weapon)
    oldp1 = trueskill.Rating(oldp1[0], oldp1[1])
    oldp2 = db.getLatestRating(fencer2id, boutid, weapon)
    oldp2 = trueskill.Rating(oldp2[0], oldp2[1])
    print (oldp1, oldp2)

    if de_or_pool == "de":
        # For now... DE's count double
        if score1 > score2:
            p1, p2 = trueskill.rate_1vs1(oldp1, oldp2)
            p1, p2 = trueskill.rate_1vs1(oldp1, oldp2)
        elif score2 > score1:
            p2, p1 = trueskill.rate_1vs1(oldp2, oldp1)
            p2, p1 = trueskill.rate_1vs1(oldp2, oldp1)
        else:
            p1, p2 = trueskill.rate_1vs1(oldp1, oldp2, drawn=True)
            p1, p2 = trueskill.rate_1vs1(oldp1, oldp2, drawn=True)
    else:
        if score1 > score2:
            p1, p2 = trueskill.rate_1vs1(oldp1, oldp2)
        elif score2 > score1:
            p2, p1 = trueskill.rate_1vs1(oldp2, oldp1)
        else:
            p1, p2 = trueskill.rate_1vs1(oldp1, oldp2, drawn=True)

    db.updateLatestRating(fencer1id, weapon, boutid, p1, oldp1)
    db.updateLatestRating(fencer2id, weapon, boutid, p2, oldp2)
    print (p1, p2)


def main():
    parser = argparse.ArgumentParser(description='rate.py uses Trueskill to rank fencers')
    parser.add_argument("-d", action="store", dest="db", default="data.db",
                        help="Specify target db")
    parser.add_argument("--weapon", action="store", dest="weapon", default=None,
                        help="Specify weapon")
    parser.add_argument("--days", action="store", dest="scrape_lookback", default=7,
                        help="Scrape lookback in calendar days. Default is 7.")
    parser.add_argument("--begin-date", action="store", dest="begin_date", default=None,
                        help="Scrape begin date in yyyy-mm-dd")
    parser.add_argument("--end-date", action="store", dest="end_date", default=datetime.now().isoformat().split("T")[0],
                        help="Scrape end date in yyyy-mm-dd")

    args = parser.parse_args()



    end_date = datetime.strptime(args.end_date, '%Y-%m-%d')

    if args.begin_date is not None:
        begin_date = datetime.strptime(args.begin_date, '%Y-%m-%d')
    else:
        begin_date = datetime.now() - timedelta(days=int(args.scrape_lookback))

    # Setup trueskill
    trueskill.setup(draw_probability=0.0018469)

    database = DBAccess(args.db, begin_date)
    rows = database.get_bouts(begin_date, end_date, args.weapon)

    for row in rows:
        print (row)
        updateRank(database, row)

    database.commit()

if __name__ == "__main__":
    main()

