import smtplib, ssl

def sendMail(to,name,pname,link):
	port = 587  # For starttls
	smtp_server = "smtp.gmail.com"
	sender_email = "feedbackuis@gmail.com"
	receiver_email = to
	password = "!23qwerty"
	message = "Subject: Review link\nHi "+name+",\nYour order has been delivered.\nProduct: "+pname+"\nUse the link below to review the product\n"+link+"\n\n\nThis message is automatically generated, don't reply back."

	context = ssl.create_default_context()
	with smtplib.SMTP(smtp_server, port) as server:
		server.ehlo()  # Can be omitted
		server.starttls(context=context)
		server.ehlo()  # Can be omitted
		server.login(sender_email, password)
		server.sendmail(sender_email, receiver_email, message)

sendMail("shashank.n.kumar@gmail.com","Shashank","Laptop","kissanime.ru")