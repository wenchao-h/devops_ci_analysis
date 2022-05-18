# -*- coding: utf-8 -*-
import argparse
import csv
import os

from utils import mysql_process_client, mysql_store_client, get_fields_chinese

import matplotlib.pyplot as plt
import pandas as pd

from matplotlib import font_manager
from matplotlib.font_manager import FontProperties
import matplotlib

fm = font_manager.FontManager()
fm.addfont("chinese.msyh.ttf")
font_manager.fontManager.ttflist.extend(fm.ttflist)
matplotlib.rcParams['font.family'] = 'Microsoft YaHei'

def get_task_summary(count=False, project=None, output=None, encode=None, need_csv=None):
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
    cursor = client.cursor()

    sql = "SELECT ATOM_CODE, COUNT(ATOM_CODE) AS ATOM_USED FROM T_PIPELINE_MODEL_TASK GROUP BY ATOM_CODE ORDER BY ATOM_USED DESC"
    if project:
        sql = "SELECT ATOM_CODE, COUNT(ATOM_CODE) AS ATOM_USED FROM T_PIPELINE_MODEL_TASK WHERE PROJECT_ID = '%s' GROUP  BY ATOM_CODE ORDER BY ATOM_USED DESC"%project
    print("SQL: %s"%sql)
    cursor.execute(sql)
    result = cursor.fetchall()

    cursor.close()
    client.close()
    # rows = list(result)
    rows = [(atom_map.get(row[0], "unknown"), *row) for row in result]
    print("rows: %s"%rows)
    csvfile = os.path.join(output, "9-bkci-plugin-use-info.csv")
    title = "蓝盾插件数量"
    pngfile = os.path.join(output, "9-bkci-plugin-counts.png")
    if project:
        csvfile = os.path.join(output, "9-%s-project-plugin-use-info.csv"%project)
        title = "%s项目插件数量"%project
        pngfile = os.path.join(output, "9-%s-project-plugin-counts.png"%project)
    if need_csv:
        with open(csvfile, "w", newline="", encoding=encode) as f:
            writer = csv.writer(f)
            headers = get_fields_chinese(["ATOM_NAME", "ATOM_CODE", "ATOM_USED"])
            writer.writerow(headers)
            writer.writerows(rows)
    
    if count:
        atom_count = len(rows)
        print(atom_count)
        fig, ax = plt.subplots(figsize=[3.5,3])

        ax.text(0.5, 0.5, str(atom_count), size=50,
                ha="right", va="center",
                c="#3A6BA8"
                )

        ax.text(0.625, 0.5, "个", size=25,
                ha="right", va="center",
                c="#3A6BA8"
                )
        ax.text(0.45, 0.4, "被引用次数大于0的插件数量",
                ha="center", va="top",
                c="#A2A2A2")

        ax.set_title(title)
        # ax.axis('tight')
        ax.axis("off")
        plt.savefig(pngfile, dpi=300)
        print("end")
    else:
        # draw a table
        df = pd.DataFrame(rows, columns=["插件名称","插件代码", "插件被引用次数"])
        fig, ax =plt.subplots(figsize=[6.4, 6.8])
        # ax.axis('tight')
        ax.axis('off')
        table = ax.table(cellText=df.values,colLabels=df.columns,cellLoc="center", loc="center", bbox=[0,0,1,1])
        table.auto_set_font_size(False)
        table.set_fontsize(8)
        table.auto_set_column_width(col=list(range(len(df.columns))))
        for (row, col), cell in table.get_celld().items():
            if (row == 0):
                cell.set_text_props(fontproperties=FontProperties(weight='bold'))
        title = "插件被流水线使用情况"
        pngfile = os.path.join(output, "8-bkci-plugin-use-info.png")
        if project:
            title = "插件被%s项目使用情况"%project
            pngfile = os.path.join(output, "8-%s-project-plugin-use-info.png"%project)
        ax.set_title(title)
        plt.savefig(pngfile, dpi=300)
    print("请查看输出结果文件: %s"%output)    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="获取插件使用情况")
    parser.add_argument("-c", "--count", help="统计插件数量", action="store_true")
    parser.add_argument("-p", "--project", help="项目ID")
    parser.add_argument("-o", "--output", help="输出文件目录，默认输出文件目录是当前路径下的output", default="output")
    parser.add_argument("-e", "--encode", help="输出文件的编码方式，utf-8/gb18030，默认为gb18030", choices=["utf-8", "gb18030"], default="gb18030")
    parser.add_argument("-x", "--csv", help="是否生成csv", action="store_true")
    args = parser.parse_args()
    get_task_summary(count=args.count, project=args.project, output=args.output, encode=args.encode, need_csv=args.csv)