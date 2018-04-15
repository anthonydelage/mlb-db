CREATE OR REPLACE VIEW `statcast_extended`
AS
SELECT
  *,
  (CASE WHEN inning_topbot = 'Top' THEN home_team ELSE away_team END) AS pitcher_team,
  (CASE WHEN inning_topbot = 'Top' THEN away_team ELSE home_team END) AS batter_team,
  ROUND(ATAN((hc_x - 125.42) / (198.27 - hc_y)) * 180 / PI() * 0.75, 2) AS spray_angle_est
FROM
  `mlbdb`.`statcast`
;
