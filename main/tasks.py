import subprocess
import os
import requests
from celery import shared_task
from dashboard.celery import app
from time import sleep
from .models import FullScan, NucleiTrigger, NucleiScan, CrawlScan, Har, ZapScan, ZapTrigger
import json 
from urllib.parse import urlparse
import time

BLACK_LIST = [".jsp", ".js", ".css", ".jpg", ".png", '.otf', '.xml', '.svg', '.gif', '.eot', '.ttf', '.woff','.woff2',
              ".ico", '.pdf', '.doc', '.docx']

def test(ID):
    pass

@app.task
def run_full_scan(ID):
    scan = FullScan.objects.filter(id=ID)
    domains = scan[0].domains.split('\r\n')
    subfinder_result=[]
    assetfinder_result=[]
    amass_result = []
    subprocess.run(f"mkdir amass/{ID}", shell=True)
    subprocess.run(f"mkdir subfinder/{ID}", shell=True)
    subprocess.run(f"mkdir assetfinder/{ID}", shell=True)

    print("DOMAINS")

    for d in domains:
        subprocess.run(f'subfinder -d {d} -o ./subfinder/{ID}/{d}', shell=True)
    subfinder_result = subprocess.check_output(f'cat ./subfinder/{ID}/*', shell=True)
    subfinder_result = str(subfinder_result).split('\\')
    subfinder_result = subfinder_result[:-1]

    for d in domains:
        subprocess.run(f'assetfinder -subs-only {d} >> ./assetfinder/{ID}/{d}', shell=True)
    assetfinder_result = subprocess.check_output(f'cat ./assetfinder/{ID}/*', shell=True)
    assetfinder_result = str(assetfinder_result).split('\\')
    assetfinder_result = assetfinder_result[:-1]

    
    #Потом раскоментить чтобы пока так для дебага.
    # for d in domains:
    #     subprocess.run(f'amass enum -d {d} -o ./amass/{ID}/{d}', shell=True)

    # amass_result = subprocess.check_output(f'cat ./amass/{ID}/*', shell=True)
    # amass_result = str(assetfinder_result).split('\\')
    # amass_result = assetfinder_result[:-1]

    dedup_domains = []

    for d in subfinder_result:
        if d not in dedup_domains:
            dedup_domains.append(d)

    for d in assetfinder_result:
        if d not in dedup_domains:
            dedup_domains.append(d)

    for d in amass_result:
        if d not in dedup_domains:
            dedup_domains.append(d)
    domains_text = ''
    
    sleep(3)
    for d in dedup_domains:
        domains_text+= str(d) + '\n'
    FullScan.objects.filter(id=ID).update(domains=domains_text, status='Поиск поддоменов завершен')
    full_scan_obj=FullScan.objects.get(id=ID)
    subprocess.run(f"rm -rf ./amass/{ID}", shell=True)
    subprocess.run(f"rm -rf ./subfinder/{ID}", shell=True)
    subprocess.run(f"rm -rf ./assetfinder/{ID}", shell=True)

    # КУСОК КОДА С ЗАПУСКОМ Nuclei
    subprocess.run(f"mkdir ./nuclei/{ID}", shell=True)

    print("Домены отправленные в НУКЛЕЙ")
    print(dedup_domains)
    for d in dedup_domains:
        print('domain is ')
        print(d)
        print(type(d))
        d= d.replace("b'", '')
        nuclei_scan = NucleiScan.objects.create(status='В процессе', domain=d, full_scan=full_scan_obj)
        nuclei_instance=NucleiScan.objects.get(id=nuclei_scan.pk)
        subprocess.run(f"nuclei -u {d} -o ./nuclei/{ID}/{d} -j", shell=True)
        ########
        ##### обработка срабатываний
        #############
        with open(f'./nuclei/{ID}/{d}', 'r') as file1:
            nuclei_result = file1.readlines()
            print(len(nuclei_result))

            jsons_results = []
            for n in nuclei_result:
                jsons_results.append(json.loads(n)) 
            print("json_resulsts")
            print(len(jsons_results))
            for j_r in jsons_results:
                info = j_r.get('info', ' ')
                print("start")
                NucleiTrigger.objects.create(status = 'Не обработано',
                                                description=info.get('description', ' '),
                                                rule=j_r.get('template', ' '),
                                                severity=info.get('severity', ' '),
                                                NucleiScan=nuclei_instance,
                                                domain=d)
                print('finish')
        NucleiScan.objects.filter(id=nuclei_scan.pk).update(status='Сканирование завершено, можно посмотреть результаты')
    FullScan.objects.filter(id=ID).update(status='Сканирование Nuclei завершено, ожидается crawling')
