from appionlib import torqueHost
from appionlib import apRefineJobFrealign
from appionlib import apRefineJobEman
from appionlib import apRefineJobXmipp
from appionlib import apRefineJobXmippML3D
from appionlib import apGenericJob
from appionlib import jobtest
import sys
import re
import time
import os

try:
    import MySQLdb
    import dbconfig
except ImportError, e:
    sys.stderr.write("Warning: %s, status updates will be disabled\n" % (e))
    statusUpdatesEnabled = False
else:
    statusUpdatesEnabled = True
    
class Agent (object):
    def __init__(self, configFile=None):
        if configFile:
            self.configFile = configFile
        
        self.currentJob = None
        self.processingHost = None
        self.statusCkInterval = 30
    
    def Main(self,command):
        
        self.processingHost = self.createProcessingHost()
        
        jobType = self.getJobType(command)
        
        #Not sure if we want pedanticaly issue warning messages 
        #if not jobType:
        #    sys.stderr.write("Warning: Could not determine job type\n")
                 
        try:   
            self.currentJob = self.createJobInst(jobType, command)
        except Exception, e:
            sys.stderr.write("Error: Could not create job  %s : %s\n" %(command, e))
            sys.exit(1)
            
        if not self.currentJob:
            sys.stderr.write("Error: Could not create job for: %s\n" % (command))
            sys.exit(1)
              
        hostJobId = self.processingHost.launchJob(self.currentJob)
        #if the job launched successfully print out the ID returned.
        if not hostJobId:
            sys.stderr.write("Error: Could not execute job %s\n" % (self.currentJob.getName()))
            sys.exit(1)
            
        sys.stdout.write(str(hostJobId) + '\n') 
        sys.stdout.flush()
       
        if statusUpdatesEnabled:
            self.updateJobStatus(self.currentJob, hostJobId)
       
        return 0
 
    ##
    #    
    def createProcessingHost(self):
        if not self.configFile:
            raise ValueError ("Could not create processing host object, configuration file not defined") 
        
        configDict = self.parseConfigFile(self.configFile)
        try:
            processingHostType = configDict['ProcessingHostType'].upper()
            if 'TORQUE' == processingHostType or 'PBS' == processingHostType:
                processingHost = torqueHost.TorqueHost(configDict)
            else:
                sys.stderr.write("Unknown processing host type, using default\n")
                processingHost = torqueHost.TorqueHost(configDict)
            
        except (KeyError, AttributeError):
            sys.stderr.write("Couldn't determine processing host type, using default\n")
            processingHost = torqueHost.TorqueHost(configDict)
 
        return processingHost
       
    ##getJobType (command)
    #Searches a list of command options , 'command',  and attempts to extract the 
    #job type from it.  Returns the job type if successful otherwise returns None.
    def getJobType(self, command):
        jobtype = None
    
        #Search for the command option that specified the job type
        for option in command:
            if option.startswith(r'--jobtype='):
                #We only need the part after the '='
                jobtype = option.split('=')[1]
                #Don't process anymore of the list then needed
                break
            
        return jobtype

    ##       
    #
    def createJobInst(self, jobType, command):
        jobInstance = None
            
        if "emanrecon" == jobType:
            jobInstance = apRefineJobEman.EmanRefineJob(command)
        elif "frealignrecon" == jobType:
            jobInstance = apRefineJobFrealign.FrealignRefineJob(command)
        elif "xmipprecon" == jobType:
            jobInstance = apRefineJobXmipp.XmippSingleModelRefineJob(command)
        elif "xmippml3d" == jobType:
            jobInstance = apRefineJobXmippML3D.XmippML3DRefineJob(command)
        elif "jobtest" == jobType:
            jobInstance = jobtest.jobtestClass()
        else:
            jobInstance = apGenericJob.genericJob(command)
        
        return jobInstance

    ##
    #
    def parseConfigFile (self, configFile):
        confDict ={}
        try:
            cFile= file(configFile, 'r')
        except IOError, e:
            raise IOError ("Couldn't read configuration file " + configFile + ": " + str(e))
        
        #for line in cFile.readlines():          
        line = cFile.readline()
        while line:
            #get rid of an leading and trailing white space
            #line = line.strip()
            #Only process lines of the correct format, quietly ignore all others"
            matchedLine=re.match(r'\s*([A-Za-z]+)\s*=\s*(\S.*)\s*',line)
            if  matchedLine:
                #split the two parts of the line
                (key, value) = matchedLine.groups()
                #value strings can be spread across multiple lines if \n is escaped (\)
                #process these lines.              
                while '\\' == value[-1]:      
                    value = value[:-1]
                    line= cFile.readline()
                    value += line.rstrip('\n')
                #split comma separated values into a list
                if ',' in value:   
                    value = re.split(r'\s*,\s*', value)
                #put the key/value pair in the configuration dictionary    
                confDict[key]=value
            line = cFile.readline()
                
        return confDict
    
    ##
    #
    def updateJobStatus (self, jobObject, hostJobId ):
        checkStatusInterval =  self.statusCkInterval
        currentStatus = 'Q'
                        
        projDB = self.__initDB(jobObject, hostJobId)                
        jobid = jobObject.getJobId()
        
        if projDB:
            #Update before forking, indicating to insert new row if necessary.
            self.__updateStatusInDB(jobid, currentStatus)
            
            try:
                pid = os.fork()        
                if pid == 0:
                    os.setsid()
                    while currentStatus != "D" and currentStatus != "U":
                        time.sleep(checkStatusInterval)
                        newStatus = self.processingHost.checkJobStatus(hostJobId)
                        if newStatus != currentStatus:
                            #Assume status changed was missed if we go from R or Q to U (unknown) and mark
                            #job as done.
                            if newStatus == "U" and (currentStatus == "R" or currentStatus == "Q"):
                                currentStatus = "D"
                            else:        
                                currentStatus = newStatus
                            
                            self.__updateStatusInDB(jobid, currentStatus)
                   
            except OSError, e:
                sys.stderr.write("Warning: Unable to monitor status: %s\n" % (e))
        else:
            sys.stderr.write("Warning: Unable to monitor job status.\n")                       

        return
    
    ##
    #
    def __updateStatusInDB (self, jobid, status):
        retVal = True   #initialize return value to True
        dbConfig = dbconfig.getConfig('appiondata')
        dbConnection = MySQLdb.connect(**dbConfig)
        cursor = dbConnection.cursor()
           
           
        updateCommand = "UPDATE ApAppionJobData SET status= '%s' WHERE `DEF_id` = '%s'" % (status, jobid)
        result = cursor.execute(updateCommand)
        
        if not result:
            retVal = False
              
        return retVal

    ##
    #
    def __initDB (self, jobObject, job):
        retValue = None
            
        try:
            #Determine the appion project database name using the project id.
            projDBConfig = dbconfig.getConfig('projectdata')
            dbConnection = MySQLdb.connect(**projDBConfig)
            cursor =  dbConnection.cursor()
                                          
            query = "SELECT appiondb from processingdb WHERE `REF|projects|project`=%d" % (jobObject.getProjectId())
            queryResult=cursor.execute(query)
            if queryResult:
                projDB = cursor.fetchone()[0]
                projDBConfig = dbconfig.setConfig('appiondata', db=projDB)
                retValue = projDB
                
            cursor.close()
            dbConnection.close()
        except MySQLdb.DatabaseError, e:
            sys.stderr.write("Warning: Failure determining project database: %s \n" % (e))
        
        #if jobId is not set, assume there is no entry in ApAppionJobData for this run
        if not jobObject.getJobId():
            path = jobObject.getRundir()
            jobname = jobObject.getName()
            jobtype = jobObject.getJobType()
            remoterundir = jobObject.getOutputDir()
            expid = jobObject.getExpId()
            cluster = os.uname()[1]
            user = os.getlogin()
                          
            dbconf = dbconfig.getConfig('appiondata')
            dbConnection = MySQLdb.connect(**dbconf)          
            cursor = dbConnection.cursor()
           
            insertQuery = "INSERT INTO ApAppionJobData (`REF|ApPathData|path`, name, jobtype, `REF|ApPathData|clusterpath`, `REF|leginondata|SessionData|session`, cluster, clusterjobid, status, user) \
                     VALUES ('%s','%s','%s','%s','%s','%s','%s','%s','%s')" %(path, jobname, jobtype, remoterundir, expid, cluster, job, 'Q', user)    

            if cursor.execute (insertQuery):
                jobObject.setJobId(cursor.lastrowid)   

            cursor.close()
            dbConnection.close()
            
        return retValue
            