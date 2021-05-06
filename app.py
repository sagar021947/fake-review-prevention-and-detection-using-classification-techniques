from flask import Flask, render_template, session, request, redirect, url_for, make_response
import csv
import time,random,math,re
import smtplib, ssl
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier
from collections import Counter
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer


apps = Flask(__name__)
apps.secret_key = 'eshop@online'

selCat=['AC Adapters', 'Headsets', 'Phones','Unlocked Cell Phones','Tablets', 'Bluetooth Speakers', 'Smart Watches & Accessories', 'Digital SLR Cameras', 'Cameras', 'SIM Cards & Tools', 'Microphones', 'Security & Surveillance', 'Coffee Filters', 'Replacement Pitcher Water Filters', 'Canning', 'Laptop & Netbook Computer Accessories', 'Speaker Systems', 'USB Flash Drives']
prodData={'asin':[],'title':[],'cat':[],'subCat':[],'imgUrl':[],'desc':[],'salRank':[],'avgRate':[],'noRvw':[],'brand':[],'price':[]}
reviewData={'asin':[],'rvrID':[],'rvrName':[],'rvwTxt':[],'pcat':[],'psubCat':[],'summary':[],'ptitle':[],'ratings':[],'rvwTim':[],'pred':[]}
WORD = re.compile(r'\w+')
clsfyUser=0
clsfyRvw=0
unixtime=1388534400
dateandtime=datetime.fromtimestamp(unixtime)

def readData():
	global reviewData,prodData
	for i in reviewData.values():
		del i[:]
	for i in prodData.values():
		del i[:]
	csv.register_dialect('myDialect',delimiter='\t',quoting=csv.QUOTE_ALL,skipinitialspace=True)
	with open("products.txt","r") as f:
		reader = csv.DictReader(f,dialect='myDialect')
		for row in reader:
			prodData['asin'].append(row['asin'])
			prodData['title'].append(row['title'])
			prodData['subCat'].append(row['subCat'])
			prodData['cat'].append(row['cat'])
			prodData['imgUrl'].append(row['imgUrl'])
			prodData['desc'].append(row['desc'])
			prodData['salRank'].append(int(row['salRank']))
			prodData['brand'].append(row['brand'])
			prodData['price'].append(float(row['price']))
	t=[[] for i in range(len(prodData['asin']))]
	with open("processedData.txt","r") as f:
		reader = csv.DictReader(f,dialect='myDialect')
		for row in reader:
			reviewData['asin'].append(row['asin'])
			reviewData['rvrID'].append(row['reviewerID'])
			reviewData['rvrName'].append(row['reviewerName'])
			reviewData['rvwTxt'].append(row['reviewText'])
			reviewData['ratings'].append(float(row['ratings']))
			reviewData['summary'].append(row['summary'])
			reviewData['rvwTim'].append(int(row['reviewTime']))
			reviewData['ptitle'].append(row['ptitle'])
			reviewData['psubCat'].append(row['psubCat'])
			reviewData['pcat'].append(row['pcat'])
			if(row['pred']=='TRUE'):
				reviewData['pred'].append(0)
			else:
				reviewData['pred'].append(1)
			t[prodData['asin'].index(row['asin'])].append(float(row['ratings']))
	prodData['noRvw']=[len(i) for i in t]
	prodData['avgRate']=[round(sum(i)/len(i),1) for i in t]

def verifyUser(det,acc):
	with open('user.txt','r') as csvFile:
		reader = csv.DictReader(csvFile,dialect='myDialect')
		for row in reader:
			if(row['userID']==det[0]):
				if(acc==1 or row['password']==det[1]):
					session['userID']=det[0]
					session['email']=row['email']
					session['name']=reviewData['rvrName'][reviewData['rvrID'].index(det[0])]
					if 'purchase' not in session:
						session['purchase']=''
					return True
		return False

