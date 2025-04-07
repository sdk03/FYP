# --- Imports: Java and Autopsy APIs, plus JSON and HTTP for API communication ---

import jarray
import inspect
import os
from java.lang import Class
from java.lang import System
from java.sql  import DriverManager, SQLException
from java.util.logging import Level
from java.util import Arrays
from java.io import File
from org.sleuthkit.datamodel import SleuthkitCase
from org.sleuthkit.datamodel import AbstractFile
from org.sleuthkit.datamodel import ReadContentInputStream
from org.sleuthkit.datamodel import BlackboardArtifact
from org.sleuthkit.datamodel import BlackboardAttribute
from org.sleuthkit.autopsy.ingest import IngestModule
from org.sleuthkit.autopsy.ingest.IngestModule import IngestModuleException
from org.sleuthkit.autopsy.ingest import DataSourceIngestModule
from org.sleuthkit.autopsy.ingest import IngestModuleFactoryAdapter
from org.sleuthkit.autopsy.ingest import IngestMessage
from org.sleuthkit.autopsy.ingest import IngestServices
from org.sleuthkit.autopsy.ingest import ModuleDataEvent
from org.sleuthkit.autopsy.coreutils import Logger
from org.sleuthkit.autopsy.casemodule import Case
from org.sleuthkit.autopsy.datamodel import ContentUtils
from org.sleuthkit.autopsy.casemodule.services import Services
from org.sleuthkit.autopsy.casemodule.services import FileManager
from org.sleuthkit.autopsy.casemodule.services import Blackboard

from java.net import URL, HttpURLConnection
from java.io import OutputStreamWriter, BufferedReader, InputStreamReader
import json


# --- Factory class that Autopsy uses to recognize and instantiate the ingest module ---
class smsDbIngestModuleFactory(IngestModuleFactoryAdapter):

    moduleName = "LLM DFIR PLUGIN"

    def getModuleDisplayName(self):
        return self.moduleName

    def getModuleDescription(self):
        return "Module to process data and categorise it using LLM's"

    def getModuleVersionNumber(self):
        return "1.0"

    def isDataSourceIngestModuleFactory(self):
        return True

    def createDataSourceIngestModule(self, ingestOptions):
        return smsDbIngestModule()
    


