import os
import keras
from sklearn.cluster import KMeans
import numpy as np
from keras.models import Sequential
from keras.layers import Dense,Input
from keras.models import Model
import subprocess
import shutil
import pickle
from keras.models import load_model
from sklearn.neighbors import KDTree
import pandas as pd
import matplotlib.pyplot as plt
from scipy.cluster.hierarchy import dendrogram,linkage


def fetchbindindSiteFile(directory):
    #Input directory
    #output list of binding site file names 
    pdbBindiSiteFiles=[]
    
    if os.path.exists(directory): 
        #fc=0
        print("In directory:",directory)
        for filename in os.listdir(directory):
            if filename.endswith("pmdesc"):
            	pdbBindiSiteFiles.append(filename)
                #fc=fc+1
                #if(fc>=600):
                    #break
    return pdbBindiSiteFiles

def fetchBindingSiteInformation(fileName,SILDINGWINDOWSIZE):
    #Input path of a binding site file
    #output an object of bindind site 
    distancePlotVector=[]
    with open(fileName,"r") as bindingSite:
        lines=bindingSite.readlines()
        totalNoofRows=len(lines)
        index=0
        sizeOfDistanceplot=int(lines[index])
        index=index+1
        for noOFRows in range(sizeOfDistanceplot):
            lenghtofDistanceplot=int(lines[index])
            index=index+1
            distancePlot=[]
            if lenghtofDistanceplot>0:
                for i in range(lenghtofDistanceplot):
                    #val=round(float(lines[index]),3)
                    val=float(lines[index])
                    #print(val)
                    distancePlot.append(val)
                    index=index+1
            else:
                distancePlot=[0]*SILDINGWINDOWSIZE
            distancePlotVector.append(distancePlot)    
            
    bindingSite.close()
    

    return distancePlotVector


def generatingOfSlidingWindowfromAllPairOfDistances(allPairShortestDistance,SILDINGWINDOWSIZE):
    #slide a fixed size window on distance plot and retun set of distance plot of size SIZEOFSLIDINGWINDOW
    #input: distance plot
    #output : set of sliding windows
    slidingWindows=[]
    lenghtOfallPairDistancesInSorted=len(allPairShortestDistance)
    noOfIteration= lenghtOfallPairDistancesInSorted-SILDINGWINDOWSIZE+1
    
    for index in range(0,noOfIteration):
        slidingWindows.append((allPairShortestDistance[index:SILDINGWINDOWSIZE+index]))
    return slidingWindows 


def setOfSlidingWindowsToHistogramVector(setofSlidingWindows,kMeanClassifier,NUMBEROFCLUSTERS):
    vectorRepresentationOfBindingSite=[]
    for slidingWindows in setofSlidingWindows:
        listOfCluster=kMeanClassifier.predict(slidingWindows)
        valueCountList=[0]*NUMBEROFCLUSTERS
        for val in listOfCluster:
            valueCountList[val]=valueCountList[val]+1
        vectorRepresentationOfBindingSite.extend(valueCountList)
    return vectorRepresentationOfBindingSite

def pdbFiletoSiteExtraction(filename,finalFolder):

	try:
		c=subprocess.Popen(['java','-jar','./Pocketmatch/test.jar',filename,finalFolder],stdout=subprocess.PIPE)
		c.wait()
		out = c.communicate()
		print("Extracted Successfully")
		return finalFolder
	except:
		return None
def saveToFile(downloadFolder,name, vectorencoding):
	with open(downloadFolder+"/"+name+".vec","w+") as f:
		for entry in vectorencoding:
			f.write("%s\n" % entry)
		f.close()
	print("Download File created")