def trainClassifier():
	global clsfyUser,clsfyRvw
	X1=[];X2=[];Y=[]
	with open("RB_features.txt","r") as f:
		reader = csv.reader(f,dialect='myDialect')
		f=True
		for row in reader:
			if(f):
				f=False
				continue
			if(row[14]!=''):
				X1.append([float(i) for i in row[2:8]])
				X2.append([float(i) for i in row[2:14]])
				Y.append(row[14])
	clsfyUser=RandomForestClassifier(n_estimators=100, max_depth=3,random_state=2)
	clsfyRvw=RandomForestClassifier(n_estimators=100, max_depth=3,random_state=2)
	clsfyUser.fit(X1[:int(len(Y)*0.7)],Y[:int(len(Y)*0.7)])
	clsfyRvw.fit(X2[:int(len(Y)*0.7)],Y[:int(len(Y)*0.7)])

def get_cosine(vec1, vec2):
    intersection = set(vec1.keys()) & set(vec2.keys())
    numerator = sum([vec1[x] * vec2[x] for x in intersection])
    sum1 = sum([vec1[x]**2 for x in vec1.keys()])
    sum2 = sum([vec2[x]**2 for x in vec2.keys()])
    denominator = math.sqrt(sum1) * math.sqrt(sum2)
    if not denominator:
        return 0.0
    else:
        return float(numerator) / denominator

def text_to_vector(text):
    words = WORD.findall(text)
    return Counter(words)

def emDiv(listOfWords):
    sid = SentimentIntensityAnalyzer()
    pos_word_list=[]
    neu_word_list=[]
    neg_word_list=[]
    for word in listOfWords:
        if (sid.polarity_scores(word)['compound']) >= 0.3:
            pos_word_list.append(word)
        elif (sid.polarity_scores(word)['compound']) <= -0.3:
            neg_word_list.append(word)
        else:
            neu_word_list.append(word)
    #print('Positive :',pos_word_list);print('Neutral :',neu_word_list);print('Negative :',neg_word_list)  
    numberOfPositive = len(pos_word_list)
    numberOfNegative = len(neg_word_list)
    numberOfNeutral = len(neu_word_list)
    totalWords = len(listOfWords)
    div = (1/3)*(abs((numberOfPositive / totalWords)-(1/3)) + abs((numberOfNegative / totalWords)-(1/3)) + 
    abs((numberOfNeutral / totalWords)-(1/3)))
    return div

def getFet1(scat):
	with open("RB_features.txt","r") as f:
		reader = csv.reader(f,dialect='myDialect')
		f=True;k=True
		for row in reader:
			if(f and session['userID']==row[0]):
				x=[float(i) for i in row[2:8]]
				f=False
			if(session['userID']==row[0] and row[15]==scat):
				x=[float(i) for i in row[2:8]]
				k=False;break
		if(k):
			x[0]=0;x[2]=500000
	return x

def getFet2(ratings,rvwTxt,asin):
	global reviewData
	x=[0]*6
	k=reviewData['asin'].index(asin)
	listOfWords=[]
	sm =0;count=0;maxsim=0;j=k
	while j<len(reviewData['asin']):
		if(asin!=reviewData['asin'][j] and j<24425):
			j=24425
			continue
		if(session['userID']!=reviewData['rvrID'][j] and abs(ratings-reviewData['ratings'][j])<=1):
			vector1 = text_to_vector(rvwTxt)
			vector2 = text_to_vector(reviewData['rvwTxt'][j])
			sim=get_cosine(vector1, vector2)
			if(maxsim<sim):
				maxsim=sim
		if reviewData['rvwTim'][j] < unixtime:
			sm = sm + reviewData['ratings'][j]
			count+=1
		j+=1
	if count<2:
		avg=3
	else:
		avg = sm/count
	x[3]=(abs(ratings - avg))
	x[2]=maxsim
	x[0]=str(ratings/5)   #Feature_7
	tokens = nltk.word_tokenize(rvwTxt)
	tagged = nltk.pos_tag(tokens)
	#print(tagged,i)
	flag = False
	x[5]=0;x[1]=len(tagged)
	for j in range(len(tagged)):
		if(tagged[j][0].isdigit() or tagged[j][0].isupper()):
			x[5]+=1
		if(flag or tagged[j][1][0] not in 'NJRWV'):
			flag=False
			continue
		if(tagged[j][0]=='not' and j<(len(tagged)-1)):
			listOfWords.append(tagged[j][0]+" "+tagged[j+1][0])
			flag=True
		else:
			listOfWords.append(tagged[j][0])
	if(listOfWords==[]):
		x[4]=1
	else:
		x[4]=emDiv(listOfWords)
	return x

