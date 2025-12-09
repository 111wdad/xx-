import pandas as pd
print(pd.__version__)
import numpy as np
import os
import sys
from datetime import datetime, timezone, timedelta

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# 导入项目中的GNSS库
from gnss_lib.ephemeris_manager import EphemerisManager
from gnss_lib.sim_gnss import FindSat
from gnss_lib.constants import gpsconsts

# 读取文件
gnssdata_path = "c:\\Users\\王翔宇\\Desktop\\deep_gnss-main\\0507005-gnssdata.csv"
derived_path = "c:\\Users\\王翔宇\\Desktop\\deep_gnss-main\\Pixel4XL_derived.csv"
output_path = "c:\\Users\\王翔宇\\Desktop\\deep_gnss-main\\mapped_gnssdata.csv"

# 读取文件
gnssdata = pd.read_csv(gnssdata_path)
derived_sample = pd.read_csv(derived_path, nrows=1)

# 只保留GPS L1卫星数据 (ConstellationType == 1)
gnssdata = gnssdata[gnssdata['ConstellationType'] == 1].copy()
print(f"过滤后只保留GPS卫星数据，共 {len(gnssdata)} 条记录")

# 创建新的DataFrame
new_df = pd.DataFrame(columns=derived_sample.columns)

# 初始化星历管理器
ephemeris_manager = EphemerisManager()

# 添加星历数据预下载功能
def ensure_ephemeris_data(ephemeris_manager, timestamps, satellites):
    """
    确保指定时间范围和卫星的星历数据可用
    """
    print("正在检查和下载星历数据...")
    
    # 获取时间范围
    gps_epoch = datetime(1980, 1, 6, 0, 0, 0, tzinfo=timezone.utc)
    unique_timestamps = set(timestamps)
    
    for timestamp in unique_timestamps:
        current_time = gps_epoch + timedelta(milliseconds=timestamp)
        print(f"检查时间戳 {timestamp} ({current_time}) 的星历数据")
        
        try:
            # 尝试获取星历数据，如果不存在会自动下载
            ephemeris_data = ephemeris_manager.get_ephemeris(current_time, satellites)
            
            if ephemeris_data.empty:
                print(f"警告：时间戳 {timestamp} 的星历数据为空")
            else:
                available_sats = ephemeris_data['sv'].unique()
                print(f"成功获取 {len(available_sats)} 颗卫星的星历数据: {list(available_sats)}")
                
        except Exception as e:
            print(f"下载时间戳 {timestamp} 的星历数据时出错: {e}")
            continue
    
    print("星历数据检查完成")

# 计算卫星钟差的函数
def calculate_satellite_clock_bias(ephemeris_data, gps_time):
    """
    计算卫星钟差
    """
    gpsconst = gpsconsts()
    
    # 计算时间偏移
    timeOffset = gps_time - ephemeris_data['t_oc']
    if abs(timeOffset) > 302400:
        timeOffset = timeOffset - np.sign(timeOffset) * 604800
    
    # 计算钟差多项式修正
    corrPolynomial = (ephemeris_data['SVclockBias'] + 
                     ephemeris_data['SVclockDrift'] * timeOffset + 
                     ephemeris_data['SVclockDriftRate'] * timeOffset**2)
    
    # 计算偏心异常角E (简化计算)
    dt = gps_time - ephemeris_data['t_oe']
    if abs(dt) > 302400:
        dt = dt - np.sign(dt) * 604800
    
    Mcorr = ephemeris_data['deltaN'] * dt
    M = ephemeris_data['M_0'] + (np.sqrt(gpsconst.muearth) * ephemeris_data['sqrtA']**-3) * dt + Mcorr
    
    E = M
    for i in range(10):
        f = M - E + ephemeris_data['e'] * np.sin(E)
        dfdE = ephemeris_data['e'] * np.cos(E) - 1.0
        dE = -f / dfdE
        E = E + dE
    
    # 计算相对论钟差修正
    corrRelativistic = gpsconst.F * ephemeris_data['e'] * ephemeris_data['sqrtA'] * np.sin(E)
    
    # 计算总钟差修正（包括TGD项）
    clockCorr = corrPolynomial - ephemeris_data['TGD'] + corrRelativistic
    
    # 转换为米
    clockBiasM = clockCorr * gpsconst.c
    
    return clockBiasM

# 计算millisSinceGpsEpoch
gnssdata['millisSinceGpsEpoch'] = (gnssdata['TimeNanos'] - gnssdata['FullBiasNanos']) // 1e6

# 获取所有需要的GPS卫星和时间戳
all_timestamps = gnssdata['millisSinceGpsEpoch'].unique()
all_satellites = []

for _, row in gnssdata.iterrows():
    svid = int(row['Svid'])  # 将svid转换为整数
    sv_name = f'G{svid:02d}'  # 只处理GPS卫星
    all_satellites.append(sv_name)

# 去重
all_satellites = list(set(all_satellites))
print(f"需要处理的GPS卫星: {all_satellites}")
print(f"时间范围: {len(all_timestamps)} 个时间戳")

# 预下载星历数据
ensure_ephemeris_data(ephemeris_manager, all_timestamps, all_satellites)

