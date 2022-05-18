# -*- coding: utf-8 -*-
import argparse
import csv
import datetime
import os
import textwrap as twp

from utils import mysql_process_client, get_fields_chinese

import matplotlib.pyplot as plt
import pandas as pd

from matplotlib import font_manager
from matplotlib.font_manager import FontProperties
import matplotlib

fm = font_manager.FontManager()
fm.addfont("chinese.msyh.ttf")
font_manager.fontManager.ttflist.extend(fm.ttflist)
matplotlib.rcParams['font.family'] = 'Microsoft YaHei'


def get_pipeline_summary(days=None, project=None, top=None, count=None, output=None, encode=None, need_csv=None):
    client = mysql_process_client()
    now = datetime.datetime.now()
    end = now - datetime.timedelta(days=days)
    end_time = end.strftime("%Y-%m-%d %H:%M:%S")
    if not os.path.exists(output):
        os.mkdir(output)
    cursor = client.cursor()
    sql_tpl = "SELECT T_PIPELINE_BUILD_SUMMARY.PROJECT_ID, T_PIPELINE_INFO.PIPELINE_NAME, LATEST_END_TIME FROM T_PIPELINE_BUILD_SUMMARY LEFT JOIN T_PIPELINE_INFO ON T_PIPELINE_BUILD_SUMMARY.PIPELINE_ID=T_PIPELINE_INFO.PIPELINE_ID  {WHERE}  ORDER BY T_PIPELINE_BUILD_SUMMARY.LATEST_END_TIME ASC"
    sql = ""
    if project:
        projects = project.split(",")
        projects = list(map(lambda proj: " '%s' "%proj, projects))
        projects = ",".join(projects)
        project_sql = [" T_PIPELINE_BUILD_SUMMARY.PROJECT_ID IN (%s) "%projects]
        internal_pipeline_sql = [" T_PIPELINE_INFO.PIPELINE_NAME NOT LIKE '100%' "]
        end_time_sql = [" LATEST_END_TIME < '%s' "%end_time]
        where = " WHERE " + " AND ".join(project_sql + end_time_sql + internal_pipeline_sql)
        sql = sql_tpl.format(WHERE=where)
        
        
    else:
        internal_pipeline_sql = [" T_PIPELINE_INFO.PIPELINE_NAME NOT LIKE '100%' "]
        end_time_sql = [" LATEST_END_TIME < '%s' "%end_time]
        where = " WHERE " + " AND ".join(internal_pipeline_sql + end_time_sql)
        sql = sql_tpl.format(WHERE=where)
    print("SQL: %s"%sql)  
    cursor.execute(sql)
    result = cursor.fetchall()
    rows = [(*row, (now - row[2]).days) for row in result]
    rows = sorted(rows, key=lambda row: row[3], reverse=True)
    # rows = [ (row[0], twp.fill(row[1], 7), row[2], row[3]) for row in rows ]
    headers = ["PROJECT_ID", "PIPELINE_NAME", "LATEST_END_TIME", "NOT_USE_DAYS"]
    headers = get_fields_chinese(headers)
    csvfile = os.path.join(output, "7-bkci-pipeline-not-used-in-%d-days-top%d.csv"%(days, top))
    pngfile = os.path.join(output, "7-bkci-pipeline-not-used-in-%d-days-top%d.png"%(days, top))
    top_rows = rows[:top]
    title = "蓝盾最近%d天未使用流水线top%d"%(days, top)
    if project:
        csvfile = os.path.join(output, "7-%s-project-pipeline-not-used-in-%d-days-top%d.csv"%(project, days, top))
        top_rows = [(row[1], row[2], row[3]) for row in top_rows]
        headers = get_fields_chinese(["PIPELINE_NAME", "LATEST_END_TIME", "NOT_USE_DAYS"])
        pngfile = os.path.join(output, "7-%s-project-pipeline-not-used-in-%d-days-top%d.png"%(project, days, top))
        title = "%s项目最近%d天未使用流水线top%d"%(project, days, top)
    # else:
    #     csvfile = os.path.join(output, "7-蓝盾最近%d天未使用流水线top%d.csv"%(days, top))
        # top_rows = [(row[0], row[1], row[2], row[3]) for row in top_rows]
    if need_csv:
        with open(csvfile, "w", newline="", encoding=encode) as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)

    # top_rows = rows[:top]
    # top_rows = [(row[1], row[2], row[3]) for row in top_rows]
    # headers = get_fields_chinese(["PIPELINE_NAME", "LATEST_END_TIME", "NOT_USE_DAYS"])
    # draw a table
    df = pd.DataFrame(top_rows, columns=headers)
    fig, ax =plt.subplots()
    ax.axis('off')
    table = ax.table(cellText=df.values,colLabels=df.columns,cellLoc="center", loc="center", bbox=[0,0,1,1])
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.auto_set_column_width(col=list(range(len(df.columns))))
    for (row, col), cell in table.get_celld().items():
        if (row == 0):
            cell.set_text_props(fontproperties=FontProperties(weight='bold'))
    # pngfile = ""
    # title = "蓝盾最近%d天未使用流水线top%d"%(days, top)
    # if project:
    #     pngfile = os.path.join(output, "7-%s项目最近%d天未使用流水线top%d.png"%(project, days, top))
    #     title = "%s项目最近%d天未使用流水线top%d"%(project, days, top)
    # else:
    #     pngfile = os.path.join(output, "7-蓝盾最近%d天未使用流水线top%d.png"%(days, top))
    ax.set_title(title)
    plt.savefig(pngfile, dpi=300)


    cursor.close()
    client.close()
    print("请查看输出结果文件: %s"%output)
                


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="获取指定时间范围内未使用的流水线统计情况")
    parser.add_argument("-d", "--days", help="天数，默认为30天，默认获取最近30天内未使用的流水线", type=int, default=30)
    parser.add_argument("-p", "--project", help="项目ID，默认统计所有项目", default=None)
    parser.add_argument("-t", "--top", help="最近未使用条数前x的流水线", default=20, type=int)
    parser.add_argument("-o", "--output", help="输出文件目录，默认输出文件目录是当前路径下的output", default="output")
    parser.add_argument("-E", "--encode", help="输出文件的编码方式，utf-8/gb18030，默认为gb18030", choices=["utf-8", "gb18030"], default="gb18030")
    parser.add_argument("-x", "--csv", help="是否生成csv", action="store_true")
    args = parser.parse_args()

    get_pipeline_summary(days=args.days, project=args.project, top=args.top, output=args.output, encode=args.encode, need_csv=args.csv)