# --- Main Ingest Module class: Defines setup, processing, and AI interaction logic ---
class smsDbIngestModule(DataSourceIngestModule):

    _logger = Logger.getLogger(smsDbIngestModuleFactory.moduleName)

    def log(self, level, msg):
        self._logger.logp(level, self.__class__.__name__, inspect.stack()[1][3], msg)

    def __init__(self):
        self.context = None


    # --- Sends SMS text to local Flask API (LLM) and parses the response ---
    def process_with_llama_api(self,sms_text):
       try:
            url = URL("http://localhost:8000/reply")
            conn = url.openConnection()
            conn.setRequestMethod("POST")
            conn.setRequestProperty("Content-Type", "application/json")
            conn.setDoOutput(True)

            data = json.dumps({"message": sms_text})

            writer = OutputStreamWriter(conn.getOutputStream())
            writer.write(data)
            writer.flush()
            writer.close()

            response_code = conn.getResponseCode()
            if response_code == HttpURLConnection.HTTP_OK:  # 200
                reader = BufferedReader(InputStreamReader(conn.getInputStream()))
                response = ""
                line = reader.readLine()
                while line is not None:
                    response += line
                    line = reader.readLine()
                reader.close()

                self.log(Level.INFO, "RESPONSE")
                self.log(Level.INFO, response)
                result = json.loads(response)
                return result.get("reply")
            else:
                print("Error calling LLAMA API:", response_code)
                return "ERROR"
       except Exception as e:
            print("Error calling LLAMA API:", str(e))
            return "ERROR"


    # --- Called before processing begins, stores the context ---
    def startUp(self, context):
        self.context = context

    # --- Creates custom artifact and attribute types for SMS analysis results ---
    def create_custom_artifact_types(self):
        """
        Create custom artifact and attribute types if they don't exist.
        """
        try:
            blackboard = Case.getCurrentCase().getSleuthkitCase().getBlackboard()

            sms_artifact_type = blackboard.getOrAddArtifactType(
                "TSK_CUSTOM_SMS", "LLM DFIR PLUGIN")

            blackboard.getOrAddAttributeType(
                "TSK_SMS_TEXT", BlackboardAttribute.TSK_BLACKBOARD_ATTRIBUTE_VALUE_TYPE.STRING, "SMS Text")
            blackboard.getOrAddAttributeType(
                "TSK_TAGS", BlackboardAttribute.TSK_BLACKBOARD_ATTRIBUTE_VALUE_TYPE.STRING, "Tags")
            blackboard.getOrAddAttributeType(
                "TSK_PERSON", BlackboardAttribute.TSK_BLACKBOARD_ATTRIBUTE_VALUE_TYPE.STRING, "Person")
            blackboard.getOrAddAttributeType(
                "TSK_ORGANIZATION", BlackboardAttribute.TSK_BLACKBOARD_ATTRIBUTE_VALUE_TYPE.STRING, "Organization")
            blackboard.getOrAddAttributeType(
                "TSK_GPE", BlackboardAttribute.TSK_BLACKBOARD_ATTRIBUTE_VALUE_TYPE.STRING, "Geo-Political Entity")
            blackboard.getOrAddAttributeType(
                "TSK_NORP", BlackboardAttribute.TSK_BLACKBOARD_ATTRIBUTE_VALUE_TYPE.STRING, "Nationalities/Religious/Political Groups")
            blackboard.getOrAddAttributeType(
                "TSK_DATE", BlackboardAttribute.TSK_BLACKBOARD_ATTRIBUTE_VALUE_TYPE.STRING, "Date")
            blackboard.getOrAddAttributeType(
                "TSK_TIME", BlackboardAttribute.TSK_BLACKBOARD_ATTRIBUTE_VALUE_TYPE.STRING, "Time")
            blackboard.getOrAddAttributeType(
                "TSK_MONEY", BlackboardAttribute.TSK_BLACKBOARD_ATTRIBUTE_VALUE_TYPE.STRING, "Money")
            blackboard.getOrAddAttributeType(
                "TSK_PERCENT", BlackboardAttribute.TSK_BLACKBOARD_ATTRIBUTE_VALUE_TYPE.STRING, "Percent")
            blackboard.getOrAddAttributeType(
                "TSK_FAC", BlackboardAttribute.TSK_BLACKBOARD_ATTRIBUTE_VALUE_TYPE.STRING, "Facility")
            blackboard.getOrAddAttributeType(
                "TSK_PRODUCT", BlackboardAttribute.TSK_BLACKBOARD_ATTRIBUTE_VALUE_TYPE.STRING, "Product")
            blackboard.getOrAddAttributeType(
                "TSK_WORK_OF_ART", BlackboardAttribute.TSK_BLACKBOARD_ATTRIBUTE_VALUE_TYPE.STRING, "Work of Art")
            blackboard.getOrAddAttributeType(
                "TSK_LANGUAGE", BlackboardAttribute.TSK_BLACKBOARD_ATTRIBUTE_VALUE_TYPE.STRING, "Language")
            blackboard.getOrAddAttributeType(
                "TSK_EVENT", BlackboardAttribute.TSK_BLACKBOARD_ATTRIBUTE_VALUE_TYPE.STRING, "Event")
            blackboard.getOrAddAttributeType(
                "TSK_LAW", BlackboardAttribute.TSK_BLACKBOARD_ATTRIBUTE_VALUE_TYPE.STRING, "Law")
            blackboard.getOrAddAttributeType(
                "TSK_ORDINAL", BlackboardAttribute.TSK_BLACKBOARD_ATTRIBUTE_VALUE_TYPE.STRING, "Ordinal")
            blackboard.getOrAddAttributeType(
                "TSK_CARDINAL", BlackboardAttribute.TSK_BLACKBOARD_ATTRIBUTE_VALUE_TYPE.STRING, "Cardinal")

            return sms_artifact_type
        except Exception as e:
            Logger.getLogger(smsDbIngestModuleFactory.moduleName).log(Level.SEVERE, "Error creating custom artifact types: " + str(e))