# 基本信息设置
new_df['collectionName'] = 'gnssdata_collection'
new_df['phoneName'] = 'Android'

# 按时间戳和卫星ID分组处理数据
for (timestamp, constellation, svid), group in gnssdata.groupby(['millisSinceGpsEpoch', 'ConstellationType', 'Svid']):
    # 只处理GPS卫星 (constellation == 1)
    if constellation != 1:
        continue
        
    row = {}
    row['millisSinceGpsEpoch'] = timestamp
    row['constellationType'] = constellation
    row['svid'] = svid
    
    # 映射已知字段
    if 'ReceivedSvTimeNanos' in gnssdata.columns:
        row['receivedSvTimeInGpsNanos'] = group['ReceivedSvTimeNanos'].iloc[0]
    else:
        row['receivedSvTimeInGpsNanos'] = 0
        
    # 设置GPS L1信号类型
    row['signalType'] = 'GPS_L1'
    sv_name = f'G{svid:02d}'
    
    # 计算伪距
    LIGHTSPEED = 299792458.0
    
    if 'ReceivedSvTimeNanos' in gnssdata.columns and not group['ReceivedSvTimeNanos'].iloc[0] == 0:
        tRxNanos = (group['TimeNanos'].iloc[0] + group['TimeOffsetNanos'].iloc[0]) - \
                   (group['FullBiasNanos'].iloc[0] + group['BiasNanos'].iloc[0])
        tRxSeconds = 1e-9 * tRxNanos
        tTxSeconds = 1e-9 * (group['ReceivedSvTimeNanos'].iloc[0] + group['TimeOffsetNanos'].iloc[0])
        
        pseudorange_seconds = tRxSeconds - tTxSeconds
        row['rawPrM'] = pseudorange_seconds * LIGHTSPEED
        
        if 'ReceivedSvTimeUncertaintyNanos' in gnssdata.columns:
            row['rawPrUncM'] = LIGHTSPEED * 1e-9 * group['ReceivedSvTimeUncertaintyNanos'].iloc[0]
        else:
            row['rawPrUncM'] = 0
    else:
        row['rawPrM'] = 0
        row['rawPrUncM'] = 0
    
    # 星历相关 - 计算卫星位置、速度和钟差
    try:
        gps_epoch = datetime(1980, 1, 6, 0, 0, 0, tzinfo=timezone.utc)
        current_time = gps_epoch + timedelta(milliseconds=timestamp)
        
        # 获取GPS星历数据
        ephemeris_data = ephemeris_manager.get_ephemeris(current_time, [sv_name])
        
        if not ephemeris_data.empty:
            # 计算GPS时间
            gps_time = (timestamp % (7 * 24 * 3600 * 1000)) / 1000.0
            gps_week = int(timestamp // (7 * 24 * 3600 * 1000))
            print(f"GPS卫星 {sv_name}: GPS时间 = {gps_time:.3f}s, GPS周 = {gps_week}")
            
            # 使用FindSat函数计算卫星位置和速度
            sat_states = FindSat(ephemeris_data, gps_time, gps_week)
            
            if not sat_states.empty:
                sat_row = sat_states.iloc[0]
                
                row['xSatPosM'] = sat_row['x']
                row['ySatPosM'] = sat_row['y']
                row['zSatPosM'] = sat_row['z']
                row['xSatVelMps'] = sat_row['vx']
                row['ySatVelMps'] = sat_row['vy']
                row['zSatVelMps'] = sat_row['vz']
                
                # 计算卫星钟差
                ephem_row = ephemeris_data.iloc[0]
                clock_bias_m = calculate_satellite_clock_bias(ephem_row, gps_time)
                row['satClkBiasM'] = clock_bias_m
                
                print(f"成功计算GPS卫星 {sv_name} 的位置、速度和钟差")
            else:
                print(f"警告：FindSat返回空结果，卫星 {sv_name}")
                row['xSatPosM'] = row['ySatPosM'] = row['zSatPosM'] = 0
                row['xSatVelMps'] = row['ySatVelMps'] = row['zSatVelMps'] = 0
                row['satClkBiasM'] = 0
        else:
            print(f"警告：无法获取GPS卫星 {sv_name} 的星历数据")
            row['xSatPosM'] = row['ySatPosM'] = row['zSatPosM'] = 0
            row['xSatVelMps'] = row['ySatVelMps'] = row['zSatVelMps'] = 0
            row['satClkBiasM'] = 0
            
    except Exception as e:
        print(f"计算GPS卫星 {sv_name} 状态时发生错误：{e}")
        row['xSatPosM'] = row['ySatPosM'] = row['zSatPosM'] = 0
        row['xSatVelMps'] = row['ySatVelMps'] = row['zSatVelMps'] = 0
        row['satClkBiasM'] = 0
    
    # 设置其他字段为0
    for col in derived_sample.columns:
        if col not in row:
            row[col] = 0
    
    # 添加到新的DataFrame
    new_df = pd.concat([new_df, pd.DataFrame([row])], ignore_index=True)

# 保存结果
new_df.to_csv(output_path, index=False)

print(f"转换完成，结果已保存到 {output_path}")
print(f"成功处理了 {len(new_df)} 条GPS L1观测数据")
