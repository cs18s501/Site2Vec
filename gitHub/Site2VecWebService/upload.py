import os
from flask import Flask, flash, request, redirect, url_for ,render_template
from werkzeug.utils import secure_filename
from Site2Vec import site2Vec
import shutil
from flask import send_file
import pandas as pd 
import urllib
from PIL import Image 

app = Flask(__name__)  
 
app.config['SECRET_KEY']='1234567890ABCDSF'
app.config['UPLOAD_FOLDER']='./File'
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
ALLOWED_EXTENSIONS = {'pdb'}
DOWNLOADFILE=""

@app.after_request
def add_header(response):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    response.headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
    response.headers['Cache-Control'] = 'public, max-age=0'
    return response
df = pd.read_pickle('./Data/file.pkl')
siteData=df['Name']
#siteData=siteData.to_dict()

@app.route('/home',methods = ['GET','POST'])  
def upload():  

    return render_template("home.html",siteData=siteData)  
 
@app.route("/multiplefile",methods = ['GET','POST'])
def multiplrFileUpload():
	return render_template("multiplefile.html")


@app.route('/multiplesucess',methods = ['GET','POST'])
def multiFilesuccess():

	if request.method == 'POST':
		flag=False
		files = request.files.getlist("file")
		if os.path.exists(app.config['UPLOAD_FOLDER']):
			shutil.rmtree(app.config['UPLOAD_FOLDER'])
		os.mkdir(app.config['UPLOAD_FOLDER'])
		finalFolder="./multiFileFolder"
		if os.path.exists(finalFolder):
			shutil.rmtree(finalFolder)
		os.mkdir(finalFolder)


		downloadFolder="./DownloadfolderMulti"
		if os.path.exists(downloadFolder):
			shutil.rmtree(downloadFolder)
		os.mkdir(downloadFolder)

		if os.path.exists("./DownloadMulti.zip"):
			os.remove("./DownloadMulti.zip")

		for f in files:
			if(not f.filename.endswith("pdb")):
				flash( str(f.filename)+' Unsupported File')
			else:
				flag=True
				filename = secure_filename(f.filename)
				f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
		status=""
		if flag == True:
			status=site2Vec.bindindSiteToVectorMultiFile(app.config['UPLOAD_FOLDER'],finalFolder,downloadFolder)
			if status == "Error":
				flash('No Site Extracted')
				return redirect(url_for('multiplrFileUpload'))
		else:
			return redirect(url_for('multiplrFileUpload'))

			
		shutil.make_archive("./DownloadMulti", 'zip', downloadFolder)



	return render_template("multiSucces.html")




@app.route('/success', methods = ['GET','POST'])  
def success():  
    if request.method == 'POST':  
        f = request.files['file']  
        print("File name: ",f.filename)
        if not f.filename.endswith("pdb"):
        	
        	flash('Unsupported File')
        	return redirect(url_for('upload'))
         
        if f and '.' in f.filename:

        	filename = secure_filename(f.filename)
        	if os.path.exists(app.config['UPLOAD_FOLDER']):
        		shutil.rmtree(app.config['UPLOAD_FOLDER'])
        	os.mkdir(app.config['UPLOAD_FOLDER'])




        	f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        	finalFolder="./Tempfolder"
        	downloadFolder="./Downloadfolder"
        	if os.path.exists(finalFolder):
        		shutil.rmtree(finalFolder)
        	os.mkdir(finalFolder)
        	status=site2Vec.bindindSiteToVector(os.path.join(app.config['UPLOAD_FOLDER'], filename),finalFolder)
        	if status != "" and status !=None:
        		return render_template("success.html", name = os.listdir(downloadFolder)) 
        	elif(status == None):
        		flash('Not Able to Extract Bindind Site')
        		return redirect(url_for('upload'))

        	else:
        		flash('No binding Site Extracted')
        		return redirect(url_for('upload'))
    else:
    	
    	return redirect(url_for('upload'))


@app.route("/download", methods = ['GET','POST'])
def download():
	
	downloadFolder="./Downloadfolder"
	downloadFileList=request.form.getlist('download')
	if len(downloadFileList)>0:
		print("Download SuccesFully")
		finalFolder="./FinalDownload"
		downloadFolder="./Downloadfolder"
		if os.path.exists("./Download.zip"):
			os.remove("./Download.zip")
		if os.path.exists(finalFolder):
			shutil.rmtree(finalFolder)
		os.mkdir(finalFolder)

		for i in downloadFileList:

			shutil.copy(downloadFolder+str("/")+i,finalFolder)
		shutil.make_archive("./Download", 'zip', finalFolder)

		return send_file("./Download.zip",attachment_filename='Download.zip')
	else:
		flash("Select atleast one file")
		return render_template("success.html", name = os.listdir(downloadFolder))


@app.route("/downloadmulti", methods = ['GET','POST'])