# --- Main processing loop: finds mmssms.db, parses SMS messages, sends them to LLM, creates artifacts ---
    def process(self, dataSource, progressBar):

        sms_artifact_type = self.create_custom_artifact_types()

        if sms_artifact_type is None:
            self.log(Level.SEVERE, "Custom artifact type TSK_CUSTOM_SMS not found. Exiting process.")
            return IngestModule.ProcessResult.ERROR

        sk_case = Case.getCurrentCase().getSleuthkitCase()
        blackboard = sk_case.getBlackboard()

        fileManager = Case.getCurrentCase().getServices().getFileManager()
        files = fileManager.findFiles(dataSource, "mmssms.db")

        numFiles = len(files)
        progressBar.switchToDeterminate(numFiles)
        fileCount = 0

        for file in files:
            if self.context.isJobCancelled():
                return IngestModule.ProcessResult.OK

            self.log(Level.INFO, "Processing file: " + file.getName())
            fileCount += 1

            lclDbPath = os.path.join(Case.getCurrentCase().getTempDirectory(), str(file.getId()) + ".db")
            ContentUtils.writeToFile(file, File(lclDbPath))

            try:
                Class.forName("org.sqlite.JDBC").newInstance()
                dbConn = DriverManager.getConnection("jdbc:sqlite:%s" % lclDbPath)
            except SQLException as e:
                self.log(Level.INFO, "Could not open database file: " + file.getName())
                continue

            try:
                stmt = dbConn.createStatement()
                resultSet = stmt.executeQuery("SELECT body FROM sms")
            except SQLException as e:
                self.log(Level.INFO, "Error querying database: " + e.getMessage())
                continue

            while resultSet.next():
                try:
                    body = resultSet.getString("body")
                except SQLException:
                    continue

                # Process SMS text with AI or handle it
                ai_data = {
                    "PERSON": "E", "ORG": "E", "GPE": "E", "NORP": "E", "DATE": "E", 
                    "TIME": "E", "MONEY": "E", "PERCENT": "E", "FAC": "E", 
                    "PRODUCT": "E", "WORK_OF_ART": "E", "LANGUAGE": "E", 
                    "EVENT": "E", "LAW": "E", "ORDINAL": "E", "CARDINAL": "E"
                }

                try:
                    ai_response = self.process_with_llama_api(body)
                    import json
                    ai_data = json.loads(ai_response)
                except (json.JSONDecodeError, Exception) as e:
                    self.log(Level.INFO, "Error processing AI response for body: {}. Error: {}".format(body, str(e)))
                    continue

                # Create artifact with explicit attributes, leaving other values blank if there's an error
                try:
                    artifact = file.newArtifact(sms_artifact_type.getTypeID())
                    artifact.addAttribute(BlackboardAttribute(
                        blackboard.getAttributeType("TSK_SMS_TEXT"), smsDbIngestModuleFactory.moduleName, body))
                    artifact.addAttribute(BlackboardAttribute(
                        blackboard.getAttributeType("TSK_TAGS"), smsDbIngestModuleFactory.moduleName, ai_data.get("TAGS", "E")))
                    artifact.addAttribute(BlackboardAttribute(
                        blackboard.getAttributeType("TSK_PERSON"), smsDbIngestModuleFactory.moduleName, ai_data.get("PERSON", "E")))
                    artifact.addAttribute(BlackboardAttribute(
                        blackboard.getAttributeType("TSK_ORGANIZATION"), smsDbIngestModuleFactory.moduleName, ai_data.get("ORG", "E")))
                    artifact.addAttribute(BlackboardAttribute(
                        blackboard.getAttributeType("TSK_GPE"), smsDbIngestModuleFactory.moduleName, ai_data.get("GPE", "E")))
                    artifact.addAttribute(BlackboardAttribute(
                        blackboard.getAttributeType("TSK_NORP"), smsDbIngestModuleFactory.moduleName, ai_data.get("NORP", "E")))
                    artifact.addAttribute(BlackboardAttribute(
                        blackboard.getAttributeType("TSK_DATE"), smsDbIngestModuleFactory.moduleName, ai_data.get("DATE", "E")))
                    artifact.addAttribute(BlackboardAttribute(
                        blackboard.getAttributeType("TSK_TIME"), smsDbIngestModuleFactory.moduleName, ai_data.get("TIME", "E")))
                    artifact.addAttribute(BlackboardAttribute(
                        blackboard.getAttributeType("TSK_MONEY"), smsDbIngestModuleFactory.moduleName, ai_data.get("MONEY", "E")))
                    artifact.addAttribute(BlackboardAttribute(
                        blackboard.getAttributeType("TSK_PERCENT"), smsDbIngestModuleFactory.moduleName, ai_data.get("PERCENT", "E")))
                    artifact.addAttribute(BlackboardAttribute(
                        blackboard.getAttributeType("TSK_FAC"), smsDbIngestModuleFactory.moduleName, ai_data.get("FAC", "E")))
                    artifact.addAttribute(BlackboardAttribute(
                        blackboard.getAttributeType("TSK_PRODUCT"), smsDbIngestModuleFactory.moduleName, ai_data.get("PRODUCT", "E")))
                    artifact.addAttribute(BlackboardAttribute(
                        blackboard.getAttributeType("TSK_WORK_OF_ART"), smsDbIngestModuleFactory.moduleName, ai_data.get("WORK_OF_ART", "E")))
                    artifact.addAttribute(BlackboardAttribute(
                        blackboard.getAttributeType("TSK_LANGUAGE"), smsDbIngestModuleFactory.moduleName, ai_data.get("LANGUAGE", "E")))
                    artifact.addAttribute(BlackboardAttribute(
                        blackboard.getAttributeType("TSK_EVENT"), smsDbIngestModuleFactory.moduleName, ai_data.get("EVENT", "E")))
                    artifact.addAttribute(BlackboardAttribute(
                        blackboard.getAttributeType("TSK_LAW"), smsDbIngestModuleFactory.moduleName, ai_data.get("LAW", "E")))
                    artifact.addAttribute(BlackboardAttribute(
                        blackboard.getAttributeType("TSK_ORDINAL"), smsDbIngestModuleFactory.moduleName, ai_data.get("ORDINAL", "E")))
                    artifact.addAttribute(BlackboardAttribute(
                        blackboard.getAttributeType("TSK_CARDINAL"), smsDbIngestModuleFactory.moduleName, ai_data.get("CARDINAL", "E")))

                    blackboard.postArtifact(artifact, smsDbIngestModuleFactory.moduleName)
                except Exception as e:
                   self.log(Level.INFO, "Error posting ARTIFACT for body: {}. Error: {}".format(body, str(e)))
                   continue


            stmt.close()
            dbConn.close()
            os.remove(lclDbPath)

        message = IngestMessage.createMessage(IngestMessage.MessageType.DATA,
                                            "LLM DFIR PLUGIN", "Processed %d messages" % fileCount)
        IngestServices.getInstance().postMessage(message)

        return IngestModule.ProcessResult.OK
