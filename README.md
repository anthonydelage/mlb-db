mlb-db
==========

Create and update a local MLB stats database.

Gets data from two main sources:

  - Baseball Savant (Statcast): uses the Statcast Search tool to collect pitch-by-pitch logs for every team and player. Sample download [here](https://baseballsavant.mlb.com/statcast_search/csv?all=true&hfPT=&hfAB=&hfBBT=&hfPR=&hfZ=&stadium=&hfBBL=&hfNewZones=&hfGT=&hfC=&hfSea=2018%7C&hfSit=&player_type=pitcher&hfOuts=&opponent=&pitcher_throws=&batter_stands=&hfSA=&game_date_gt=&game_date_lt=&team=NYY&position=&hfRO=&home_road=&hfFlag=&metric_1=&hfInn=&min_pitches=0&min_results=0&group_by=name-event&sort_col=pitches&player_event_sort=api_p_release_speed&sort_order=desc&min_abs=0&type=details&).
  - Crunchtime Baseball player maps: a full table of MLB players by MLBAM ID, mapped to their IDs in other "systems". Sample download [here](http://crunchtimebaseball.com/master.csv).

Requirements
----------

  - Python 3.6+ (versions 3.5 and earlier haven't been tested)
  - MySQL 5.7

Setup
----------

Before using any of this tool's features, a MySQL databse and user need to be created with credentials matching those in `config.yaml`. For example:

```
> mysql -u root -p

mysql> create database if not exists mlbdb;
mysql> create user mlb-db;
mysql> grant all on mlbdb.* to 'mlb-db'@'localhost' identified by 'password'
```

Usage
----------

To set up the repository's [virtual evironment](http://docs.python-guide.org/en/latest/dev/virtualenvs/), run:

```
> make venv
```

To initialize the database's tables, run:

```
> make db
```

To run a standard database update (all events for the current year and players), run:

```
> make update
```

To make more granular updates, refer to the documentation in the `src/update.py` file. For example, to update all events from 2016 without updating the `players` table, run:

```
> python src/update.py --year=2016 --no-statcast
```

Useful Resources
----------

  - [Research Notebook: New Format for Statcast Data Export at Baseball Savant](https://www.fangraphs.com/tht/research-notebook-new-format-for-statcast-data-export-at-baseball-savant/)
  - [Exploring Statcast Data from Baseball Savant](https://baseballwithr.wordpress.com/2016/08/15/exploring-statcast-data-from-baseball-savant/)
  - [Baseball Savant Data Scraping](https://github.com/alanrkessler/savantscraper/blob/master/scraper.ipynb)