def downloadMulti():
	return send_file("./DownloadMulti.zip",attachment_filename='Download.zip')


@app.route('/find',methods=['GET','POST'])
def findSimilarSite():
	if request.method == 'POST':  
		f = request.files['Findfile']
		k = request.form['KneaestNeighbour']
		if f and '.' in f.filename:
			filename = secure_filename(f.filename)
			f.save(filename)

			vectorDescriptor=site2Vec.readVectorFile(filename)
			if os.path.exists(filename):
				os.remove(filename)
			if vectorDescriptor == None:
				flash(" Data Error")
				neighbourSites=[]
				return render_template("find.html",neighbourSites=neighbourSites)

			neighbourSites=site2Vec.findNearestNeighbourSites(vectorDescriptor,k)
			if len(neighbourSites)==0:
				flash("No neighbour")
				return render_template("find.html",neighbourSites=neighbourSites)
	else:
		if os.path.exists(filename):
			os.remove(filename)
		neighbourSites=[]
		flash("File not supported")
		return render_template("find.html",neighbourSites=neighbourSites)
	return render_template("find.html",neighbourSites=neighbourSites)	


@app.route('/display',methods=['GET','POST'])
def displayDendrogram():
	if request.method == 'POST':
		files = request.files.getlist("displayfile")
		visualFolder="./Visual"
		visulizatioSites=[]
		visulizatioSitesName=[]
		flag=False
		if os.path.exists(visualFolder):
			shutil.rmtree(visualFolder)
		os.mkdir(visualFolder)
		for f in files:


			filename = secure_filename(f.filename)
			f.save(os.path.join(visualFolder, filename))

			vector=site2Vec.readVectorFile(os.path.join(visualFolder, filename))
			if vector == None:
				flash( str(f.filename)+' Unsupported File')
			else:
				visulizatioSites.append(vector)
				visulizatioSitesName.append(filename[0:6])
		if len(visulizatioSites)>1:
			print(len(visulizatioSites))
			flag=site2Vec.visualizationDendrogram(visulizatioSites,visulizatioSitesName)
			
		elif len(visulizatioSites) ==1:
			flash("Only One Site is Uploaded")
		else:
			flash("No Site is Uploaded")


		return render_template("display.html",flag=flag)

@app.route("/downloadImage", methods=['GET','POST'])
def downloadImage():
	return send_file("./image.zip",attachment_filename='image.zip')

@app.route("/Filedownload",methods=['GET','POST'])
def fileDownload():
	downloadFileList=request.form.getlist('filedownload')
	print(len(downloadFileList))
	downloadFolder="./selectedFileDownload"
	if os.path.exists(downloadFolder):
		shutil.rmtree(downloadFolder)
	os.mkdir(downloadFolder)
	if os.path.exists("./DownloadSite.zip"):
		os.remove("./DownloadSite.zip")
	if len(downloadFileList) ==0:
		flash("No Site is Selected")
		return redirect(url_for('upload'))
	else:
		for site in downloadFileList:
			site2Vec.downloadSiteByNane(downloadFolder,site)


		shutil.make_archive("./DownloadSite", 'zip', downloadFolder)

		return send_file("./DownloadSite.zip",attachment_filename='DownloadSite.zip')

@app.route("/search",methods=['GET','POST'])
def searchFile():

	return render_template("search.html",siteData=siteData.tolist()) 

@app.route("/pdbdownload",methods=['GET','POST'])
def downloadAndProcesspdb():
	if request.method == 'POST':
		pdbFile=request.form['pdbid']
		if os.path.exists(app.config['UPLOAD_FOLDER']):
			shutil.rmtree(app.config['UPLOAD_FOLDER'])
		os.mkdir(app.config['UPLOAD_FOLDER'])
		try:

			urllib.request.urlretrieve('http://files.rcsb.org/download/'+pdbFile.upper()+".pdb", app.config['UPLOAD_FOLDER']+"/"+pdbFile.lower()+'.pdb')
			finalFolder="./Tempfolder"
			downloadFolder="./Downloadfolder"
			if os.path.exists(finalFolder):
				shutil.rmtree(finalFolder)
			os.mkdir(finalFolder)
			status=site2Vec.bindindSiteToVector(app.config['UPLOAD_FOLDER']+"/"+pdbFile.lower()+'.pdb',finalFolder)
			if status != "" and status !=None:
				return render_template("success.html", name = os.listdir(downloadFolder)) 
			elif(status == None):
				flash('Not able to Extract Bindind Site')
				return redirect(url_for('upload'))

			else:
				flash('No binding Site Extracted')
				return redirect(url_for('upload'))
    

		except:
			flash('Wrong pdb Code')
			return redirect(url_for('upload'))	
	else:

		return redirect(url_for('upload'))


if __name__ == '__main__':  
    app.run(debug = True,host='0.0.0.0',port=5616)  