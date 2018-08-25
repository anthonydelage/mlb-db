mlb-db
==========

Loads a range of baseball data to Google BigQuery.

Gets data from three main sources:

  - Baseball Savant (Statcast): uses the Statcast Search tool to collect pitch-by-pitch logs for every team and player. Sample download [here](https://baseballsavant.mlb.com/statcast_search/csv?all=true&hfPT=&hfAB=&hfBBT=&hfPR=&hfZ=&stadium=&hfBBL=&hfNewZones=&hfGT=&hfC=&hfSea=2018%7C&hfSit=&player_type=pitcher&hfOuts=&opponent=&pitcher_throws=&batter_stands=&hfSA=&game_date_gt=&game_date_lt=&team=NYY&position=&hfRO=&home_road=&hfFlag=&metric_1=&hfInn=&min_pitches=0&min_results=0&group_by=name-event&sort_col=pitches&player_event_sort=api_p_release_speed&sort_order=desc&min_abs=0&type=details&).
  - Crunchtime Baseball player maps: a full table of current MLB players by MLBAM ID, mapped to their IDs in other "systems". Sample download [here](http://crunchtimebaseball.com/master.csv).
  - Baseball Prospectus player maps: a table containing current and retired MLB players. Not as complete as the Crunchtime Baseball maps. Sample download [here](http://www.baseballprospectus.com/sortable/playerids/playerid_list.csv).
  - Bill Petti's weather (hosted on Box): a table containing weather for every game. Sample [here](https://app.box.com/v/gamedayboxscoredata).

Requirements
----------

  - Python 3.6+ (versions 3.5 and earlier haven't been tested)

Setup
----------

Before using any of this tool's features, a BigQuery project and dataset need to be created with credentials matching those in `config.yaml`.

For a quick introduction to Google BigQuery, have a look at their tutorials [here](https://cloud.google.com/bigquery/docs/tutorials).

Usage
----------

To set up the repository's [virtual evironment](http://docs.python-guide.org/en/latest/dev/virtualenvs/), run:

```
> make venv
```

To initialize the BigQuery tables, run:

```
> make tables
```

To run a standard database update (all events for the current year and players), run:

```
> make data
```

To make more granular updates, refer to the documentation in the `src/data.py` file. For example, to update all events from 2016 without updating the `players` table, run:

```
> python src/update.py --year=2016 --no-players
```

Useful Resources
----------

  - [Research Notebook: New Format for Statcast Data Export at Baseball Savant](https://www.fangraphs.com/tht/research-notebook-new-format-for-statcast-data-export-at-baseball-savant/)
  - [Exploring Statcast Data from Baseball Savant](https://baseballwithr.wordpress.com/2016/08/15/exploring-statcast-data-from-baseball-savant/)
  - [Baseball Savant Data Scraping](https://github.com/alanrkessler/savantscraper/blob/master/scraper.ipynb)
