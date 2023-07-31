# -*- coding: utf-8 -*-
"""
Created on Tue Jun  7 16:13:29 2022

@author: AugurWorkStation
"""


# -*- coding: utf-8 -*-
"""
Created on Mon May 23 11:00:20 2022

@author: AugurWorkStation
"""

from shapely.geometry import shape
import geopandas as gpd
import os
from collections import Counter

import copy
import matplotlib.pyplot as plt
import time
from shapely.geometry import Polygon
from tqdm import tqdm,trange


def topology_check2(gdf):
    # 将数据框转换为投影坐标系
    gdv = gdf.copy()
    gdv_sindex = gdv.sindex
    # 创建一个空的多边形列表
    polys = []
    drop_list = []
    wait_list = []
    # 遍历所有多边形
    for index, row in gdf.iterrows():
        if index in wait_list:
            continue
        # 获取多边形几何对象
        poly = row['geometry']
        poly = poly.buffer(0.001)
        polys.append(poly)
        possible_intersects_idx = list(gdv_sindex.intersection(poly.bounds))

        for idx in possible_intersects_idx:
            if idx == index or idx in polys:
                continue
            possible_intersect_poly = gdv.loc[idx, 'geometry']
            possible_intersect_poly = possible_intersect_poly.buffer(0.001)
            if poly.intersects(possible_intersect_poly):
                intersect_area = poly.intersection(possible_intersect_poly).area
                # 计算两个多边形的面积比例
                poly_area_ratio = intersect_area / poly.area
                possible_intersect_poly_area_ratio = intersect_area / possible_intersect_poly.area
                # 如果两个多边形的面积比例都大于0.3，则判断哪个多边形应该被删除
                if poly_area_ratio > 0.3 and possible_intersect_poly_area_ratio > 0.3:
                    if possible_intersect_poly.area > poly.area:
                        if index not in drop_list:
                            drop_list.append(index)
                    elif poly_area_ratio == possible_intersect_poly_area_ratio:
                        drop_list.append(index)
                        wait_list.append(idx)
                    else:
                        if idx not in drop_list:
                            drop_list.append(idx)
                elif poly_area_ratio > 0.3:
                    drop_list.append(index)
                    break
                elif possible_intersect_poly_area_ratio > 0.3:
                    drop_list.append(idx)
                else:
                    continue
    return drop_list



if __name__ == '__main__':
    road_path = r'./shp/0.shp'
    out = r'./spatial_deduplication'
    shp_ = []
    if os.path.isfile(road_path):
        shp_.append(road_path)
    else:
        for root,dirs,files in os.walk(road_path):
            for i in files:
                if i.endswith('.shp'):
                    name = os.path.join(root,i)
                    shp_.append(name)
    shp_1 = shp_
    for i in tqdm(shp_1):
        j = os.path.basename(i)

        gdc= gpd.read_file(i,encoding='gbk')
        gdf = gdc.copy()
        be = len(gdf)
        gdf=gdf.drop_duplicates(subset=['geometry'])
        
        try:
            gdf.to_crs('EPSG:4326')
        except:
            gdf = gdf.set_crs('EPSG:4326', allow_override=True)
        gdf.reset_index(drop=True,inplace=True)
        start=time.time()
        drop_list=topology_check2(gdf.to_crs('EPSG:3857'))
        gdf.drop(axis=0,index=drop_list,inplace=True)
        gdf.reset_index(drop=True,inplace=True)
        gdf.to_crs('EPSG:4326')
        af = len(gdf)
        if os.path.isfile(out):
            gdf.to_file(out,encoding='gbk')
        else:
            gdf.to_file(os.path.join(out,j),encoding='gbk')
        end=time.time()
        print(end-start,'前：',be,'后：',af)
