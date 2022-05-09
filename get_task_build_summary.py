# -*- coding: utf-8 -*-
import argparse
import csv
import pymysql
import json
from collections import defaultdict
import operator
import os


from utils import mysql_process_client, mysql_store_client

import matplotlib.pyplot as plt
import pandas as pd

from matplotlib import font_manager
from matplotlib.font_manager import FontProperties
import matplotlib

fm = font_manager.FontManager()
fm.addfont("chinese.msyh.ttf")
font_manager.fontManager.ttflist.extend(fm.ttflist)
matplotlib.rcParams['font.family'] = 'Microsoft YaHei'

def parse_build_model(model):
    """
    model: T_PIPELINE_BUILD_DETAIL.MODEL的json反序列化对象
    return: atom_count{atom_code: cnt}
    """
    atom_count = defaultdict(lambda: 0) 
    for stage in model["stages"]:
        for container in stage["containers"]:
            for element in container["elements"]:
                if "status" in element:
                    if element["status"] != "SKIP":
                        atom = element["atomCode"]
                        atom_count[atom] += 1
    return atom_count
    

def get_task_build_summary(top=None, output=None, encode=None, need_csv=None):
    if not os.path.exists(output):
        os.mkdir(output)
    store_client = mysql_store_client()
    store_cursor = store_client.cursor()
    atom_sql = "select ATOM_CODE, NAME from T_ATOM group by ATOM_CODE"
    store_cursor.execute(atom_sql)
    atom_result = store_cursor.fetchall()
    atom_map = dict(atom_result)
    print("atom_dict:  %s"%atom_map)

    client = mysql_process_client()
    cursor = client.cursor(pymysql.cursors.SSDictCursor)
    atom_dict = defaultdict(lambda: 0) 
    sql = "SELECT MODEL FROM T_PIPELINE_BUILD_DETAIL"
    print("SQL: %s"%sql)
    cursor.execute(sql)
    result = cursor.fetchone()
    while result:
        model = json.loads(result["MODEL"])
        atom_count = parse_build_model(model)
        for atom, cnt in atom_count.items():
            atom_dict[atom] += cnt
        result = cursor.fetchone()
    rows = list(sorted(atom_dict.items(), key=operator.itemgetter(1), reverse=True))
    top_rows = rows[:top]
    top_rows = [(atom_map.get(row[0], "unknown"), *row) for row in top_rows]
    print("top_rows: %s"%top_rows)
    cursor.close()
    client.close()
    csvfile = os.path.join(output, "10-蓝盾执行次数top%d的插件.csv"%top)
    if need_csv:
        with open(csvfile, "w", newline="", encoding=encode) as f:
            writer = csv.writer(f)
            writer.writerow(["插件名称","插件代码", "执行次数"])
            writer.writerows(top_rows)
        
    # draw a table
    df = pd.DataFrame(top_rows, columns=["插件名称", "插件代码", "执行次数"])
    fig, ax =plt.subplots()
    ax.axis('tight')
    ax.axis('off')
    table = ax.table(cellText=df.values,colLabels=df.columns,cellLoc="center",loc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.auto_set_column_width(col=list(range(len(df.columns))))
    for (row, col), cell in table.get_celld().items():
        if (row == 0):
            cell.set_text_props(fontproperties=FontProperties(weight='bold'))
    ax.set_title("蓝盾执行次数top %d的插件"%top)
    pngfile = os.path.join(output, "10-蓝盾执行次数top%d的插件.png"%top)
    plt.savefig(pngfile, dpi=300)
    print("请查看输出结果文件: %s"%output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="获取各插件执行次数")
    parser.add_argument("-t", "--top", help="插件执行次数前x的插件", default=20, type=int)
    parser.add_argument("-o", "--output", help="输出文件目录，默认输出文件目录是当前路径下的output", default="output")
    parser.add_argument("-E", "--encode", help="输出文件的编码方式，utf-8/gb18030，默认为gb18030", choices=["utf-8", "gb18030"], default="gb18030")
    parser.add_argument("-x", "--csv", help="是否生成csv", action="store_true")
    args = parser.parse_args()
    get_task_build_summary(top=args.top, output=args.output, encode=args.encode, need_csv=args.csv)