########### CRAWLING 
    scan = FullScan.objects.filter(id=ID)
    dedup_domains = scan[0].domains.split('\n')
    full_scan_obj = FullScan.objects.get(id=ID)
    subprocess.run(f"mkdir ./xurlfinder/{ID}", shell=True)
    print("Домены отправленные в КРАУЛИНГ")
    print(dedup_domains)
    for d in dedup_domains:
        d = d.replace("b'", '')
        print(d)
        crawl_scan = CrawlScan.objects.create(status='В процессе', domain=d, full_scan=full_scan_obj)
        crawl_instanse=CrawlScan.objects.get(id=crawl_scan.pk)
        subprocess.run(f"xurlfind3r -d {d} -o ./xurlfinder/{ID}/{d}", shell=True)
        with open(f'./xurlfinder/{ID}/{d}', 'r') as file1:
            crawl_resulsts = file1.readlines()
            print("json_resulsts")
            print(len(crawl_resulsts))
            #### код дедупликаци 
            clear_urls = [] 
            for url in crawl_resulsts:
                if not black_list_extensions(url) and url not in clear_urls:
                    clear_urls.append(url)
            domains = split_by_domains(clear_urls)
            new_urls = []
            for domain in domains.keys():
                new_urls+=domains[domain]
            for domain in domains.keys():
                domains[domain] = delete_simple_pages(domains[domain])
            dedup_hars = []
            for domain in domains.keys():
                dedup_hars+=domains[domain]
            for j_r in dedup_hars:
                Har.objects.create(har=j_r,
                                   CrawlScan=crawl_instanse,
                                   domain=d,
                                   type='Пасивный')
        CrawlScan.objects.filter(id=crawl_scan.pk).update(status='Пасивное сканирование завершено')
    FullScan.objects.filter(id=ID).update(status='Пасивный сбор HAR завершен')

############ запуск KATANA
    subprocess.run(f"mkdir ./katana/{ID}", shell=True)
    for d in dedup_domains:
        d = d.replace("b'", '')
        print(d)
        crawl_scan = CrawlScan.objects.filter( domain=d, full_scan=ID)
        print(crawl_scan)
        print("ID")
        print(crawl_scan[0].id)
        crawl_instanse=CrawlScan.objects.get(id=crawl_scan[0].id)

        subprocess.run(f"katana -u http://{d} -jc -ct 10  -j -o ./katana/{ID}/{d}", shell=True) ### заменить ct на 1800
        with open(f'./katana/{ID}/{d}', 'r') as file1:
            active_crawl_resulsts = file1.readlines()
            jsons_results = []
            for n in active_crawl_resulsts:
                jsons_results.append(json.loads(n))
            for j_r in jsons_results:
                raw = j_r.get('request').get('endpoint') ## если что заменить на raw
                print("raw is ")
                print(raw)
                Har.objects.create(har=raw,
                    CrawlScan=crawl_instanse,
                    domain=d,
                    type='Активный')
        CrawlScan.objects.filter(id=crawl_scan[0].id).update(status='Активное сканирование завершено')
    FullScan.objects.filter(id=ID).update(status='Активный сбор HAR завершен')
    print("CRAWLING ЗАКОНЧЕН")
    run_zap(ID)