def bindindSiteToVector(filename,finalFolder):
	SILDINGWINDOWSIZE=10
	NUMBEROFCLUSTERS=10



	siteDirectory=pdbFiletoSiteExtraction(filename,finalFolder)
	if siteDirectory is None:
		return None
	listOfbindingSitesasnames=fetchbindindSiteFile(siteDirectory)
	listOfBingingSiteDescriptors=[]
	setOfSlidingWindowsforlistOfBindingSites=[]
	bindingSiteNameList=[]


	if (len(listOfbindingSitesasnames)>0):
		for bindingSiteName in listOfbindingSitesasnames:
			filePath=siteDirectory+"/"+str(bindingSiteName)
			bindingSiteNameList.append(bindingSiteName)
			bindingSiteDescriptor=fetchBindingSiteInformation(filePath,SILDINGWINDOWSIZE)
			listOfBingingSiteDescriptors.append(bindingSiteDescriptor)
		for setOfDistancePlots in listOfBingingSiteDescriptors:
			setOfSlidingWindowsforbindingSite=[]
			for distancePlot in setOfDistancePlots:
				if len(distancePlot)<SILDINGWINDOWSIZE:
					distancePlot.extend([0]*(SILDINGWINDOWSIZE-len(distancePlot)))
					distancePlot.sort()
				slidingwindows=generatingOfSlidingWindowfromAllPairOfDistances(distancePlot,SILDINGWINDOWSIZE)
				setOfSlidingWindowsforbindingSite.append(slidingwindows)
			setOfSlidingWindowsforlistOfBindingSites.append(setOfSlidingWindowsforbindingSite)
		print("Number of Sites",len(setOfSlidingWindowsforlistOfBindingSites))
		kMeanClustering=pickle.load(open("./Model/Cluster.sav",'rb'))
		vectorEmbeddingOFListOfBindingSite=[]
		for setOfSlidingWindows in setOfSlidingWindowsforlistOfBindingSites:
			vectorEmbeddingOfbindingSite=setOfSlidingWindowsToHistogramVector(setOfSlidingWindows,kMeanClustering,NUMBEROFCLUSTERS)
			vectorEmbeddingOFListOfBindingSite.append(vectorEmbeddingOfbindingSite)
		
		totalnumberOfbindingsiters=len(vectorEmbeddingOFListOfBindingSite)
		vectorLenght=len(vectorEmbeddingOFListOfBindingSite[0])

		vectorEmbeddingOFListOfBindingSite=np.asarray(vectorEmbeddingOFListOfBindingSite)
		vectorEmbeddingOFListOfBindingSite=vectorEmbeddingOFListOfBindingSite.reshape(totalnumberOfbindingsiters,vectorLenght)
		print("Shape",vectorEmbeddingOFListOfBindingSite.shape)
		trainedModel=load_model("./Model/AutoEncoder.h5")
		encodedVectorListForBindingSites = trainedModel.predict(vectorEmbeddingOFListOfBindingSite)
		print("Shape",encodedVectorListForBindingSites.shape)
		keras.backend.clear_session()
		downloadFolder="./Downloadfolder"
		if os.path.exists(downloadFolder):
			shutil.rmtree(downloadFolder)
		os.mkdir(downloadFolder)
		for i in range(encodedVectorListForBindingSites.shape[0]):
			saveToFile(downloadFolder,bindingSiteNameList[i], encodedVectorListForBindingSites[i])
		if os.path.exists("./Download.zip"):
			os.remove("./Download.zip")
		shutil.make_archive("./Download", 'zip', downloadFolder)
		return "./Download.zip"
	else:
		if os.path.exists("./Download.zip"):
			os.remove("./Download.zip")
		return ""



