1) pip install celery
2) sudo docker run -d -p 6379:6379 redis
3)  celery -A dashboard worker -l info
4)  cd /dashboard
5)  mkdir amass subfinder xurlfinder katana zap
6)  go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
7)  go install -v github.com/owasp-amass/amass/v4/...@master
8)  go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
9) sudo apt install assetfinder
10) go install github.com/projectdiscovery/katana/cmd/katana@latest
11) sudo apt install zaproxy
12) python manage.py runserver
13) see 127.0.0.1:8000
