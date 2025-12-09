import pandas as pd
import numpy as np

# 读取两个CSV文件
mm_wp_file = r'c:\Users\王翔宇\Desktop\deep_gnss-main1\0509167-gps_res_mm_wp.csv'
ground_truth_file = r'c:\Users\王翔宇\Desktop\deep_gnss-main1\ground_truth.csv'

# 读取数据
mm_wp_df = pd.read_csv(mm_wp_file)
ground_truth_df = pd.read_csv(ground_truth_file)

print(f"mm_wp.csv 数据行数: {len(mm_wp_df)}")
print(f"ground_truth.csv 数据行数: {len(ground_truth_df)}")

# 创建一个新的DataFrame，行数与mm_wp相同
# 使用ground_truth的列结构，但只保留mm_wp的行数
if len(ground_truth_df) > 0:
    # 获取ground_truth的列结构
    columns = ground_truth_df.columns.tolist()
    # 创建与mm_wp行数相同的新DataFrame
    new_ground_truth = pd.DataFrame(index=range(len(mm_wp_df)), columns=columns)
    
    # 填充基本信息（使用第一行的值作为模板）
    if 'collectionName' in columns:
        new_ground_truth['collectionName'] = ground_truth_df.iloc[0]['collectionName']
    if 'phoneName' in columns:
        new_ground_truth['phoneName'] = ground_truth_df.iloc[0]['phoneName']
else:
    # 如果ground_truth为空，创建基本结构
    new_ground_truth = pd.DataFrame({
        'collectionName': ['2020-07-08-US-MTV-1'] * len(mm_wp_df),
        'phoneName': ['Pixel4XL'] * len(mm_wp_df),
        'millisSinceGpsEpoch': [0] * len(mm_wp_df),
        'latDeg': [0] * len(mm_wp_df),
        'lngDeg': [0] * len(mm_wp_df),
        'heightAboveWgs84EllipsoidM': [0] * len(mm_wp_df),
        'timeSinceFirstFixSeconds': [0] * len(mm_wp_df),
        'hDop': [0] * len(mm_wp_df),
        'vDop': [0] * len(mm_wp_df),
        'speedMps': [0] * len(mm_wp_df),
        'courseDegree': [0] * len(mm_wp_df)
    })

# 映射mm_wp的数据到新的DataFrame
for i in range(len(mm_wp_df)):
    new_ground_truth.loc[i, 'latDeg'] = mm_wp_df.loc[i, 'proj_y_deg']  # proj_y_deg -> latDeg
    new_ground_truth.loc[i, 'lngDeg'] = mm_wp_df.loc[i, 'proj_x_deg']  # proj_x_deg -> lngDeg
    new_ground_truth.loc[i, 'millisSinceGpsEpoch'] = mm_wp_df.loc[i, 'timestamp']  # timestamp -> millisSinceGpsEpoch

# 将指定字段全部设置为0
new_ground_truth['heightAboveWgs84EllipsoidM'] = 0
new_ground_truth['timeSinceFirstFixSeconds'] = 0
new_ground_truth['hDop'] = 0
new_ground_truth['vDop'] = 0
new_ground_truth['speedMps'] = 0
new_ground_truth['courseDegree'] = 0

# 保存更新后的ground_truth文件
output_file = r'c:\Users\王翔宇\Desktop\deep_gnss-main1\ground_truth_updated0509167csv'
new_ground_truth.to_csv(output_file, index=False)

print(f"映射完成！更新后的文件保存为: {output_file}")
print(f"最终数据行数: {len(new_ground_truth)}")
print(f"mm_wp数据行数: {len(mm_wp_df)}")

# 显示前几行结果
print("\n更新后的前5行数据:")
print(new_ground_truth[['millisSinceGpsEpoch', 'latDeg', 'lngDeg', 'heightAboveWgs84EllipsoidM', 'timeSinceFirstFixSeconds', 'hDop', 'vDop', 'speedMps', 'courseDegree']].head())