def bindindSiteToVectorMultiFile(folder,finalFolder,downloadFolder):
	SILDINGWINDOWSIZE=10
	NUMBEROFCLUSTERS=10
	for file in os.listdir(folder):
		filename= folder+str("/")+file
		print(filename)
		siteDirectory=pdbFiletoSiteExtraction(filename,finalFolder)
	if siteDirectory is None:
		return None
	listOfbindingSitesasnames=fetchbindindSiteFile(siteDirectory)
	listOfBingingSiteDescriptors=[]
	setOfSlidingWindowsforlistOfBindingSites=[]
	bindingSiteNameList=[]

	
	if (len(listOfbindingSitesasnames)>0):
		for bindingSiteName in listOfbindingSitesasnames:
			filePath=siteDirectory+"/"+str(bindingSiteName)
			bindingSiteNameList.append(bindingSiteName)
			bindingSiteDescriptor=fetchBindingSiteInformation(filePath,SILDINGWINDOWSIZE)
			listOfBingingSiteDescriptors.append(bindingSiteDescriptor)
		for setOfDistancePlots in listOfBingingSiteDescriptors:
			setOfSlidingWindowsforbindingSite=[]
			for distancePlot in setOfDistancePlots:
				if len(distancePlot)<SILDINGWINDOWSIZE:
					distancePlot.extend([0]*(SILDINGWINDOWSIZE-len(distancePlot)))
					distancePlot.sort()
				slidingwindows=generatingOfSlidingWindowfromAllPairOfDistances(distancePlot,SILDINGWINDOWSIZE)
				setOfSlidingWindowsforbindingSite.append(slidingwindows)
			setOfSlidingWindowsforlistOfBindingSites.append(setOfSlidingWindowsforbindingSite)
		print("Number of Sites",len(setOfSlidingWindowsforlistOfBindingSites))
		kMeanClustering=pickle.load(open("./Model/Cluster.sav",'rb'))
		vectorEmbeddingOFListOfBindingSite=[]
		for setOfSlidingWindows in setOfSlidingWindowsforlistOfBindingSites:
			vectorEmbeddingOfbindingSite=setOfSlidingWindowsToHistogramVector(setOfSlidingWindows,kMeanClustering,NUMBEROFCLUSTERS)
			vectorEmbeddingOFListOfBindingSite.append(vectorEmbeddingOfbindingSite)
		
		totalnumberOfbindingsiters=len(vectorEmbeddingOFListOfBindingSite)
		vectorLenght=len(vectorEmbeddingOFListOfBindingSite[0])

		vectorEmbeddingOFListOfBindingSite=np.asarray(vectorEmbeddingOFListOfBindingSite)
		vectorEmbeddingOFListOfBindingSite=vectorEmbeddingOFListOfBindingSite.reshape(totalnumberOfbindingsiters,vectorLenght)
		print("Shape",vectorEmbeddingOFListOfBindingSite.shape)
		trainedModel=load_model("./Model/AutoEncoder.h5")
		encodedVectorListForBindingSites = trainedModel.predict(vectorEmbeddingOFListOfBindingSite)
		print("Shape",encodedVectorListForBindingSites.shape)
		keras.backend.clear_session()

		for i in range(encodedVectorListForBindingSites.shape[0]):
			saveToFile(downloadFolder,bindingSiteNameList[i], encodedVectorListForBindingSites[i])

		return "success"
	else:
		return "Error"


def readVectorFile(filename):
	try:
		with open(filename,"r") as f:
			vector=f.readlines()
		f.close()


		vectorEncoding=[]
		for element in vector:
			e=float(element[1:-1])
			vectorEncoding.append(e)
	except:
		return None
	print("Vector Generation Completed")
	if(len(vectorEncoding)!=200):
		return None
	return vectorEncoding

def findNearestNeighbourSites(vector,kn):
	df = pd.read_pickle('./Data/file.pkl')
	siteData=df['value'].tolist()
	tree=KDTree(siteData)
	distance , indices = tree.query(np.array(vector).reshape(1,-1,),k=int(kn))
	neighborSites=[]
	for i in indices[0]:
		neighborSites.append(df.iloc[i]['Name'])
	return neighborSites

def visualizationDendrogram(siteList,nameList):
	folderName="./static"
	if os.path.exists(folderName):
		shutil.rmtree(folderName)
	os.mkdir(folderName)
	linkageMatrix= linkage(siteList, 'ward')
	dendrogram(linkageMatrix,truncate_mode='lastp',show_contracted=False,leaf_rotation=90.,leaf_font_size=8.,labels=nameList)
	plt.title("Dendrogram")
	plt.savefig(folderName+"/Dedrogram.png")
	plt.close()
	if os.path.exists("./image.zip"):
		os.remove("./image.zip")
	shutil.make_archive("./image", 'zip', folderName)
	return True


def downloadSiteByNane(downloadFolder,name):

	df = pd.read_pickle('./Data/file.pkl')
	print(name)

	vector=list(df[df['Name']==name]['value'])
	vectorencoding = vector[0]
	#print(vector)
	saveToFile(downloadFolder,name, vectorencoding)


