import requests
import json
import os
import base64
import sys
import glob
from string import Template
import sys
import argparse
import datetime
import natsort

from utils import get_config

def send_mail(mail_list=None, png_dir=None, project=None, report_type=None, need_csv=False):
    print(mail_list)
    print(png_dir)
    print(project)

    cur_dir = os.getcwd()
    png_path = ""
    if os.path.isabs(png_dir):
        png_path = png_dir
    else:
        png_path = os.path.join(cur_dir, png_dir)
    if not os.path.exists(png_path):
        print("%s does not exist"%png_path)
        return

    html_list = []
    attachments = []
    tr_tpl = """ 
            <tr style="background: #FFFFFF;">
                <td colspan="2"><img src="cid:{filename}" style="width:100%"></td>
            </tr>
            <tr style="background: #FFFFFF;">
                <td colspan="4" style="height: 20px;"></td>
            </tr>
    """ 
    abs_filenames = natsort.natsorted(glob.glob(os.path.join(png_path ,"*.png")))
    # filenames = list(map(lambda filename: os.path.basename(filename), abs_filenames))
    print("filenames: %s"%abs_filenames)
    for filename in abs_filenames:
        
        filecontent = base64.b64encode(open(filename, "rb").read())
        file_basename = os.path.basename(filename)
        html = tr_tpl.format(filename=file_basename)
        html_list.append(html)
        attachment = {
            "filename": file_basename,
            "content": filecontent.decode('utf-8'),
            "content_id": file_basename,
            "deposition": "inline",
        }    
        attachments.append(attachment)
    
    if need_csv:
        csv_abs_filenames = natsort.natsorted(glob.glob(os.path.join(png_path ,"*.csv")))
        for filename in csv_abs_filenames:
            filecontent = base64.b64encode(open(filename, "rb").read())
            file_basename = os.path.basename(filename)
            attachment = {
                "filename": file_basename,
                "content": filecontent.decode('utf-8'),
                "content_id": file_basename,
                "deposition": "attachment",
            }    
            attachments.append(attachment)
        
    url = "http://paas.service.consul/api/c/compapi/cmsi/send_mail/"
    content_tpl = """
<!DOCTYPE html>
<html lang="en">

<head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="ie=edge">
    <title>Document</title>
    <style>
        /* table td{ border: 1px black solid;} */
    </style>
</head>

<body>
    <style class="fox_global_style">
        div.fox_html_content {
            background: #F0F1F5;
        }
    </style>
    <style type="text/css">
        body {
            background: #F0F1F5;
        }
    </style>
    <div style="background: #F0F1F5; width: 100%;">
        <table style="margin:0 auto; width: 900px; word-wrap:break-word; word-break:break-all;" border="0" cellspacing="0" cellpadding="0">
            <tbody>
                <tr style="background: #FFFFFF;">
                    <td colspan="4" style="height: 20px; border-left: 1px solid #DCDEE5; border-top: 1px solid #DCDEE5; border-right: 1px solid #DCDEE5; border-top-left-radius: 6px; border-top-right-radius: 6px;">
                    </td>
                </tr>
                <tr style="background: #FFFFFF;">
                    <td style="border-left: 1px solid #DCDEE5;"></td>
                    <td colspan="2" style="height: 36px; font-size: 18px; font-weight: bold; color: #313238;">
                        <span style="color: ${color};">【${num}${type}报】</span>${title}
                    </td>
                    <td style="border-right: 1px solid #DCDEE5;"></td>
                </tr>
                <tr style="background: #FFFFFF;">
                    <td style="border-bottom: 2px solid #F0F1F5; border-left: 1px solid #DCDEE5;"></td>
                    <td colspan="2" style="height: 32px; border-bottom: 2px solid #F0F1F5; color: #63656E; font-size: 14px; vertical-align: text-top; padding-left: 10px;">
                        ${now}</td>
                    <td style="border-bottom: 2px solid #F0F1F5; border-right: 1px solid #DCDEE5;"></td>
                </tr>
                <tr style="background: #FFFFFF;">
                    <td rowspan="100" style="width: 4.5%; min-width: 0; border-left: 1px solid #DCDEE5;">
                    </td>
                    <td width="100" style="height: 40px;"></td>
                    <td></td>
                    <td rowspan="100" style="width: 4.5%; min-width: 0; border-right: 1px solid#DCDEE5;">
                    </td>
                </tr>
    """ + "".join(html_list) + """
                <tr style="background: #FFFFFF;">
                    <td colspan="2" style="height: 40px;"></td>
                </tr>
            </table>
            <table style="margin:0 auto; width: 900px;" border="0" cellspacing="0" cellpadding="0">
                <tr style="background: #FFFFFF;">
                    <td style="height: 58px; border-top: 2px solid #F0F1F5; font-size: 14px; color: #979BA5; border-left: 1px solid #DCDEE5; border-right: 1px solid #DCDEE5; border-bottom: 1px solid #DCDEE5; border-bottom-right-radius: 6px; border-bottom-left-radius: 6px;"
                        align="center">此为系统邮件，请勿回复</td>
                </tr>
            </table>
        </div>
    </body>

    </html>
    """
    color = "#FF9C01"
    num = datetime.datetime.today().strftime("%W")
    if report_type == "月":
        color = "#EA3636"
        num = datetime.datetime.today().strftime("%m")
    title = "蓝盾使用情况报表"
    if project:
        title = "%s项目蓝盾使用情况报表"%project
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    content = Template(content_tpl).safe_substitute(color=color, title=title, now=now, type=report_type, num=num)
    # print(content)
    
    config = get_config()
    data = {
        "bk_app_code": config["bk_app_code"],
        "bk_app_secret": config["bk_app_secret"],
        "bk_username": "admin",
        "receiver": mail_list,
        "title": title,
        "content": content,
        "body_format": "Html",
        "attachments": attachments,
    }
    # print(data)
    headers = {"Content-Type": "application/json"}
    resp = requests.post(url, headers=headers, data=json.dumps(data))
    # print(resp.content)
    print(json.loads(resp.content))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="邮件发送")
    parser.add_argument("-j", "--join", help="发送邮件地址列表，英文逗号,分隔多个邮件地址", required=True)
    parser.add_argument("-w", "--workspace", help="图片存放目录", required=True)
    parser.add_argument("-p", "--project", help="项目ID", default=None)
    parser.add_argument("-t", "--type", help="周/月报", default="周")
    parser.add_argument("-x", "--csv", help="是否发送csv文件", action="store_true")
    # parser.add_argument("-n", "--num", help="x月份/第x周", required=True)
    args = parser.parse_args()

    send_mail(mail_list=args.join, png_dir=args.workspace, project=args.project, report_type=args.type, need_csv=args.csv)
