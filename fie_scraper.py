import requests
from bs4 import BeautifulSoup

import json


def extract_pool_bouts(tables):
    """
    take a list pools of
    { rows: [{ fencerId: id, matches: [null || { score: num, v: won } ] } ] }
    and turn them into a list of
    { winner: id, loser: id }
    """
    pools = tables["_pools"]['pools']
    bouts = []
    for pool in pools:
        try:
            a = pool['rows']
        except:
            continue
        # print(pool)
        ids = [row['fencerId'] for row in pool['rows']]
        # only add a bout if they're the winner to prevent doubling matches
        for r_idx, row in enumerate(pool['rows']):
            for m_idx, match in enumerate(row['matches']):
                if match and match['v']:
                    bouts.append({"winner": ids[r_idx], "loser": ids[m_idx]})
    return bouts


def extract_competition_info(comp):
    out = {
        "id": comp['id'],
        "date": comp['startDate'],
        "weapon": comp['weapon'],
        "type": comp['type'],
    }
    return out


def extract_tableau_bouts(tableau):
    bouts = []

    for table in tableau:
        for name, round in table['rounds'].items():
            for bout in round:
                if bout['fencer1']['isWinner']:
                    bouts.append({"winner": bout['fencer1']['id'], "loser": bout['fencer2']['id']})
                else:
                    bouts.append({"winner": bout['fencer2']['id'], "loser": bout['fencer1']['id']})

    return bouts


def get_competion_list():
    """
    {"name":"","status":"passed","gender":[],"weapon":[],"type":["i"],"season":"-1","level":"","competitionCategory":"","fromDate":"","toDate":"","fetchPage":1}

    :return:
    """
    r = requests.post("https://fie.org/competitions/search", '{"name":"","status":"passed","gender":[],"weapon":[],"type":["i"],"season":"-1","level":"","competitionCategory":"","fromDate":"","toDate":"","fetchPage":1}')






def main():
    # url = "https://fie.org/competitions/2016/242"
    # name = "rio2016"
    url = "https://fie.org/competitions/2020/156"
    name = "cup2020"
    # r = requests.get(url)
    # with open(f"{name}.html", "w") as f:
    #     f.write(r.text)
    text = ""
    with open(f"{name}.html", "r") as f:
        text = f.read()
    soup = BeautifulSoup(text, 'html.parser')
    data = soup.find(id="js-competition")

    # print(data.string)
    lines = data.string.split(";")
    tables = {}
    for line in lines:
        try:
            front, back = line.split("=", 1)
            print(front)
            _, name = front.split('.', 1)
            tables[name.strip()] = json.loads(back)
        except Exception as e:
            print(e)


    print(list(tables.keys()))
    comp = extract_competition_info(tables['_competition'])
    print(comp)
    pools = extract_pool_bouts(tables)
    print(len(pools))
    des = extract_tableau_bouts(tables['_tableau'])
    print(len(des))





if __name__ == '__main__':
    main()