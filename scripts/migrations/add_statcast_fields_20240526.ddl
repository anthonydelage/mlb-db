ALTER TABLE `ad-fantasy-baseball.core.statcast`
ADD COLUMN IF NOT EXISTS delta_home_win_exp NUMERIC;

ALTER TABLE `ad-fantasy-baseball.core.statcast`
ADD COLUMN IF NOT EXISTS delta_run_exp NUMERIC;

ALTER TABLE `ad-fantasy-baseball.core.statcast`
ADD COLUMN IF NOT EXISTS bat_speed NUMERIC;

ALTER TABLE `ad-fantasy-baseball.core.statcast`
ADD COLUMN IF NOT EXISTS swing_length NUMERIC;