def detectSpmr(scat):
	x=getFet1(scat)
	p=clsfyUser.predict([x])[0]
	return (p!='TRUE')

def detectFkRvw(ratings,rvwTxt,asin,scat):
	x=getFet1(scat)+getFet2(ratings,rvwTxt,asin)
	p=clsfyRvw.predict([x])[0]
	return p

@apps.route('/eshop/login', methods=['GET', 'POST'])
def login():
	global selCat,prodData,reviewData
	if request.method == 'GET':
		if 'userID' in session:
			return redirect(url_for('home'))
		else:
			return render_template('Login.html')
	uname= request.form['uname']
	pw= request.form['pw']
	if(verifyUser([uname,pw],0)):
		return redirect('home')
	return render_template('Login.html')
		
@apps.route('/eshop/home', methods=['GET'])
def home():
	global selCat,prodData
	if 'userID' not in session:
		return redirect(url_for('login'))
	topProd=[i for i in zip(prodData['asin'],prodData['title'],prodData['salRank'],prodData['imgUrl'],prodData['avgRate'],prodData['noRvw'])]
	topProd.sort(key=lambda i:i[2])
	resp=make_response(render_template('homeboot.html',category=selCat,topProd=topProd[:6]))
	return resp

@apps.route('/logout', methods=['GET'])
def logout():
	session.pop('userID', None)
	session.pop('email', None)
	session.pop('name', None)
	resp=make_response(redirect(url_for('login')))
	return resp
		
@apps.route('/eshop/product', methods=['GET', 'POST'])
def product():
	global selCat,prodData,reviewData
	asin=request.args.get('asin')
	ky=request.args.get('key')
	dr=0;klink=False
	with open('purchase.txt','r') as csvFile:
		reader = csv.DictReader(csvFile,dialect='myDialect')
		ua=request.user_agent		
		for row in reader:
			if(row['asin']==asin and row['key']==ky):
				verifyUser([row['userID'],''],1)
				dr=1;klink=True
				break
			if('userID' in session and session['userID']==row['userID'] and (row['userID']+asin) in session['purchase'] and row['asin']==asin and row['device']==ua.string[ua.string.index('(')+1:ua.string.index(')')] and row['platform']==ua.platform and row['browser']==ua.browser and row['version']<=ua.version):
				dr=1
	for i in range(len(reviewData['rvrID'])):
		if('userID' in session and session['userID']==reviewData['rvrID'][i] and reviewData['asin'][i]==asin):
			dr=3
	if 'userID' not in session:
		return redirect(url_for('login'))
	ind=prodData['asin'].index(asin)
	if(detectSpmr(prodData['subCat'][ind]) and not klink):
		dr=0
	prod=(prodData['asin'][ind],prodData['title'][ind],prodData['subCat'][ind],prodData['imgUrl'][ind],prodData['avgRate'][ind],prodData['desc'][ind],prodData['noRvw'][ind],prodData['brand'][ind],prodData['price'][ind])
	rvws=[(reviewData['rvrID'][i],reviewData['ratings'][i],reviewData['rvrName'][i],reviewData['summary'][i],reviewData['rvwTxt'][i],reviewData['rvwTim'][i],reviewData['pred'][i]) for i in range(len(reviewData['asin'])) if reviewData['asin'][i]==asin]
	rvws.sort(key=lambda i:i[5],reverse=True)
	rvws.sort(key=lambda i:i[6])
	if request.method == 'GET':
		return render_template('details.html',category=selCat,p=prod,rvws=rvws,dr=dr)

@apps.route('/eshop/srch_det', methods=['GET', 'POST'])
def search():
	global selCat
	if 'userID' not in session:
		return redirect(url_for('login'))
	if request.method == 'GET':
		q=request.args.get('search')
		print(q)
		prods=[]
		for ind in range(len(prodData['asin'])):
			if prodData['asin'][ind]==q or (q.lower() in prodData['title'][ind].lower()) or (prodData['subCat'][ind] in q):
				prods.append((prodData['asin'][ind],prodData['title'][ind],prodData['subCat'][ind],prodData['imgUrl'][ind],prodData['avgRate'][ind],prodData['desc'][ind],prodData['noRvw'][ind],prodData['brand'][ind],prodData['price'][ind]))
		prods.sort(key= lambda i:i[4],reverse=True)
		return render_template('search_det.html',category=selCat,prods=prods)

