# Simple HTTP Server
Simple server based on HTTP protocol with asyncio pool for horizontal scaling

## Architecture overview
Server is based on async execution. [asyncio-pool](https://github.com/gistart/asyncio-pool) is used 
as async coroutines pool.

## Features
* Scaling for n workers
* 200, 400 and 404 response statuses for GET and HEAD requests
* 405 response status for other requests
* Returns file by arbitrary file path in DOCUMENT_ROOT: 
  * calling `/file.ext` returns `DOCUMENT_ROOT/file.ext` 
  * calling `/dir/` returns `DOCUMENT_ROOT/dir/index.html` if exists
* Headers for GET and HEAD requests: _Date, Server, Content-Length, Content-Type, Connection_
* Relevant Content-Type for _.html, .css, .js, .jpg, .jpeg, .png, .gif, .swf files_
* Correctly parses whitespaces and %XX in filenames

## Run

```shell
httpd.py usage: httpd.py [-h] [-i] [-p] [-w] [-r] [-l]
```
#### Options:
  * `-h, --help` - _show help message and exit_
  * `-i , --ip` - _Host address_ (default `localhost`)
  * `-p , --port` - _Port to listen_ (default `8080`)
  * `-w , --workers` - _Number of workers to execute_ (default `8`)
  * `-r , --doc_root` - _Path to documents root_ (default `.`)
  * `-l , --log` - _Path to log file_ (default `./.tmp/logs/logs.txt`)

## Test

#### Tests using the [test-repository](https://github.com/s-stupnikov/http-test-suite)

### Example of running tests:
```shell
git clone git@github.com:s-stupnikov/http-test-suite.git .tmp/http-test-suite
python3 httpd.py -w 100 -r .tmp/http-test-suite &
python3 .tmp/http-test-suite/httptest.py -v
```
#### Results:
```text
directory index file exists ... ok
document root escaping forbidden ... ok
Send bad http headers ... ok
file located in nested folders ... ok
absent file returns 404 ... ok
urlencoded filename ... ok
file with two dots in name ... ok
query string after filename ... ok
slash after filename ... ok
filename with spaces ... ok
Content-Type for .css ... ok
Content-Type for .gif ... ok
Content-Type for .html ... ok
Content-Type for .jpeg ... ok
Content-Type for .jpg ... ok
Content-Type for .js ... ok
Content-Type for .png ... ok
Content-Type for .swf ... ok
head method support ... ok
directory index file absent ... ok
large file downloaded correctly ... ok
post method forbidden ... ok
Server header exists ... ok

----------------------------------------------------------------------
Ran 23 tests in 0.644s

OK
```

### Example of running load tests with ab:
```shell
python3 httpd.py -w 100 -r .tmp/http-test-suite &
ab -n 50000 -c 100 -r http://127.0.0.1:8080/httptest/dir1/dir12/dir123/deep.txt
```

#### Report:
```text
Server Software:        SimpleHTTPServer/1.0
Server Hostname:        127.0.0.1
Server Port:            8080

Document Path:          /httptest/dir1/dir12/dir123/deep.txt
Document Length:        20 bytes

Concurrency Level:      100
Time taken for tests:   27.812 seconds
Complete requests:      50000
Failed requests:        0
Total transferred:      8550000 bytes
HTML transferred:       1000000 bytes
Requests per second:    1797.78 [#/sec] (mean)
Time per request:       55.624 [ms] (mean)
Time per request:       0.556 [ms] (mean, across all concurrent requests)
Transfer rate:          300.21 [Kbytes/sec] received

Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0   33 200.9      0    7104
Processing:     0   14 347.3      5   26726
Waiting:        0   14 347.3      5   26726
Total:          0   47 424.5      5   27774

Percentage of the requests served within a certain time (ms)
  50%      5
  66%      5
  75%      6
  80%      6
  90%      6
  95%      8
  98%   1026
  99%   1061
 100%  27774 (longest request)
```

### Manual testing
* Browser: `Google Chrome Version 107.0.5304.121 (Official Build) (x86_64)`
* Request: `http://localhost:8080/httptest/wikipedia_russia.html`

#### Result:
![img.png](img.png)

## Run Docker container:

* Build image:
```shell
docker build -f Dockerfile -t otpypro-webserver ./ --progress plain
```
* Run Docker container:
```shell
docker run -ti --name otpypro-webserver \                          
--hostname otpypro-webserver \
-p 8080:8080 \
otpypro-webserver sh
```
* Run server
* Run tests