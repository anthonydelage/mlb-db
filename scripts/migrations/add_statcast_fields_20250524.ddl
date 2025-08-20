ALTER TABLE `ad-fantasy-baseball.core.statcast`
ADD COLUMN IF NOT EXISTS estimated_slg_using_speedangle NUMERIC;

ALTER TABLE `ad-fantasy-baseball.core.statcast`
ADD COLUMN IF NOT EXISTS delta_pitcher_run_exp NUMERIC;

ALTER TABLE `ad-fantasy-baseball.core.statcast`
ADD COLUMN IF NOT EXISTS hyper_speed NUMERIC;

ALTER TABLE `ad-fantasy-baseball.core.statcast`
ADD COLUMN IF NOT EXISTS home_score_diff INTEGER;

ALTER TABLE `ad-fantasy-baseball.core.statcast`
ADD COLUMN IF NOT EXISTS bat_score_diff INTEGER;

ALTER TABLE `ad-fantasy-baseball.core.statcast`
ADD COLUMN IF NOT EXISTS home_win_exp NUMERIC;

ALTER TABLE `ad-fantasy-baseball.core.statcast`
ADD COLUMN IF NOT EXISTS bat_win_exp NUMERIC;

ALTER TABLE `ad-fantasy-baseball.core.statcast`
ADD COLUMN IF NOT EXISTS age_pit_legacy INTEGER;

ALTER TABLE `ad-fantasy-baseball.core.statcast`
ADD COLUMN IF NOT EXISTS age_bat_legacy INTEGER;

ALTER TABLE `ad-fantasy-baseball.core.statcast`
ADD COLUMN IF NOT EXISTS age_pit INTEGER;

ALTER TABLE `ad-fantasy-baseball.core.statcast`
ADD COLUMN IF NOT EXISTS age_bat INTEGER;

ALTER TABLE `ad-fantasy-baseball.core.statcast`
ADD COLUMN IF NOT EXISTS n_thruorder_pitcher INTEGER;

ALTER TABLE `ad-fantasy-baseball.core.statcast`
ADD COLUMN IF NOT EXISTS n_priorpa_thisgame_player_at_bat INTEGER;

ALTER TABLE `ad-fantasy-baseball.core.statcast`
ADD COLUMN IF NOT EXISTS pitcher_days_since_prev_game INTEGER;

ALTER TABLE `ad-fantasy-baseball.core.statcast`
ADD COLUMN IF NOT EXISTS batter_days_since_prev_game INTEGER;

ALTER TABLE `ad-fantasy-baseball.core.statcast`
ADD COLUMN IF NOT EXISTS pitcher_days_until_next_game INTEGER;

ALTER TABLE `ad-fantasy-baseball.core.statcast`
ADD COLUMN IF NOT EXISTS batter_days_until_next_game INTEGER;

ALTER TABLE `ad-fantasy-baseball.core.statcast`
ADD COLUMN IF NOT EXISTS api_break_z_with_gravity NUMERIC;

ALTER TABLE `ad-fantasy-baseball.core.statcast`
ADD COLUMN IF NOT EXISTS api_break_x_arm NUMERIC;

ALTER TABLE `ad-fantasy-baseball.core.statcast`
ADD COLUMN IF NOT EXISTS api_break_x_batter_in NUMERIC;

ALTER TABLE `ad-fantasy-baseball.core.statcast`
ADD COLUMN IF NOT EXISTS arm_angle NUMERIC;

ALTER TABLE `ad-fantasy-baseball.core.statcast`
ADD COLUMN IF NOT EXISTS attack_angle NUMERIC;

ALTER TABLE `ad-fantasy-baseball.core.statcast`
ADD COLUMN IF NOT EXISTS attack_direction NUMERIC;

ALTER TABLE `ad-fantasy-baseball.core.statcast`
ADD COLUMN IF NOT EXISTS swing_path_tilt NUMERIC;

ALTER TABLE `ad-fantasy-baseball.core.statcast`
ADD COLUMN IF NOT EXISTS intercept_ball_minus_batter_pos_x_inches NUMERIC;

ALTER TABLE `ad-fantasy-baseball.core.statcast`
ADD COLUMN IF NOT EXISTS intercept_ball_minus_batter_pos_y_inches NUMERIC;
