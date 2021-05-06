set webbrowser = createobject("internetexplorer.application")
webbrowser.statusbar=false
webbrowser.menubar=false
webbrowser.toolbar=false
webbrowser.visible=true

webbrowser.navigate("http://192.168.43.214:5000/eshop/product?asin=B004J3Y9U6&key=bic1k6p")
wscript.sleep(6000)
webbrowser.document.all.item("oprvws").click
wscript.sleep(2000)
webbrowser.document.all.item("star-5").click
wscript.sleep(2000)
webbrowser.document.all.item("rvwTxt").value = "This is nice product. Worth for money"
wscript.sleep(2000)
webbrowser.document.all.item("rwsubmit").click

