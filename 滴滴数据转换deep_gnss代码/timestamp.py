import pandas as pd
import os

def convert_timestamps_to_relative():
    # 文件路径
    mapped_derived_path = "mapped_gnssdata0509167.csv"
    ground_truth_path = "ground_truth_updated0509167.csv"
    
    # 读取mapped_derived.csv文件
    print("正在读取mapped_derived.csv...")
    mapped_df = pd.read_csv(mapped_derived_path)
    
    # 读取ground_truth.csv文件
    print("正在读取ground_truth.csv...")
    ground_truth_df = pd.read_csv(ground_truth_path)
    
    # 获取各自文件的第一个时间戳作为基准
    first_timestamp_mapped = int(mapped_df['millisSinceGpsEpoch'].iloc[0] / 1000)  # mapped_derived需要除以1000并取整
    first_timestamp_ground_truth = ground_truth_df['millisSinceGpsEpoch'].iloc[0]  # ground_truth直接使用
    
    print(f"mapped_derived基准时间戳（第一个时间戳/1000并取整）: {first_timestamp_mapped}")
    print(f"ground_truth基准时间戳（第一个时间戳）: {first_timestamp_ground_truth}")
    
    # 显示原始时间戳范围
    print(f"\n原始时间戳范围:")
    print(f"mapped_derived: {mapped_df['millisSinceGpsEpoch'].min()} 到 {mapped_df['millisSinceGpsEpoch'].max()}")
    print(f"ground_truth: {ground_truth_df['millisSinceGpsEpoch'].min()} 到 {ground_truth_df['millisSinceGpsEpoch'].max()}")
    
    # 处理mapped_derived.csv
    # 先除以1000并取整，再减去自己的第一个时间戳（除以1000并取整后）
    mapped_df['millisSinceGpsEpoch'] = (mapped_df['millisSinceGpsEpoch'] / 1000).astype(int) - first_timestamp_mapped
    
    # 处理ground_truth.csv
    # 直接减去自己的第一个时间戳
    ground_truth_df['millisSinceGpsEpoch'] = ground_truth_df['millisSinceGpsEpoch'] - first_timestamp_ground_truth
    
    # 保存修改后的文件
    mapped_output_path = "0509167_derived.csv"
    ground_truth_output_path = "0509167ground_truth.csv"
    
    print("\n正在保存mapped_derived_relative.csv...")
    mapped_df.to_csv(mapped_output_path, index=False)
    
    print("正在保存ground_truth_relative.csv...")
    ground_truth_df.to_csv(ground_truth_output_path, index=False)
    
    # 显示转换结果统计
    print("\n转换完成！")
    print(f"mapped_derived.csv: {len(mapped_df)} 行数据")
    print(f"  - 相对时间戳范围: {mapped_df['millisSinceGpsEpoch'].min():.1f} 到 {mapped_df['millisSinceGpsEpoch'].max():.1f}")
    
    print(f"ground_truth.csv: {len(ground_truth_df)} 行数据")
    print(f"  - 相对时间戳范围: {ground_truth_df['millisSinceGpsEpoch'].min():.1f} 到 {ground_truth_df['millisSinceGpsEpoch'].max():.1f}")
    
    print(f"\n输出文件:")
    print(f"  - {mapped_output_path}")
    print(f"  - {ground_truth_output_path}")
    
    # 验证第一个时间戳都是0
    print(f"\n验证（两个文件的第一个时间戳都应该是0）:")
    print(f"  - mapped_derived第一个相对时间戳: {mapped_df['millisSinceGpsEpoch'].iloc[0]:.1f}")
    print(f"  - ground_truth第一个相对时间戳: {ground_truth_df['millisSinceGpsEpoch'].iloc[0]:.1f}")
    
    return mapped_df, ground_truth_df

if __name__ == "__main__":
    try:
        mapped_df, ground_truth_df = convert_timestamps_to_relative()
        
        # 显示前几行数据作为验证
        print("\n=== mapped_derived_relative.csv 前5行 ===")
        print(mapped_df[['collectionName', 'phoneName', 'millisSinceGpsEpoch']].head())
        
        print("\n=== ground_truth_relative.csv 前5行 ===")
        print(ground_truth_df[['collectionName', 'phoneName', 'millisSinceGpsEpoch']].head())
        
    except Exception as e:
        print(f"处理过程中出现错误: {e}")