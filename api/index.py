from http.server import BaseHTTPRequestHandler
import urllib.request
import urllib.parse
import json
import ssl

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        # 允许跨域（虽然小程序不强校验CORS，但为了调试方便加上）
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Cookie, X-Wx-Token')
        self.end_headers()

        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        
        try:
            # 接收从小程序传来的 JSON 参数
            params = json.loads(post_data)
            cookie_str = params.get('cookieStr', '')
            token_str = params.get('tokenStr', '')
            keyword = params.get('searchKeyword', '')

            if not cookie_str or not token_str or not keyword:
                self.wfile.write(json.dumps({"error": "缺少必要参数"}).encode('utf-8'))
                return

            # 智能清理 Cookie 前缀
            if cookie_str.lower().startswith('cookie:'):
                cookie_str = cookie_str[7:].strip()

            # 构造向微信公众平台发起的请求
            wx_url = f"https://mp.weixin.qq.com/cgi-bin/wxopen?token={token_str}&lang=zh_CN&f=json&ajax=1&action=self_promote_search&key={urllib.parse.quote(keyword)}"
            
            req = urllib.request.Request(wx_url, method='POST')
            req.add_header('Cookie', cookie_str)
            req.add_header('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:149.0) Gecko/20100101 Firefox/149.0')
            req.add_header('X-Requested-With', 'XMLHttpRequest')
            req.add_header('Referer', f'https://mp.weixin.qq.com/cgi-bin/wxopen?action=list&token={token_str}&lang=zh_CN')
            req.add_header('Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8')

            # 忽略 SSL 证书校验，防止 Vercel 节点证书问题
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            # 发送请求给微信并读取返回结果
            with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
                wx_res_data = response.read().decode('utf-8')
                self.wfile.write(wx_res_data.encode('utf-8'))

        except urllib.error.URLError as e:
            self.wfile.write(json.dumps({"error": f"请求微信服务器失败: {str(e)}"}).encode('utf-8'))
        except Exception as e:
            self.wfile.write(json.dumps({"error": f"代理服务器内部错误: {str(e)}"}).encode('utf-8'))

    def do_OPTIONS(self):
        # 处理预检请求
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Cookie, X-Wx-Token')
        self.end_headers()