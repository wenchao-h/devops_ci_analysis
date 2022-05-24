# -*- coding: utf-8 -*-
import argparse
import csv
import datetime
import os
import math
import sys
# import textwrap as twp
# from dateutil.relativedelta import relativedelta

from utils import mysql_process_client, get_fields_chinese, autolabel, get_month_list, get_week_list

import matplotlib.pyplot as plt
import pandas as pd

from matplotlib import font_manager
import matplotlib

fm = font_manager.FontManager()
fm.addfont("chinese.msyh.ttf")
font_manager.fontManager.ttflist.extend(fm.ttflist)
matplotlib.rcParams['font.family'] = 'Microsoft YaHei'

plt.rc('font', size=5.79)          # controls default text sizes
plt.rc('axes', titlesize=10)     # fontsize of the axes title
plt.rc('axes', labelsize=8)    # fontsize of the x and y labels
plt.rc('xtick', labelsize=5.79)    # fontsize of the tick labels
plt.rc('ytick', labelsize=5.79)    # fontsize of the tick labels
plt.rc('legend', fontsize=10)    # legend fontsize
plt.rc('figure', titlesize=5.79)  # fontsize of the figure title

def get_pipeline_summary(start=None, end=None, project=None, groupby=None, output=None, encode=None, need_csv=None):
    client = mysql_process_client()
    cursor = client.cursor()
    start_time = None
    end_time = None
    if start:
        start_time = datetime.datetime.strptime(start, "%Y-%m-%d").strftime("%Y-%m-%d %H:%M:%S")
    if end:
        end_time = datetime.datetime.strptime(end, "%Y-%m-%d")
        end_time += datetime.timedelta(
                hours=23,
                minutes=59,
                seconds=59,
                milliseconds=999
            )
        end_time = end_time.strftime("%Y-%m-%d %H:%M:%S")
    time_sql = []
    if start_time:
        time_sql.append(" LATEST_END_TIME > '%s' "%start_time)
    if end_time:
        time_sql.append(" LATEST_END_TIME < '%s' "%end_time)
    if start is None and end is None:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        time_sql.append(" LATEST_END_TIME < '%s' "%now)

    sql_tpl = ""
    sql = ""
    headers = ["年份", "月份", "活跃数"]
    if groupby == "month":
        sql_tpl = "SELECT YEAR(LATEST_END_TIME) as YEAR, DATE_FORMAT(LATEST_END_TIME, '%Y-%m') AS MONTH, COUNT(PIPELINE_ID) AS PIPELINE_USED_CNT FROM T_PIPELINE_BUILD_SUMMARY {WHERE} GROUP BY MONTH ORDER BY MONTH"
        pass
    elif groupby == "week":
        sql_tpl = "select YEAR(LATEST_END_TIME) as YEAR, WEEK(LATEST_END_TIME) as WEEK, COUNT(PIPELINE_ID) AS PIPELINE_USED_CNT FROM T_PIPELINE_BUILD_SUMMARY {WHERE} GROUP BY WEEK ORDER BY WEEK"
        headers = ["年份", "周", "活跃数"]
        pass
    else:
        print("groupby must be week/month")
        sys.exit(1)
    where_sql = time_sql
    if project:
        where_sql = [" PROJECT_ID = '%s' "%project] + time_sql
    sql = sql_tpl.format(WHERE=" WHERE " + " AND ".join(where_sql))
    print("SQL: %s"%sql)
    cursor.execute(sql)
    result = cursor.fetchall()
    cursor.close()
    client.close()
    rows = list(result)
    if groupby == "week":
        rows = [(item[0], "{year}-{week:02d}".format(year=item[0], week=item[1]), item[2]) for item in rows]
        week_base = [row[1] for row in rows]
        print("week_base: %s"%week_base)
        week_list = get_week_list(start, datetime.datetime.today().strftime("%Y-%m-%d"))
        week_not_in_base = set(week_list) - set(week_base)
        for week in week_not_in_base:
            year = week.split("-")[0]
            rows.append((year, week, 0))

        rows.sort(key=lambda row: row[1])
        print("sorted_rows: %s"%rows)
    elif groupby == "month":
        month_list = get_month_list(start, datetime.datetime.today().strftime("%Y-%m-%d"))
        month_base = [row[1] for row in rows]
        month_not_in_base = set(month_list) - set(month_base)
        for month in month_not_in_base:
            year = month.split("-")
            rows.append((year, month, 0))
        rows.sort(key=lambda row: row[1])
        print("sorted_rows: %s"%rows)
    if groupby == "month":
        xlabel = "月份"
        if project:
            csvfile = os.path.join(output, "1-%s-project-active-pipeline-count-monthly.csv"%project)
            pngfile = os.path.join(output, "1-%s-project-active-pipeline-count-monthly.png"%project)
            title = "%s项目流水线每月活跃数"%project
        else:
            csvfile = os.path.join(output, "1-bkci-active-pipeline-count-monthly.csv")
            pngfile = os.path.join(output, "1-bkci-active-pipeline-count-monthly.png")
            title = "蓝盾流水线每月活跃数"
    elif groupby == "week":
        xlabel = "周"
        if project:
            csvfile = os.path.join(output, "1-%s-project-active-pipeline-count-weekly.csv"%project)
            pngfile = os.path.join(output, "1-%s-project-active-pipeline-count-weekly.png"%project)
            title = "%s项目流水线每周活跃数"%project
        else:
            csvfile = os.path.join(output, "1-bkci-active-pipeline-count-weekly.csv")
            pngfile = os.path.join(output, "1-bkci-active-pipeline-count-weekly.png")
            title = "蓝盾流水线每周活跃数"
    else:
        print("groupby must be week/month")
        sys.exit(1)
    if need_csv:
        with open(csvfile, "w", newline="", encoding=encode) as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)

    fig, ax = plt.subplots(figsize=[6.4, 5.2])
    width = 0.35
    labels = [row[1] for row in rows]
    y = [row[2] for row in rows]
    max_y = max(y)
    ax.set_ylim(0, max_y + math.ceil(max_y/10))
    p = ax.bar(labels, y, width, label="活跃数")
    ax.set_title(title)
    ax.set_ylabel('活跃数/条')
    ax.set_xlabel(xlabel)
    ax.legend()
    plt.xticks(rotation=45)
    autolabel(ax, p)
    plt.savefig(pngfile, dpi=300)

    print("请查看输出结果文件: %s"%output)
                


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="获取指定时间范围内未使用的流水线统计情况")
    parser.add_argument("-s", "--start", help="开始时间, 格式为%%Y-%%m-%%d, 如2022-03-29")
    parser.add_argument("-e", "--end", help="结束时间，格式为%%Y-%%m-%%d, 如2022-03-29")
    parser.add_argument("-p", "--project", help="项目ID，默认统计所有项目", default=None)
    parser.add_argument("-g", "--groupby", help="按照周/月分组",choices=["week", "month"], default="month")
    parser.add_argument("-o", "--output", help="输出文件目录，默认输出文件目录是当前路径下的output", default="output")
    parser.add_argument("-E", "--encode", help="输出文件的编码方式，utf-8/gb18030，默认为gb18030", choices=["utf-8", "gb18030"], default="gb18030")
    parser.add_argument("-x", "--csv", help="是否生成csv", action="store_true")
    args = parser.parse_args()

    get_pipeline_summary(start=args.start, end=args.end, project=args.project, groupby=args.groupby, output=args.output, encode=args.encode, need_csv=args.csv)