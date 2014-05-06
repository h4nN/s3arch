import urllib.parse, socket, urllib.request, urllib.parse, urllib.error
import chardet
import encodings
from thirdparty.urllib3 import *
from thirdparty.urllib3.exceptions import *
from .Response import *
from .RequestException import *

class Requester:
    headers = {
        'User-agent' : 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1468.0 Safari/537.36',
        'Accept-Language': 'en-us',
        'Accept-Encoding': 'identity',
        'Keep-Alive': '300',
        'Connection': 'keep-alive',
        'Cache-Control': 'max-age=0',
    }

    def __init__(self, url, cookie=None, useragent=None, maxPool=1, maxRetries=5, timeout=30, ip=None):
        #if no backslash, append one    
        if url[len(url) - 1] != '/':
            url = url + '/'


        parsed = urllib.parse.urlparse(url)
        self.basePath = parsed.path

        #if not protocol specified, set http by default
        if(parsed.scheme != 'http' and parsed.scheme != 'https'):
            parsed = urllib.parse.urlparse('http://' + url)
            self.basePath = parsed.path
        self.protocol = parsed.scheme

        if (self.protocol != 'http') and (self.protocol != 'https'): 
            self.protocol = 'http'
        

        # Resolve ip address and set host header
        self.host = parsed.netloc.split(':')[0]
        if ip != None:
            self.ip = ip
        else:
            try:
                self.ip = socket.gethostbyname(self.host)
            except socket.gaierror:
                raise RequestException({"message" : "Couldn't resolve DNS"})
        self.headers['Host'] = self.host

        try:
            self.port = parsed.netloc.split(':')[1]
        except IndexError:
            self.port = None

        #Set cookie and user-agent headers
        if cookie != None:
            self.setHeader("Cookie", cookie)
        if useragent != None:
            self.setHeader("User-agent", useragent)
        self.maxRetries = maxRetries
        self.maxPool = maxPool
        self.timeout = timeout
        self.pool = None
        self.encoding = None

        
    def setHeader(self, header, content):
        self.headers[header] = content


    def getConnection(self):
        if (self.pool == None):
            if (self.protocol == 'https'):
                self.pool = HTTPSConnectionPool(self.ip, port=self.port, timeout=self.timeout, maxsize=self.maxPool, block=True, cert_reqs='CERT_NONE',
                                assert_hostname=False)
            else:
                self.pool = HTTPConnectionPool(self.ip, port=self.port, timeout=self.timeout, maxsize=self.maxPool, block=True)

        return self.pool

        
    def request(self, path, method="GET", params="", data=""):
        i = 0
        while i <= self.maxRetries:
            try:
                url = "{0}{1}?{2}".format(self.basePath, path, params)
                response = self.getConnection().request(method, url, headers=self.headers, fields=data, assert_same_host=False)
                
                result = Response(response.status, response.reason, response.headers, self.decode(response.data))
                break
            except (MaxRetryError, ReadTimeoutError, socket.error):
                continue
            finally:
                i = i + 1
        if(i > self.maxRetries):
            raise RequestException({"message" : "There was a problem in the request to: {0}".format(path)})
        return result


    def decode(self, data):
        if self.encoding is not None:
            try:
                to_ret = data.decode(self.encoding)
            except (UnicodeDecodeError, TypeError):
                self.encoding = None

        if self.encoding is None:
            self.encoding = chardet.detect(data)['encoding']
            try:
                to_ret = data.decode(self.encoding)
            except (UnicodeDecodeError, TypeError):
                self.encoding = None

        if self.encoding is None:
            self.encoding = self.guess_encoding(data)
            if self.encoding:
                raise EncodingNotFound('Try using the "encoding" command.')
            try:
                to_ret = data.decode(self.encoding)
            except (UnicodeDecodeError, TypeError):
                self.encoding = None

        if self.encoding is None:
            raise EncodingNotFound('Try using the "encoding" command.')

        return to_ret