@apps.route('/navbar', methods=['GET', 'POST'])
def nb():
	return render_template('navbar.html',category=selCat)

@apps.route('/footer', methods=['GET', 'POST'])
def ftr():
	global dateandtime
	return render_template('footer.html',dateandtime=dateandtime)

@apps.route('/eshop/purchase', methods=['GET', 'POST'])
def purchase():
	userID=session['userID']
	if request.method == 'GET':
		q=request.args.get('asin')
		t=time.time()
		letters = 'abcdefghijklmnopqrstuvwxyz0123456789'
		akeys=[]
		with open('purchase.txt','r') as csvFile:
			reader = csv.DictReader(csvFile,dialect='myDialect')
			for row in reader:
				akeys.append(row['key'])
		while(True):
			ky=''.join(random.choice(letters) for i in range(7))
			if(ky not in akeys):
				break
		with open('purchase.txt','a') as f:
			ua=request.user_agent
			try:
				f.write(userID+'\t'+q+'\t'+str(t)+'\t'+ky+'\t'+ua.string[ua.string.index('(')+1:ua.string.index(')')]+'\t'+ua.platform+'\t'+ua.browser+'\t'+ua.version+'\n')
				session['purchase']+=(userID+q)+','
				print(session['purchase'])
			except:
				return '0'
		return '1'

@apps.route('/eshop/writeReview', methods=['GET', 'POST'])
def writeReview():
	global prodData
	asin=request.form['asin']
	ratings=request.form['ratings']
	summary=request.form['summary']
	reviewText=request.form['reviewText']
	ind=prodData['asin'].index(asin)
	t=int(time.time())
	d=detectFkRvw(float(ratings),reviewText,asin,prodData['subCat'][ind])
	with open("processedData.txt",'a') as f:
		f.write(session['userID']+'\t'+asin+'\t'+session['name']+'\t'+reviewText+'\t'+ratings+'\t'+summary+'\t'+str(t)+"\t"+prodData['title'][ind]+'\t\t'+prodData['subCat'][ind]+'\t'+d+'\n')
	readData()
	return "1"

@apps.route('/eshop/sendMail', methods=['POST'])
def sendMail():
	global prodData
	ky=""
	asin= request.form['asin']
	with open('purchase.txt','r') as csvFile:
		reader = csv.DictReader(csvFile,dialect='myDialect')
		for row in reader:
			if(row['userID']==session['userID'] and row['asin']==asin):
				ky=row['key']
	if(ky==''):
		return "0"
	link='http://192.168.43.226:5000/eshop/product?asin='+asin+'&key='+ky
	port = 587  # For starttls
	smtp_server = "smtp.gmail.com"
	sender_email = "feedbackuis@gmail.com"
	receiver_email = session['email']
	password = "!23qwerty"
	message = "Subject: Review link\nHi "+session['name']+",\nYour order has been delivered.\nProduct: "+prodData['title'][prodData['asin'].index(asin)]+"\nUse the link below to review the product\n"+link+"\n\n\nThis message is automatically generated, don't reply back."
	context = ssl.create_default_context()
	with smtplib.SMTP(smtp_server, port) as server:
		server.ehlo()  # Can be omitted
		server.starttls(context=context)
		server.ehlo()  # Can be omitted
		server.login(sender_email, password)
		server.sendmail(sender_email, receiver_email, message)
	return "1"

@apps.route('/settime', methods=['GET', 'POST'])
def settime():
	global dateandtime,unixtime
	if request.method == 'GET':
		return render_template('timeset.html')
	timeset= request.form['settime']
	dateandtime = datetime.strptime(timeset, '%Y-%m-%dT%H:%M')
	unixtime = time.mktime(dateandtime.timetuple())
	return redirect('/settime')

if __name__ == "__main__":
	readData()
	trainClassifier()
	apps.run(host='0.0.0.0',debug=True)
