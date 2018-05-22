#!/bin/bash

LOOKBACK=$1
date -u >> update_times.log
date -u >> errors.log
python collect_data.py -d data.db --scrape-results --days $LOOKBACK -k $(cat apikey.txt) &>> errors.log;
python collect_data.py -d data.db --scrape-promotions --days $LOOKBACK -k $(cat apikey.txt) &>> errors.log;
python collect_data.py -d data.db --scrape-fencer-update -k $(cat apikey.txt);
python rate.py -d data.db --weapon Epee --days $LOOKBACK &>> errors.log;
python rate.py -d data.db --weapon Foil --days $LOOKBACK &>> errors.log; 
python rate.py -d data.db --weapon Saber --days $LOOKBACK &>> errors.log;
cat queries/adjusted_ratings.sql | sqlite3 data.db &>> errors.log;
#cp data.db ~/pointcontrol/data.db
#echo "drop table ratings; drop table promotions;" | sqlite3 data_mini.db;
#echo "vacuum;" | sqlite3 data_mini.db;
#cp /Users/davidma/askfred/data_mini.db /Users/davidma/Dropbox/Public/data.db
#
#sleep 600;
#ssh ubuntu@54.186.126.173 bash dailyjobs.sh
echo "All done!" >> ./collect.log
echo "All done!" >> ./errors.log
