#encoding: utf8
import time
import aiml
import os, sys
import json
import urllib

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from urlparse import urlparse
from QA.QACrawler import baike
from QA.Tools import Html_Tools as QAT
from QA.Tools import TextProcess as T
from QA.QACrawler import search_summary

HOST_NAME = '0.0.0.0'
PORT_NUMBER = 9000

class MyHandler(BaseHTTPRequestHandler):
    def do_HEAD(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        paths = {
            '/answer': {'status': 200}
        }

        if self.path in paths:
            self.respond(paths[self.path])
        else:
            self.respond({'status': 500})

    def handle_http(self, status_code, path):
        self.send_response(status_code)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        query = urlparse(self.path).query
        query_components = dict(qc.split("=") for qc in query.split("&"))
        question = urllib.unquote(query_components["q"])
        try:
          content = [ans for ans in answer(question)]
        except Exception as e:
          content = [e.message]

        return json.dumps(content, ensure_ascii=True)

    def respond(self, opts):
        response = self.handle_http(opts['status'], self.path)
        self.wfile.write(response)


def createBot():
  mybot = aiml.Kernel()
  mybot.learn(os.path.split(os.path.realpath(__file__))[0]+"/QA/resources/std-startup.xml")
  mybot.learn(os.path.split(os.path.realpath(__file__))[0] + "/QA/resources/bye.aiml")
  mybot.learn(os.path.split(os.path.realpath(__file__))[0] + "/QA/resources/tools.aiml")
  mybot.learn(os.path.split(os.path.realpath(__file__))[0] + "/QA/resources/bad.aiml")
  mybot.learn(os.path.split(os.path.realpath(__file__))[0] + "/QA/resources/funny.aiml")
  mybot.learn(os.path.split(os.path.realpath(__file__))[0] + "/QA/resources/OrdinaryQuestion.aiml")
  mybot.learn(os.path.split(os.path.realpath(__file__))[0] + "/QA/resources/Common conversation.aiml")
  return mybot

def answer(question):
  if len(question) > 600:
      print mybot.respond("句子长度过长")
      raise Exception("Too Long")
  elif question.strip() == '':
      print mybot.respond("无")
      raise Exception("No Input")

  print question
  message = T.wordSegment(question)
  # 去标点
  print 'word Seg:'+ message
  print '词性：'
  words = T.postag(question)


  if message == 'q':
      exit()
  else:
    response = mybot.respond(message)

    print response

    if response == "":
        raise Exception("No Answer")
    # 百科搜索
    elif response[0] == '#':
      # 匹配百科
      if response.__contains__("searchbaike"):
        print "searchbaike"
        print response
        res = response.split(':')
        #实体
        entity = str(res[1]).replace(" ","")
        #属性
        attr = str(res[2]).replace(" ","")
        print entity+'<---->'+attr

        ans = baike.query(entity, attr)
        # 如果命中答案
        if type(ans) == list:
          print 'Eric：' + QAT.ptranswer(ans,False)
          return [QAT.ptranswer(ans,False)]
        elif ans.decode('utf-8').__contains__(u'::找不到'):
          #百度摘要+Bing摘要
          print "通用搜索"
          ans = search_summary.kwquery(question)

      # 匹配不到模版，通用查询
      elif response.__contains__("NoMatchingTemplate"):
        print "NoMatchingTemplate"
        ans = search_summary.kwquery(question)


      if len(ans) == 0:
        raise Exception("No Answer")
      elif len(ans) >1:
        print "不确定候选答案"
        print 'Eric: '
        for a in ans:
          print a.encode("utf8")
        return [a.encode("utf8") for a in ans]
      else:
        print 'Eric：' + ans[0].encode("utf8")
        return [ans[0].encode("utf8")]

    # 匹配模版
    else:
      print 'Eric：' + response
      return [response]


if __name__ == '__main__':
  #初始化jb分词器
    T.jieba_initialize()

    #切换到语料库所在工作目录
    mybot_path = './'
    mybot = createBot()
    os.chdir(mybot_path)

    server_class = HTTPServer
    httpd = server_class((HOST_NAME, PORT_NUMBER), MyHandler)
    print(time.asctime(), 'Server Starts - %s:%s' % (HOST_NAME, PORT_NUMBER))
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print(time.asctime(), 'Server Stops - %s:%s' % (HOST_NAME, PORT_NUMBER))