################ ZAP
    crawl_scan = CrawlScan.objects.filter(full_scan=ID)
    print(crawl_scan)
    for i in range(len(crawl_scan)):
        hars = Har.objects.filter(CrawlScan=crawl_scan[i].id)
        print(len(hars))
        print("ЗАПУСК ЗАПА")
        print(hars)
        full_scan_instanse=FullScan.objects.get(id=ID)
        subprocess.run(f'mkdir ./ZAP/{ID}', shell=True)
        try:
            for har in hars:
                zp_scan=ZapScan.objects.create(full_scan=full_scan_instanse, har_id=hars[0], status = 'Новый') ## убрать отсюда индекс
                zap_instanse=ZapScan.objects.get(id=zp_scan.pk)
                print(har.har)
                HAR = har.har
                HAR = HAR.replace('\n','')
                pwd = os.getcwd()
                print(pwd)
                subprocess.run(f"/Applications/ZAP.app/Contents/MacOS/ZAP.sh -cmd -quickurl {HAR} -quickout {pwd}/ZAP/{ID}/{har.id}.json", shell=True)
                with open(f'./ZAP/{ID}/{har.id}.json', 'r') as fcc_file:
                    fcc_data = json.load(fcc_file)
                    if fcc_data.get('site'):
                        alerts=fcc_data.get('site')[0].get('alerts', [])
                    else:
                        alerts = [] 
                    print(len(alerts))
                    for alert in alerts:
                        ZapTrigger.objects.create(Zap_scan=zap_instanse,
                                                har_id=har,
                                                riskdesc=alert['riskdesc'],
                                                instance_metod=alert['instances'][0].get('method', ' '),
                                                instance_url=alert['instances'][0].get('uri', ' '),
                                                instance_param=alert['instances'][0].get('param', ' '),
                                                instance_attack=alert['instances'][0].get('attack', ' '),
                                                instance_evidence=alert['instances'][0].get('evidence', ' '),
                                                instance_otherinfo=alert['instances'][0].get('otherinfo', ' '),
                                                status = 'Не обработано')
                    ZapScan.objects.filter(id=zp_scan.pk).update(status='Сканирование завершено, можно посмотреть результаты')
                    Har.objects.filter(id=har.id).update(status ='Сканирование ZAP завершено, можно посмотреть результаты')
            FullScan.objects.filter(id=ID).update(status='Сканирование полностью завершено')
        except Exception as err:
            print(err)

@app.task
def run_crawl(ID):
    scan = FullScan.objects.filter(id=ID)
    dedup_domains = scan[0].domains.split('\n')
    full_scan_obj = FullScan.objects.get(id=ID)
    subprocess.run(f"mkdir ./xurlfinder/{ID}", shell=True)
    print("Домены отправленные в КРАУЛИНГ")
    print(dedup_domains)
    for d in dedup_domains:
        d = d.replace("b'", '')
        print(d)
        crawl_scan = CrawlScan.objects.create(status='В процессе', domain=d, full_scan=full_scan_obj)
        crawl_instanse=CrawlScan.objects.get(id=crawl_scan.pk)
        subprocess.run(f"xurlfind3r -d {d} -o ./xurlfinder/{ID}/{d}", shell=True)
        with open(f'./xurlfinder/{ID}/{d}', 'r') as file1:
            crawl_resulsts = file1.readlines()
            print("json_resulsts")
            print(len(crawl_resulsts))
            #### код дедупликаци 
            clear_urls = [] 
            for url in crawl_resulsts:
                if not black_list_extensions(url) and url not in clear_urls:
                    clear_urls.append(url)
            domains = split_by_domains(clear_urls)
            new_urls = []
            for domain in domains.keys():
                new_urls+=domains[domain]
            for domain in domains.keys():
                domains[domain] = delete_simple_pages(domains[domain])
            dedup_hars = []
            for domain in domains.keys():
                dedup_hars+=domains[domain]
            for j_r in dedup_hars:
                Har.objects.create(har=j_r,
                                   CrawlScan=crawl_instanse,
                                   domain=d,
                                   type='Пасивный')
        CrawlScan.objects.filter(id=crawl_scan.pk).update(status='Пасивное сканирование завершено')
    FullScan.objects.filter(id=ID).update(status='Пасивный сбор HAR завершен')

    # запуск katana
    subprocess.run(f"mkdir ./katana/{ID}", shell=True)
    for d in dedup_domains:
        d = d.replace("b'", '')
        print(d)
        crawl_scan = CrawlScan.objects.filter( domain=d, full_scan=ID)
        print(crawl_scan)
        print("ID")
        print(crawl_scan[0].id)
        crawl_instanse=CrawlScan.objects.get(id=crawl_scan[0].id)

        subprocess.run(f"katana -u http://{d} -jc -ct 10  -j -o ./katana/{ID}/{d}", shell=True) ### заменить ct на 1800
        with open(f'./katana/{ID}/{d}', 'r') as file1:
            active_crawl_resulsts = file1.readlines()
            jsons_results = []
            for n in active_crawl_resulsts:
                jsons_results.append(json.loads(n))
            for j_r in jsons_results:
                raw = j_r.get('request').get('endpoint') ## если что заменить на raw
                print("raw is ")
                print(raw)
                Har.objects.create(har=raw,
                    CrawlScan=crawl_instanse,
                    domain=d,
                    type='Активный')
        CrawlScan.objects.filter(id=crawl_scan[0].id).update(status='Активное сканирование завершено')
    FullScan.objects.filter(id=ID).update(status='Активный сбор HAR завершен')



