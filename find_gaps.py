import time
import json
import requests
import argparse
import sqlite3
from datetime import datetime, timedelta

def main():
    parser = argparse.ArgumentParser(description='finds gaps in Askfred bout data')
    parser.add_argument("-k", action="store", dest="API_KEY", default="",
                        help="Askfred REST API key")
    parser.add_argument("-d", action="store", dest="db", default="data.db",
                        help="db target")
    args = parser.parse_args()

    API_KEY = args.API_KEY
    conn = sqlite3.connect(args.db, timeout=20)
    db = conn.cursor()

    db.execute("""select tournamentid 
                    from tournaments 
                    where not exists(
                        select * 
                        from tournament_results
                        where tournaments.tournamentid = tournament_results.tournamentid)
                    order by tournamentid asc;""")
    result1 = db.fetchall()
    flat1 = [i for sublist in result1 for i in sublist]
    # print(result)
    db.execute("""select tournamentid 
                    from tournaments 
                    where not exists(
                        select * 
                        from tournament_results
                        where tournaments.tournamentid = tournament_results.tournamentid)
                    order by tournamentid asc;""")
    result2 = db.fetchall()
    flat2 = [i for sublist in result2 for i in sublist]
    final = sorted(flat1 + flat2)

    print(final)
    print(len(final))







if __name__=="__main__":
    main()