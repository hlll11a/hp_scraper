from numpy import gradient
import streamlit as st
import requests
from bs4 import BeautifulSoup
import json
import time
import csv
import re
import pandas as pd
import base64

def scp_hpg(area_cd,page_num):
    out = []
    for i in range(1,page_num+1):
        res = requests.get(f'https://www.hotpepper.jp/SA11/{area_cd}/lst/bgn{i}/')
        soup = BeautifulSoup(res.text, 'html.parser')
        page_lst = json.loads(soup.find("script",type="application/ld+json").contents[0])["itemListElement"]
        for page in page_lst:
            res = requests.get(page["url"])
            soup = BeautifulSoup(res.text, 'html.parser')
            try:
                name = soup.find("title").text.rstrip("＜ネット予約可＞ | ホットペッパーグルメ'").split("(")[0]
                area = soup.find("title").text.rstrip("＜ネット予約可＞ | ホットペッパーグルメ'").split("(")[1].split("/")[0]
                genre = soup.find("title").text.rstrip("＜ネット予約可＞ | ホットペッパーグルメ'").split("(")[1].split("/")[1].rstrip(")")
                tel = soup.find("span",class_="telNumber").text
            except:
                name = ""
                area = ""
                genre = ""
                tel = ""
            out.append([name,page["url"],area,genre,tel])
            # st.text([name,page["url"],area,genre,tel])
            time.sleep(2)
        st.text(f"{i}ページ目まで完了")
    return out

def scp_hpb(area_cd,page_num,cat):
    out = []
    for i in range(1,page_num+1):
        if cat == "salon":
            res = requests.get(f'https://beauty.hotpepper.jp/svcSA/{area_cd}/salon/PN{i}.html')
        else:
            res = requests.get(f'https://beauty.hotpepper.jp/{cat}/svcSA/{area_cd}/salon/PN{i}.html')
        soup = BeautifulSoup(res.text, 'html.parser')
        url_l = [soup.find_all("li",class_="searchListCassette")[i].find("h3",class_="slcHead").a.get('href').split("?")[0]+"tel/" for i in range(len(soup.find_all("li",class_="searchListCassette")))]
        
        for url in url_l:
            res = requests.get(url)
            soup = BeautifulSoup(res.text, 'html.parser')   
            # 店舗名
            try:
                name = soup.title.text.rstrip("の電話番号｜ホットペッパービューティー")
            except:
                name = "取得に失敗"
            # 電話番号
            try:
                tel = soup.find("td",class_="fs16 b").text.rstrip()
            except:
                tel = ""
            
            # タグ
            try:
                res = requests.get(url.rstrip("/tel/"))
                soup = BeautifulSoup(res.text, 'html.parser')
                tags = str([e.text for e in soup.find_all("li",class_= lambda value: value and value.startswith("fl iS offL kr")) if e.text != "ジャンル"])
            except:
                tags = ""
            
            out.append([name,url.rstrip("tel/"),tags,tel])
            time.sleep(2)
        st.text(f"{i}ページ目まで完了")
    return out 

def disp_num(store_num,max_page):
    st.text(f"合計{store_num}店舗 {max_page}ページ")
    to_page = st.number_input('なんページめまで取得するか',step=1,min_value=1,max_value = int(max_page) )
    st.text(f"約{20*to_page*2}秒かかります")
    return to_page

hp = st.sidebar.selectbox(
    "グルメ or ビューティー",
    ("グルメ", "ビューティー")
)


if hp == "グルメ":
    res = requests.get(f'https://www.hotpepper.jp/SA11/')
    soup = BeautifulSoup(res.text, 'html.parser')
    area2cd = {}
    area_tag_lst = soup.find("div",class_="areaSA11").find_all('li')

    for area_tag in area_tag_lst:
        area2cd[area_tag.text] = area_tag.contents[0].get("href").split("/")[2]

    area = st.sidebar.selectbox("エリア",area2cd.keys())
    area_cd = area2cd[area]
    
    res = requests.get(f'https://www.hotpepper.jp/SA11/{area_cd}/lst/bgn1/')
    soup = BeautifulSoup(res.text, 'html.parser')
    store_num = soup.find("span",class_="fcLRed bold fs18 padLR3").text
    max_page = soup.find("li",class_="lh27").text.rstrip("ページ").split("/")[1]
    to_page = disp_num(store_num,max_page)
 
    if st.button('取得開始'):
        st.write('開始')
        out = scp_hpg(area_cd,to_page)
        st.write('完了')
        df_download= pd.DataFrame(out)
        df_download.columns=["名前","URL","エリア","ジャンル","電話番号"]
        csv = df_download.to_csv(index=False)
        b64 = base64.b64encode(csv.encode()).decode()  
        linko= f'<a href="data:file/csv;base64,{b64}" download="{hp}_{area}.csv">ダウンロード</a>'
        st.markdown(linko, unsafe_allow_html=True)

if hp == "ビューティー":
    res = requests.get(f'https://beauty.hotpepper.jp/svcSA/')
    genre_dic = {"ネイル・まつげサロン":"nail","リラクサロン":"relax","エステサロン":"esthe"}
    genre = st.sidebar.selectbox("ジャンル",genre_dic.keys())
    genre_cd = genre_dic[genre]
    soup = BeautifulSoup(res.text, 'html.parser')
    area2cd = {}
    for el in soup.find_all("ul",class_="routeMa"):
        for e in el.find_all("li"):
            area2cd[e.contents[0].text] = e.contents[0].get("href").split("/")[-2]
    area = st.sidebar.selectbox("エリア",area2cd.keys())
    area_cd = area2cd[area]
    if genre_cd == "salon":
        res = requests.get(f'https://beauty.hotpepper.jp/svcSA/{area_cd}/salon/PN1.html')
    else:
        res = requests.get(f'https://beauty.hotpepper.jp/{genre_cd}/svcSA/{area_cd}/salon/PN1.html')
    soup = BeautifulSoup(res.text, 'html.parser')
    store_num = soup.find("span",class_="numberOfResult").text
    max_page = soup.find("p",class_="pa bottom0 right0").text.strip().rstrip("次へ").strip().rstrip("ページ").split("/")[1]
    to_page = disp_num(store_num,max_page)

    if st.button('取得開始'):
        st.write('開始')
        out = scp_hpb(area_cd,to_page,genre_cd)
        st.write('完了')
        df_download= pd.DataFrame(out)
        df_download.columns=["名前","URL","ジャンル","電話番号"]
        csv = df_download.to_csv(index=False)
        b64 = base64.b64encode(csv.encode()).decode()  
        linko= f'<a href="data:file/csv;base64,{b64}" download="{hp}_{genre}_{area}.csv">ダウンロード</a>'
        st.markdown(linko, unsafe_allow_html=True)




