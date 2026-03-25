"""
FIXED PIPELINE — правильное создание признаков

ИСПРАВЛЕНИЯ:
1. Features создаются НА ВСЕХ данных ДО split (сохраняем историю)
2. Target создаётся ПОСЛЕ split (нет leakage)
3. НЕ заполняем lag/change нулями (оставляем NaN)
"""

import pandas as pd
import numpy as np

# Пример правильного pipeline:

# 1. Загрузка данных
full_raw = data[['date', 'Name', 'open', 'high', 'low', 'close', 'volume']].copy()
full_raw['date'] = pd.to_datetime(full_raw['date'])

# 2. Добавляем макро данные
for col in ['key_rate', 'usd_rub', 'oil_price', 'inflation']:
    if col in data.columns:
        full_raw[col] = data[col]

# 3. Очистка (winsorization пороги только на train!)
train_temp = full_raw[full_raw['date'].dt.year < TRAIN_END_YEAR].copy()
quantile_thresholds = DataValidator.compute_winsorization_thresholds(train_temp)
full_raw = DataValidator.clean(full_raw, quantile_thresholds=quantile_thresholds)

feature_pipeline = FeaturePipeline(max_features=Config.MAX_FEATURES)

full_features_list = []
for name, group in full_raw.groupby('Name'):
    group_features = feature_pipeline.create_all_features(group.copy())
    full_features_list.append(group_features)

full_df = pd.concat(full_features_list, ignore_index=True)

print(f"Всего: {len(full_df):,} строк, {len(feature_pipeline.feature_columns)} признаков")

# 5. ✅ ТЕПЕРЬ split ПО ВРЕМЕНИ (признаки уже созданы!)
train_df = full_df[full_df['date'].dt.year < TRAIN_END_YEAR].copy()
val_df = full_df[
    (full_df['date'].dt.year >= TRAIN_END_YEAR) &
    (full_df['date'].dt.year < TEST_START_YEAR)
].copy()
test_df = full_df[full_df['date'].dt.year >= TEST_START_YEAR].copy()

# 6. ✅ Target ТОЛЬКО ПОСЛЕ split!
train_df['target'] = TripleBarrierLabeler.get_labels(train_df, PT_RATIO, SL_RATIO, TB_WINDOW)
val_df['target'] = TripleBarrierLabeler.get_labels(val_df, PT_RATIO, SL_RATIO, TB_WINDOW)
test_df['target'] = TripleBarrierLabeler.get_labels(test_df, PT_RATIO, SL_RATIO, TB_WINDOW)

# 7. Drop последних window строк
def drop_last_window(df, window):
    return df.groupby('Name').apply(lambda x: x.iloc[:-window]).reset_index(drop=True)

train_df = drop_last_window(train_df, TB_WINDOW)
val_df = drop_last_window(val_df, TB_WINDOW)
test_df = drop_last_window(test_df, TB_WINDOW)

# 8. Feature correlation filtering (на train)
corr_matrix = train_df[feature_pipeline.feature_columns].corr(min_periods=1).abs()
upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
to_drop = [column for column in upper.columns if any(upper[column] > 0.95)]

if len(to_drop) > 0:
    feature_pipeline.feature_columns = [c for c in feature_pipeline.feature_columns if c not in to_drop]

print(f"Train: {len(train_df):,} строк")
print(f"Val: {len(val_df):,} строк")
print(f"Test: {len(test_df):,} строк")
print(f"Признаков: {len(feature_pipeline.feature_columns)}")
