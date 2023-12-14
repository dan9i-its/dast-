from django.shortcuts import render, redirect
from .models import FullScan, NucleiScan, NucleiTrigger, CrawlScan, Har, ZapScan, ZapTrigger, User, Comment
from .forms import FullScanForm
# from .subdomains_enum import run_subs_enum
from .tasks import run_full_scan, test, run_crawl, run_zap, zap_deduplicate
from urllib.parse import urlparse

def index(request):
    return render(request, 'main/index.html')

def scans(request):
    domens = []
    scans = FullScan.objects.order_by('-id') #find(id) order_by(field)
    for i in range(len(scans)-1):
        domens.append(scans[i].domains.split('\n'))
        if domens[i]:
            domens[i][0].replace("b'", '')
       # print(domens[i])
    return render(request, 'main/scans.html', {'title': 'Сканы', 'scans': scans, 'domens': domens})

def zap(request):
    zap_scans = ZapScan.objects.order_by('-id') #find(id) order_by(field) 
    print(len(zap_scans))
    return render(request, 'main/zap.html', {'title': 'Zap Scans', 'zap_scans': zap_scans})

def zap_full_results(request, scan_full_results_id):
    if request.method == "POST":
        ID = request.POST['id']
        comment = request.POST['comment']
        print(comment)
        user_instanse = User.objects.get(id=1)
        com = Comment.objects.create(User=user_instanse, comment=comment)
        comment_instanse = Comment.objects.get(id=com.pk)
        ZapTrigger.objects.filter(id=ID).update(status=request.POST['status'], comment=comment_instanse)
    Full_Scan = FullScan.objects.filter(id=scan_full_results_id)
    ZapScans = ZapScan.objects.filter(full_scan=Full_Scan[0].id)
    zap_triggers = []
    for zap_scan in ZapScans:
        zap_triggers+=ZapTrigger.objects.filter(Zap_scan=zap_scan.id)
    zap_triggers=zap_deduplicate(zap_triggers)
    return render(request, 'main/zap_full_results.html', {'title':f'Результаты {scan_full_results_id}', 'zap_triggers':zap_triggers })

def nuclei(request):
    nuclei_scans = NucleiScan.objects.order_by('-id')
    print(len(nuclei_scans))
    return render(request, 'main/nuclei.html', {'title': 'Nuclei Scans', 'nuclei_scans': nuclei_scans})


def nuclei_results(request, nuclei_results_id):
    if request.method == "POST":
        ID = request.POST['id']
        comment = request.POST['comment']
        print(comment)
        user_instanse = User.objects.get(id=1)
        com = Comment.objects.create(User=user_instanse, comment=comment)
        comment_instanse = Comment.objects.get(id=com.pk)
        NucleiTrigger.objects.filter(id=ID).update(status=request.POST['status'], comment=comment_instanse)
    nuclei_triggers = NucleiTrigger.objects.filter(NucleiScan=nuclei_results_id)
    return render(request, 'main/nuclei_results.html', {'title':f'Результаты {nuclei_results_id}', 'nuclei_triggers':nuclei_triggers })



def zap_results(request, zap_results_id):
    if request.method == "POST":
        ID = request.POST['id']
        comment = request.POST['comment']
        print(comment)
        user_instanse = User.objects.get(id=1)
        com = Comment.objects.create(User=user_instanse, comment=comment)
        comment_instanse = Comment.objects.get(id= com.pk)
        ZapTrigger.objects.filter(id=ID).update(status=request.POST['status'], comment=comment_instanse)
    zap_triggers = ZapTrigger.objects.filter(Zap_scan=zap_results_id)
    return render(request, 'main/zap_results.html', {'title':f'Результаты {zap_results_id}', 'zap_triggers':zap_triggers })


def create(request):
    error=''
    if request.method == "POST":
        form = FullScanForm(request.POST)
        if form.is_valid():
            a = form.save()
            print("Scan id is ")
            print(a.id)
            run_full_scan.delay(a.id)
            return redirect('scans')
        else:
             error="Форма была неверной"
    form = FullScanForm()
    context = {
        'form': form,
        'error': error
    }
    return render (request, 'main/create.html', context)

def crawl_results(request, crawl_results_id):
    crawl_results = Har.objects.filter(CrawlScan=crawl_results_id)
    return render(request, 'main/crawl_results.html', {'title':f'Результаты {crawl_results[0].id}', 'crawl_results':crawl_results })


def crawl(request):
    crawl_scans = CrawlScan.objects.order_by('-id')
    print(len(crawl_scans))
    return render(request, 'main/crawl.html', {'title': 'Crawl Scans', 'crawl_scans': crawl_scans})