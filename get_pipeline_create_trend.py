# -*- coding: utf-8 -*-
import argparse
import csv
import datetime
import os 

from utils import mysql_process_client, get_fields_chinese, autolabel

import matplotlib.pyplot as plt
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

def get_pipeline_create_trend(start=None, end=None, groupby=None, project=None, output=None, encode=None, need_csv=None):
    if not os.path.exists(output):
        os.mkdir(output)

    if start:
        start = datetime.datetime.strptime(start, "%Y-%m-%d").strftime("%Y-%m-%d %H:%M:%S")
    if end:
        end = datetime.datetime.strptime(end, "%Y-%m-%d")
        end += datetime.timedelta(
                hours=23,
                minutes=59,
                seconds=59,
                milliseconds=999
            )
        end = end.strftime("%Y-%m-%d %H:%M:%S")
    time_sql = []
    if start:
        time_sql.append(" CREATE_TIME > '%s' "%start)
    if end:
        time_sql.append(" CREATE_TIME < '%s' "%end)
    client = mysql_process_client()
    cursor = client.cursor()
    
    if project:
        sql_tpl = "SELECT YEAR(CREATE_TIME) AS YEAR, DATE_FORMAT(CREATE_TIME, '%Y-%m') AS MONTH, COUNT(PIPELINE_ID) AS PIPELINE_CREATED_CNT FROM T_PIPELINE_INFO {WHERE} GROUP BY MONTH ORDER BY MONTH"
        csvfile = os.path.join(output, "%s项目每月新建流水线数量.csv"%project)
        title = "%s项目每月流水线新增数量"%project
        xlabel = "月份"
        headers = get_fields_chinese(["YEAR", "MONTH", "PIPELINE_CREATED_CNT"])
            
        if groupby == "week":
            sql_tpl = "SELECT YEAR(CREATE_TIME) AS YEAR, WEEK(CREATE_TIME) as WEEK, COUNT(PIPELINE_ID) AS PIPELINE_CREATED_CNT FROM T_PIPELINE_INFO {WHERE} GROUP BY WEEK ORDER BY WEEK"
            csvfile = os.path.join(output, "%s项目每周新建流水线数量.csv"%project)
            title = "%s项目每周流水线新增数量"%project
            xlabel = "周"
            headers = get_fields_chinese(["YEAR", "WEEK", "PIPELINE_CREATED_CNT"])

        where_sql = []
        where_sql += [" PROJECT_ID = '%s' "%project]
        if time_sql:
            where_sql += time_sql
        where = " WHERE " + " AND ".join(where_sql)
        sql = sql_tpl.format(WHERE=where)
        print("SQL: %s"%sql)
        cursor.execute(sql)
        result = cursor.fetchall()
        rows = list(result)
        if groupby == "week":
            rows = [(row[0], "{year}-{week:02d}".format(year=row[0], week=row[1]), row[2]) for row in rows]
            rows.sort(key=lambda row: row[1])
        if need_csv:
            with open(csvfile, "w", newline="", encoding=encode) as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                writer.writerows(rows)
                

        labels = [row[1] for row in rows]
        y = [row[2] for row in rows]
        x = list(range(len(labels)))
        fig, ax = plt.subplots(figsize=[6.4, 5.2])
        width = 0.35

        p = ax.bar(labels, y, width, label=project)
        autolabel(ax, p)

        ax.set_xlabel(xlabel)
        ax.set_ylabel("流水线新增数/条")
        ax.set_title(title)
        ax.legend()
        plt.xticks(x, labels, rotation=45)
        pngfile = os.path.join(output, title+".png")
        plt.savefig(pngfile, dpi=300)

    else:

        sql = "SELECT YEAR(CREATE_TIME) AS YEAR, DATE_FORMAT(CREATE_TIME, '%Y-%m') AS MONTH, COUNT(PIPELINE_ID) AS PIPELINE_CREATED_CNT FROM T_PIPELINE_INFO {WHERE} GROUP BY MONTH ORDER BY MONTH"
        csvfile = os.path.join(output, "蓝盾每月新建流水线数量.csv")
        title = "蓝盾每月流水线新增数量"
        xlabel = "月份"
        headers = get_fields_chinese(["YEAR", "MONTH", "PIPELINE_CREATED_CNT"])

        if groupby == "week":
            sql = "SELECT YEAR(CREATE_TIME) AS YEAR, WEEK(CREATE_TIME) as WEEK,  COUNT(PIPELINE_ID) AS PIPELINE_CREATED_CNT FROM T_PIPELINE_INFO {WHERE} GROUP BY WEEK ORDER BY WEEK"
            csvfile = os.path.join(output, "蓝盾每周新建流水线数量.csv")
            title = "蓝盾每周流水线新增数量"
            xlabel = "周"
            headers = get_fields_chinese(["YEAR", "WEEK", "PIPELINE_CREATED_CNT"])

        where_sql = ""
        if time_sql:
            where_sql += " WHERE " + " AND ".join(time_sql)
        sql = sql.format(WHERE=where_sql)
        print("SQL: %s"%sql)
        cursor.execute(sql)
        result = cursor.fetchall()
        rows = list(result)
        if groupby == "week":
            rows = [(row[0], "{year}-{week:02d}".format(year=row[0], week=row[1]), row[2]) for row in rows]
            rows.sort(key=lambda row: row[1])
        if need_csv:
            with open(csvfile, "w", newline="", encoding=encode) as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                writer.writerows(rows)
        labels = [row[1] for row in rows]
        y = [row[2] for row in rows]
        fig, ax = plt.subplots(figsize=[6.4, 5.2])
        width = 0.35
        p = ax.bar(labels, y, width, label="流水线新建数量")
        autolabel(ax, p)
        ax.set_xlabel(xlabel)
        ax.set_ylabel('流水线新增数量/条')
        ax.set_title(title)
        ax.legend()
        plt.xticks(rotation=45)
        pngfile = os.path.join(output, title + ".png")
        plt.savefig(pngfile, dpi=300)
    cursor.close()
    client.close()
    print("请查看输出结果文件: %s"%output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="获取指定时间范围内流水线的新建数")
    parser.add_argument("-s", "--start", help="开始时间, 格式为%%Y-%%m-%%d, 如2022-03-29")
    parser.add_argument("-e", "--end", help="结束时间，格式为%%Y-%%m-%%d, 如2022-03-29")
    parser.add_argument("-g", "--groupby", help="分组，每月/每周新增数", default="month")
    parser.add_argument("-p", "--project", help="项目ID，多个项目ID英文逗号分隔，不指定项目名称则默认统计所有项目的构建成功率", default=None)
    parser.add_argument("-o", "--output", help="输出文件路径目录，默认输出目录是当前路径下output", default="output")
    parser.add_argument("-E", "--encode", help="输出文件的编码方式，utf-8/gb18030，默认为gb18030", choices=["utf-8", "gb18030"], default="gb18030")
    parser.add_argument("-x", "--csv", help="是否生成csv", action="store_true")
    args = parser.parse_args()
    if args.start:
        try:
            datetime.datetime.strptime(args.start, "%Y-%m-%d")
        except Exception as e:
            print("start参数格式解析失败，请确认格式为%%Y-%%m-%%d, 如2022-03-29，%s"%e)
    if args.end:
        try:
            datetime.datetime.strptime(args.end, "%Y-%m-%d")
        except Exception as e:
            print("end参数格式解析失败，请确认格式为%%Y-%%m-%%d, 如2022-03-29，%s"%e)
    get_pipeline_create_trend(start=args.start, end=args.end, groupby=args.groupby, project=args.project, output=args.output, encode=args.encode, need_csv=args.csv)
