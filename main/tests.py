

with open('/Users/d.bezrukov/Documents/MY_DASHBOARD/dashboard/juice_shop.json', 'r') as file1:
    active_crawl_resulsts = file1.readlines()
    jsons_results = []
    for n in active_crawl_resulsts:
        jsons_results.append(json.loads(n))
    for j_r in jsons_results:
        raw = j_r.get('request').get('raw') ## если что заменить на raw
        print("raw is ")
        print(raw)
