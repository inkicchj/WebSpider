import requests
from bs4 import BeautifulSoup

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0'
}

url = 'http://yjgl.yanan.gov.cn/search.html?keywords=灾害&size=15&tab=wj&scope=title,resourceSummary,resourceContent,mc_listtitle'
response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, 'html.parser')
li_list = soup.select(".ss_list ul li .info_item")

for li in li_list:
    if li.a:  # 检查是否存在 <a> 标签
        title = li.a.text.strip()  # 获取链接文字内容
        push_time = li.select(".table .table-td")[1].text  # 发布时间
        detail_url = li.a['href']  # 获取链接地址

        # 应急管理局应该是部门文件

        # 获取文件内容 纯文本
        if detail_url:
            resp = requests.get(detail_url, headers=headers)

            if resp and resp.status_code == 200:
                resp.encoding = resp.apparent_encoding
                content = resp.text
                soup = BeautifulSoup(content, "html.parser")

                # 文件内容
                article = soup.find(attrs={"id": "article"})
                if article:
                    article = article.text.strip()

                # 文件来源
                source = soup.find(attrs={"class": "m-txt-crm"}).\
                    find_all("span")[0].text.replace("来源：", "")

        print(title, "爬取成功！")

