CREATE VIEW `ad-fantasy-baseball.core.statcast_extended`
AS
SELECT
  *,
  (CASE WHEN inning_topbot = 'Top' THEN home_team ELSE away_team END) AS pitcher_team,
  (CASE WHEN inning_topbot = 'Top' THEN away_team ELSE home_team END) AS batter_team,
  ROUND(ATAN((hc_x - 125.421) / (198.271 - hc_y)) * 180 / ACOS(-1) * 0.75, 2) AS spray_angle_est
FROM
  `ad-fantasy-baseball.core.statcast`
;