@app.task
def run_zap(ID):
    crawl_scan = CrawlScan.objects.filter(full_scan=ID)
    print(crawl_scan)
    for i in range(len(crawl_scan)):
        hars = Har.objects.filter(CrawlScan=crawl_scan[i].id)
        print(len(hars))
        print("ЗАПУСК ЗАПА")
        print(hars)
        full_scan_instanse=FullScan.objects.get(id=ID)
        subprocess.run(f'mkdir ./ZAP/{ID}', shell=True)
        try:
            for har in hars:
                zp_scan=ZapScan.objects.create(full_scan=full_scan_instanse, har_id=hars[0], status = 'Новый') ## убрать отсюда индекс
                zap_instanse=ZapScan.objects.get(id=zp_scan.pk)
                print(har.har)
                HAR = har.har
                HAR = HAR.replace('\n','')
                pwd = os.getcwd()
                print(pwd)
                subprocess.run(f"/Applications/ZAP.app/Contents/MacOS/ZAP.sh -cmd -quickurl {HAR} -quickout {pwd}/ZAP/{ID}/{har.id}.json", shell=True)
                with open(f'./ZAP/{ID}/{har.id}.json', 'r') as fcc_file:
                    fcc_data = json.load(fcc_file)
                    if fcc_data.get('site'):
                        alerts=fcc_data.get('site')[0].get('alerts', [])
                    else:
                        alerts = [] 
                    print(len(alerts))
                    for alert in alerts:
                        ZapTrigger.objects.create(Zap_scan=zap_instanse,
                                                har_id=har,
                                                riskdesc=alert['riskdesc'],
                                                instance_metod=alert['instances'][0].get('method', ' '),
                                                instance_url=alert['instances'][0].get('uri', ' '),
                                                instance_param=alert['instances'][0].get('param', ' '),
                                                instance_attack=alert['instances'][0].get('attack', ' '),
                                                instance_evidence=alert['instances'][0].get('evidence', ' '),
                                                instance_otherinfo=alert['instances'][0].get('otherinfo', ' '),
                                                status = 'Не обработано')
                    ZapScan.objects.filter(id=zp_scan.pk).update(status='Сканирование завершено, можно посмотреть результаты')
                    Har.objects.filter(id=har.id).update(status ='Сканирование ZAP завершено, можно посмотреть результаты')
            FullScan.objects.filter(id=ID).update(status='Сканирование полностью завершено')
        except Exception as err:
            print(err)

def black_list_extensions(url):
    for extension in BLACK_LIST:
        if extension in url:
            return True
    return False 


def split_by_domains(urls):
    domains = {}
    for url in urls:
        host = urlparse(url).hostname
        if host not in domains.keys():
            domains[host] = []
        else:
            domains[host].append(url)
    return domains


def end_with_digits(url):
    if url.endswith("/"):
        url = url[:-1]
    index = url.rfind('/')
    last_path = url[index+1:]
    try:
        a = int(last_path)
        return True
    except:
        return False
    

def delete_simple_pages(urls):
    copy_urls = []
    need_delete = []
    i = 0 
    for url in urls:
        i+=1
        print(i)
        if end_with_digits(url):
            copy_urls.append(url)
            path = get_path_without_last(url)
            for URL in urls:
                if get_path_without_last(URL) == path:
                    need_delete.append(URL)
    result_urls = []
    for url in urls:
        if url not in need_delete:
            result_urls.append(url)
    for url in copy_urls:
        if url not in result_urls:
            result_urls.append(url)
    return result_urls


def get_path_without_last(url):
    url = url.replace('//', '')
    start = url.find('/')
    last = url.rfind('/')
    last_path = url[start:last]
    return last_path


def zap_deduplicate(zap_triggers):
    print("ZAPDeduplicate")
    for zap_trigger in zap_triggers:
        print(zap_trigger.id)
    dedupliceted_triggers = deduplicate_sign(zap_triggers)
    return dedupliceted_triggers

def deduplicate_sign(zap_triggers):
    signs = []
    dedup_triggers = []
    print("Before deduplicate")
    print(len(zap_triggers))
    for zap_trigger in zap_triggers:
        sign = str(zap_trigger.instance_evidence)+str(zap_trigger.instance_url)
        if sign not in signs:
            signs.append(sign)
    for zap_trigger in zap_triggers:
        if str(zap_trigger.instance_evidence)+str(zap_trigger.instance_url) in signs:
            dedup_triggers.append(zap_trigger)
            signs.remove(str(zap_trigger.instance_evidence)+str(zap_trigger.instance_url))
    print("Before after")
    print(len(dedup_triggers))
    return dedup_triggers
