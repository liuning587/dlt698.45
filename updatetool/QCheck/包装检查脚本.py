#coding:utf-8

from __future__ import division
import sys, time, datetime, telnetlib, ConfigParser, fileinput, os, re, exceptions, hashlib

#根据文件名，计算md5
def md5sum(filename):
    fd = open(filename,"r")
    fcont = fd.read()
    fd.close()
    fmd5 = hashlib.md5(fcont)
    return fmd5

#
#程序读取配置文件，返回所有配置文件字段。
#
def readConfig(name):
	config=ConfigParser.ConfigParser()

	try:
		with open(name,'r') as cfgFile:
			config.readfp(cfgFile)
			return config
	except IOError, e:
		print '程序没有找到配置文件，程序当前目录需要config.ini文件。'.decode('utf-8')
		sys.exit()

#
#检查配置文件是否正确
#
def checkConfig(config):
	config = readConfig(config);
	items = config.options('items')
	for item in items:
		if not config.has_option('target', item):
			print '配置文件参数数量不匹配'.decode('utf-8')
			sys.exit()

	return config

#准备网络
#
#登陆Telnet，自动输入用户名密码，完成后打印成功
#
def ReadyNet(host, user, passwd):
	try:
		telnetfp = telnetlib.Telnet(host)

		telnetfp.read_until("ogin: ")
		telnetfp.write(user + "\r\n")
		telnetfp.read_until("assword: ")
		telnetfp.write(passwd + "\r\n")
		return telnetfp

	except IOError, e:
		print '网络连接错误，检查网线连接状态。'
		raise e

#
#获取用户输入产品号，附带输入信息；
#
def getInputGiveInfo():
	try:
		print "<按［回车］键，开始检查>".decode('utf-8')
		return str(input('>>>'))
	except IOError, e:
		print '请输入正确格式的信息。'.decode('utf-8')
	except SyntaxError, e:
		return ''

#
#检查所选项目是否正确
#
def CheckMsg(msg, target):
	return msg.find(target)

#
#处理网络连接，逐项检查常规检查
#
def checkDevice(config):
	items = config.options('items')

	for item in items:
		lNet = ReadyNet(config.get('info','host'), config.get('info','user'), config.get('info','passwd'))
		lNet.write(config.get('items', item) + "\r\n")
		lNet.write("exit" + "\r\n")
		msg = lNet.read_all()
		if CheckMsg(msg, config.get('target', item)) == -1:
			print str(config.get('name', item)+"\t错误\t"+config.get('target', item)).decode('utf-8')
		else:
			print str(config.get('name', item)+"\t正确\t"+config.get('target', item)).decode('utf-8')
		lNet.close()
		time.sleep(0.2)
	print "\n\n"

#
#检查进程运行情况
#
def checkProgs(config):
	progs = config.options('progs')
	lNet = ReadyNet(config.get('info','host'), config.get('info','user'), config.get('info','passwd'))
	lNet.write("ps"+ "\r\n")
	lNet.write("exit" + "\r\n")
	msg = lNet.read_all()

	ok = 1

	for p in progs:
		if CheckMsg(msg, "S    "+config.get('progs', p)) == -1:
			print str(p+"\t错误\t").decode('utf-8')
			ok = 0
	if ok == 0:
		print "进程运行情况 <<<<<<<<错误>>>>>>>>\n\n".decode('utf-8')
	else:
		print "进程运行情况-正确！\n\n".decode('utf-8')

	lNet.close()

#
#检查设备时间误差
#
def checkDateTime(config):
	lNet = ReadyNet(config.get('info','host'), config.get('info','user'), config.get('info','passwd'))
	lNet.write("date +\"UTC:%Y-%m-%d %T\"" + "\r\n")
	lNet.write("exit" + "\r\n")
	msg = lNet.read_all()

	pos = msg.rfind("UTC")
	deviceDate = datetime.datetime.strptime(msg[pos+4:pos+23], "%Y-%m-%d %H:%M:%S")
	devation = deviceDate - datetime.datetime.now()
	if devation.seconds > 5:
		print "对时\t错误\t时间差距%d秒".decode('utf-8') %devation.seconds
	else:
		print "对时\t正确\t时间差距%d秒".decode('utf-8') %devation.seconds

	lNet.close()

#
#检查设备固件版本
#
def checkSoftVersion(config):
	lNet = ReadyNet(config.get('info','host'), config.get('info','user'), config.get('info','passwd'))
	lNet.write("md5sum /nand/bin/*" + "\r\n")
	lNet.write("exit" + "\r\n")
	msg = lNet.read_all()

	ok = 1

	s = os.sep
	root = "app/"
	for i in os.listdir(root):
		if os.path.isfile(os.path.join(root,i)):
			check_res = md5sum(os.path.join(root,i))

			if msg.find(check_res.hexdigest()) == -1:
				print "版本\t错误\t".decode('utf-8') + i.decode('utf-8')
				ok = 0
	if ok == 0:
		print "程序版本检查 <<<<<<<<错误>>>>>>>>\n\n".decode('utf-8')
	else:
		print "程序版本检查-正确！\n\n".decode('utf-8')

	lNet.close()

#
#检查电池电压
#
def checkBatteryV(config):
	lNet = ReadyNet(config.get('info','host'), config.get('info','user'), config.get('info','passwd'))
	lNet.write("vd bettery" + "\r\n")
	lNet.write("exit" + "\r\n")
	msg = lNet.read_all()

	m = re.findall("\d.{1,1}\d{5,6}", msg)
	batteryV = float(m[0])

	if batteryV > 3.55:
		print "电池\t正确\t电压 %sV" %m[0]
	else:
		print "电池\t错误\t电压 %sV" %m[0]

	lNet.close()

#
#输出设备ID
#
def showDeviceId(config):
	lNet = ReadyNet(config.get('info','host'), config.get('info','user'), config.get('info','passwd'))
	lNet.write("cj id" + "\r\n")
	lNet.write("exit" + "\r\n")
	msg = lNet.read_all()

	print msg[130:]

	lNet.close()

if __name__ == '__main__':
	config = checkConfig("./check.ini")
	while True:
		getInputGiveInfo()

		os.system('cls;clear')
		checkDevice(config)
		checkProgs(config)
		checkSoftVersion(config)
		#checkBatteryV(config)
		checkDateTime(config)
		showDeviceId(config)








